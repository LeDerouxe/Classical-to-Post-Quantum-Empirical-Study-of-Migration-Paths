#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <openssl/x509v3.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define CIPHER "TLS_AES_128_GCM_SHA256"

static void print_errors(const char *where) {
    fprintf(stderr, "ERROR\t%s\t", where);
    ERR_print_errors_fp(stderr);
}

static void usage(const char *name) {
    fprintf(stderr, "usage: %s server PORT CERT KEY GROUP SIGALG | %s client PORT CA HOST GROUP SIGALG\n", name, name);
    exit(2);
}

static uint64_t now_ticks(void) {
    LARGE_INTEGER value;
    return QueryPerformanceCounter(&value) ? (uint64_t)value.QuadPart : 0;
}

static uint64_t frequency(void) {
    LARGE_INTEGER value;
    return QueryPerformanceFrequency(&value) ? (uint64_t)value.QuadPart : 0;
}

static SSL_CTX *new_context(int server, const char *group, const char *sigalg) {
    SSL_CTX *ctx = SSL_CTX_new(server ? TLS_server_method() : TLS_client_method());
    if (!ctx) return NULL;
    if (SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_max_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_ciphersuites(ctx, CIPHER) != 1 ||
        SSL_CTX_set1_groups_list(ctx, group) != 1 ||
        SSL_CTX_set1_sigalgs_list(ctx, sigalg) != 1 ||
        SSL_CTX_set_num_tickets(ctx, 0) != 1) {
        SSL_CTX_free(ctx);
        return NULL;
    }
    SSL_CTX_set_options(ctx, SSL_OP_NO_TICKET);
    SSL_CTX_set_session_cache_mode(ctx, SSL_SESS_CACHE_OFF);
    return ctx;
}

static SOCKET make_listener(unsigned short port) {
    SOCKET fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    struct sockaddr_in address;
    int one = 1;
    if (fd == INVALID_SOCKET) return INVALID_SOCKET;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, (const char *)&one, sizeof(one));
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = htons(port);
    if (bind(fd, (const struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR ||
        listen(fd, 1) == SOCKET_ERROR) {
        closesocket(fd);
        return INVALID_SOCKET;
    }
    return fd;
}

static void fields(SSL *ssl, int server, const char **version, const char **cipher,
                   const char **group, const char **signature) {
    *version = SSL_get_version(ssl);
    *cipher = SSL_get_cipher_name(ssl);
    *group = SSL_get0_group_name(ssl);
    if (server) SSL_get0_signature_name(ssl, signature);
    else SSL_get0_peer_signature_name(ssl, signature);
    if (!*group) *group = "(unknown)";
    if (!*signature) *signature = "(unknown)";
}

static int server_mode(int argc, char **argv) {
    SOCKET listener = INVALID_SOCKET, fd = INVALID_SOCKET;
    SSL_CTX *ctx = NULL;
    SSL *ssl = NULL;
    const char *version = "", *cipher = "", *group = "", *signature = "";
    int rc = 1;
    if (argc != 7) usage(argv[0]);
    ctx = new_context(1, argv[5], argv[6]);
    if (!ctx || SSL_CTX_use_certificate_chain_file(ctx, argv[3]) != 1 ||
        SSL_CTX_use_PrivateKey_file(ctx, argv[4], SSL_FILETYPE_PEM) != 1 ||
        SSL_CTX_check_private_key(ctx) != 1) { print_errors("configure_server"); goto done; }
    listener = make_listener((unsigned short)strtoul(argv[2], NULL, 10));
    if (listener == INVALID_SOCKET) { fprintf(stderr, "ERROR\tlisten\t%d\n", WSAGetLastError()); goto done; }
    printf("READY\tport=%s\n", argv[2]); fflush(stdout);
    fd = accept(listener, NULL, NULL);
    if (fd == INVALID_SOCKET) { fprintf(stderr, "ERROR\taccept\t%d\n", WSAGetLastError()); goto done; }
    ssl = SSL_new(ctx);
    if (!ssl || SSL_set_fd(ssl, (int)fd) != 1 || SSL_accept(ssl) != 1) { print_errors("SSL_accept"); goto done; }
    fields(ssl, 1, &version, &cipher, &group, &signature);
    printf("SERVER_RESULT\ttls_version=%s\tcipher=%s\tgroup=%s\tsignature=%s\n", version, cipher, group, signature);
    fflush(stdout);
    rc = 0;
done:
    if (ssl) SSL_free(ssl);
    if (fd != INVALID_SOCKET) closesocket(fd);
    if (listener != INVALID_SOCKET) closesocket(listener);
    if (ctx) SSL_CTX_free(ctx);
    return rc;
}

static int client_mode(int argc, char **argv) {
    SOCKET fd = INVALID_SOCKET;
    SSL_CTX *ctx = NULL;
    SSL *ssl = NULL;
    struct sockaddr_in address;
    const char *version = "", *cipher = "", *group = "", *signature = "";
    X509 *peer = NULL;
    EVP_PKEY *key = NULL;
    const char *key_type = "(missing)";
    uint64_t start = 0, stop = 0, freq = frequency();
    int rc = 1, host_ok = 0;
    long verify = X509_V_ERR_UNSPECIFIED;
    if (argc != 7) usage(argv[0]);
    ctx = new_context(0, argv[5], argv[6]);
    if (!ctx || SSL_CTX_load_verify_locations(ctx, argv[3], NULL) != 1) { print_errors("configure_client"); goto done; }
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (fd == INVALID_SOCKET) { fprintf(stderr, "ERROR\tsocket\t%d\n", WSAGetLastError()); goto done; }
    memset(&address, 0, sizeof(address));
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    address.sin_port = htons((unsigned short)strtoul(argv[2], NULL, 10));
    if (connect(fd, (const struct sockaddr *)&address, sizeof(address)) == SOCKET_ERROR) { fprintf(stderr, "ERROR\tconnect\t%d\n", WSAGetLastError()); goto done; }
    ssl = SSL_new(ctx);
    if (!ssl || SSL_set_fd(ssl, (int)fd) != 1 || SSL_set1_host(ssl, argv[4]) != 1 ||
        SSL_set_tlsext_host_name(ssl, argv[4]) != 1) { print_errors("SSL_new_or_hostname"); goto done; }
    start = now_ticks();
    int accepted = SSL_connect(ssl);
    stop = now_ticks();
    if (accepted != 1) { print_errors("SSL_connect"); goto done; }
    verify = SSL_get_verify_result(ssl);
    peer = SSL_get1_peer_certificate(ssl);
    key = peer ? X509_get_pubkey(peer) : NULL;
    if (key) key_type = EVP_PKEY_get0_type_name(key);
    host_ok = peer ? X509_check_host(peer, argv[4], 0, 0, NULL) : 0;
    fields(ssl, 0, &version, &cipher, &group, &signature);
    rc = (verify == X509_V_OK && host_ok == 1 && peer && key) ? 0 : 1;
done:
    printf("CLIENT_RESULT\tsuccess=%d\ttls_version=%s\tcipher=%s\tgroup=%s\tpeer_public_key_type=%s\tcertificate_verify_signature_scheme=%s\tchain_result=%s\thostname_result=%s\tqpc_start=%llu\tqpc_stop=%llu\tqpc_frequency=%llu\n",
           rc == 0, version, cipher, group, key_type, signature,
           verify == X509_V_OK ? "PASS" : "FAIL", host_ok == 1 ? "PASS" : "FAIL",
           (unsigned long long)start, (unsigned long long)stop, (unsigned long long)freq);
    fflush(stdout);
    EVP_PKEY_free(key); X509_free(peer);
    if (ssl) SSL_free(ssl);
    if (fd != INVALID_SOCKET) closesocket(fd);
    if (ctx) SSL_CTX_free(ctx);
    return rc;
}

int main(int argc, char **argv) {
    WSADATA data;
    int result = WSAStartup(MAKEWORD(2, 2), &data);
    if (result != 0) { fprintf(stderr, "WSAStartup failed: %d\n", result); return 1; }
    if (argc < 2) usage(argv[0]);
    result = strcmp(argv[1], "server") == 0 ? server_mode(argc, argv) :
             strcmp(argv[1], "client") == 0 ? client_mode(argc, argv) : 2;
    WSACleanup();
    return result;
}
