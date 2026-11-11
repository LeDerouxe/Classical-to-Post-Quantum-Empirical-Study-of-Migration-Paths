#define _GNU_SOURCE

#include <arpa/inet.h>
#include <errno.h>
#include <linux/tcp.h>
#include <netinet/in.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static uint64_t now_ns(void) {
    struct timespec value;
    if (clock_gettime(CLOCK_MONOTONIC_RAW, &value) != 0) return 0;
    return (uint64_t)value.tv_sec * 1000000000ULL + (uint64_t)value.tv_nsec;
}

static void usage(const char *name) {
    fprintf(stderr, "usage:\n  %s server BIND_IP PORT CERT KEY GROUP SIGALG CIPHER\n"
                    "  %s client SERVER_IP PORT CA HOST GROUP SIGALG CIPHER\n", name, name);
    exit(2);
}

static SSL_CTX *new_context(int server, const char *group, const char *sigalg,
                            const char *cipher) {
    SSL_CTX *ctx = SSL_CTX_new(server ? TLS_server_method() : TLS_client_method());
    if (!ctx) return NULL;
    if (SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_max_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_ciphersuites(ctx, cipher) != 1 ||
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

static int make_address(struct sockaddr_in *address, const char *ip, const char *port) {
    memset(address, 0, sizeof(*address));
    address->sin_family = AF_INET;
    address->sin_port = htons((uint16_t)strtoul(port, NULL, 10));
    return inet_pton(AF_INET, ip, &address->sin_addr) == 1;
}

static void negotiated_fields(SSL *ssl, int server, const char **version,
                              const char **cipher, const char **group,
                              const char **signature) {
    int group_id = SSL_get_negotiated_group(ssl);
    const char *signature_name = NULL;
    *version = SSL_get_version(ssl);
    *cipher = SSL_get_cipher_name(ssl);
    *group = group_id ? SSL_group_to_name(ssl, group_id) : "";
    if (server) SSL_get0_signature_name(ssl, &signature_name);
    else SSL_get0_peer_signature_name(ssl, &signature_name);
    *signature = signature_name ? signature_name : "";
}

static int server_mode(int argc, char **argv) {
    SSL_CTX *ctx = NULL;
    SSL *ssl = NULL;
    struct sockaddr_in address;
    int listener = -1, fd = -1, rc = 1;
    const char *version = "", *cipher = "", *group = "", *signature = "";

    if (argc != 9) usage(argv[0]);
    ctx = new_context(1, argv[6], argv[7], argv[8]);
    if (!ctx || SSL_CTX_use_certificate_chain_file(ctx, argv[4]) != 1 ||
        SSL_CTX_use_PrivateKey_file(ctx, argv[5], SSL_FILETYPE_PEM) != 1 ||
        SSL_CTX_check_private_key(ctx) != 1 ||
        !make_address(&address, argv[2], argv[3])) goto done;
    listener = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (listener < 0) goto done;
    { int one = 1; (void)setsockopt(listener, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one)); }
    if (bind(listener, (struct sockaddr *)&address, sizeof(address)) != 0 || listen(listener, 1) != 0) goto done;
    puts("READY");
    fflush(stdout);
    do { fd = accept4(listener, NULL, NULL, SOCK_CLOEXEC); } while (fd < 0 && errno == EINTR);
    if (fd < 0) goto done;
    ssl = SSL_new(ctx);
    if (!ssl || SSL_set_fd(ssl, fd) != 1 || SSL_accept(ssl) != 1) goto done;
    negotiated_fields(ssl, 1, &version, &cipher, &group, &signature);
    rc = 0;
done:
    fprintf(stdout, "RESULT\t%d\t%s\t%s\t%s\t%s\n", rc == 0, version, cipher, group, signature);
    fflush(stdout);
    if (rc && ERR_peek_error()) ERR_print_errors_fp(stderr);
    SSL_free(ssl);
    if (fd >= 0) close(fd);
    if (listener >= 0) close(listener);
    SSL_CTX_free(ctx);
    return rc;
}

static int client_mode(int argc, char **argv) {
    SSL_CTX *ctx = NULL;
    SSL *ssl = NULL;
    struct sockaddr_in address;
    struct tcp_info info;
    socklen_t info_length = sizeof(info);
    int fd = -1, rc = 1, connect_result;
    uint64_t connect_ns = 0, handshake_ns = 0, started = 0;
    const char *version = "", *cipher = "", *group = "", *signature = "";

    if (argc != 9) usage(argv[0]);
    ctx = new_context(0, argv[6], argv[7], argv[8]);
    if (!ctx || SSL_CTX_load_verify_locations(ctx, argv[4], NULL) != 1 ||
        !make_address(&address, argv[2], argv[3])) goto done;
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    ssl = SSL_new(ctx);
    if (!ssl || SSL_set1_host(ssl, argv[5]) != 1 ||
        SSL_set_tlsext_host_name(ssl, argv[5]) != 1) goto done;
    fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd < 0 || SSL_set_fd(ssl, fd) != 1) goto done;
    started = now_ns();
    connect_result = connect(fd, (struct sockaddr *)&address, sizeof(address));
    connect_ns = now_ns() - started;
    if (connect_result == 0) {
        started = now_ns();
        if (SSL_connect(ssl) == 1) {
            handshake_ns = now_ns() - started;
            negotiated_fields(ssl, 0, &version, &cipher, &group, &signature);
            if (SSL_get_verify_result(ssl) == X509_V_OK) rc = 0;
        } else {
            handshake_ns = now_ns() - started;
        }
    }
done:
    memset(&info, 0, sizeof(info));
    int info_ok = fd >= 0 && getsockopt(fd, IPPROTO_TCP, TCP_INFO, &info, &info_length) == 0;
    fprintf(stdout, "RESULT\t%d\t%s\t%s\t%s\t%s\t%llu\t%llu\t%llu\t%u\n",
            rc == 0 && info_ok, version, cipher, group, signature,
            (unsigned long long)connect_ns, (unsigned long long)handshake_ns,
            (unsigned long long)(info_ok ? info.tcpi_bytes_sent + info.tcpi_bytes_received : 0),
            info_ok ? info.tcpi_segs_out + info.tcpi_segs_in : 0);
    fflush(stdout);
    if (rc && ERR_peek_error()) ERR_print_errors_fp(stderr);
    SSL_free(ssl);
    if (fd >= 0) close(fd);
    SSL_CTX_free(ctx);
    return rc == 0 && info_ok ? 0 : 1;
}

int main(int argc, char **argv) {
    signal(SIGPIPE, SIG_IGN);
    if (argc < 2) usage(argv[0]);
    if (strcmp(argv[1], "server") == 0) return server_mode(argc, argv);
    if (strcmp(argv[1], "client") == 0) return client_mode(argc, argv);
    usage(argv[0]);
}
