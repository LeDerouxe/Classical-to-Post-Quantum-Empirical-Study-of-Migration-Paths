#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <netinet/in.h>
#include <openssl/err.h>
#include <openssl/evp.h>
#include <openssl/ssl.h>
#include <openssl/tls1.h>
#include <openssl/x509v3.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define CIPHER "TLS_AES_128_GCM_SHA256"

typedef struct {
    X509 *ecdsa_cert;
    EVP_PKEY *ecdsa_key;
    X509 *mldsa_cert;
    EVP_PKEY *mldsa_key;
} credentials;

static int label_index = -1;

static void print_errors(const char *where) {
    fprintf(stderr, "ERROR\t%s\t", where);
    ERR_print_errors_fp(stderr);
}

static int valid_profile(const char *id) {
    return strcmp(id, "L") == 0 || strcmp(id, "H") == 0 ||
           strcmp(id, "D") == 0 || strcmp(id, "Q") == 0;
}

/* SSL_get_sigalgs documents rhash as the high byte and rsig as the low byte
 * of the offered TLS SignatureScheme. */
static int client_offers_signature_scheme(SSL *ssl,
                                          unsigned char expected_rhash,
                                          unsigned char expected_rsig) {
    int count = SSL_get_sigalgs(ssl, -1, NULL, NULL, NULL, NULL, NULL);
    int sign = NID_undef, hash = NID_undef, signhash = NID_undef;
    unsigned char rsig = 0, rhash = 0;
    for (int i = 0; i < count; i++) {
        if (SSL_get_sigalgs(ssl, i, &sign, &hash, &signhash, &rsig, &rhash) > 0 &&
            rhash == expected_rhash && rsig == expected_rsig)
            return 1;
    }
    return 0;
}

static int select_dual_certificate(SSL *ssl, void *arg) {
    credentials *creds = (credentials *)arg;
    int has_ecdsa = client_offers_signature_scheme(ssl, 0x04, 0x03);
    int has_mldsa = client_offers_signature_scheme(ssl, 0x09, 0x05);
    const char *label = NULL;
    X509 *cert = NULL;
    EVP_PKEY *key = NULL;
    if (has_mldsa) {
        label = "ML-DSA-65";
        cert = creds->mldsa_cert;
        key = creds->mldsa_key;
    } else if (has_ecdsa) {
        label = "ECDSA-P-256";
        cert = creds->ecdsa_cert;
        key = creds->ecdsa_key;
    } else {
        fprintf(stderr, "ERROR\tno_supported_client_signature_capability\n");
        return 0;
    }
    if (SSL_use_cert_and_key(ssl, cert, key, NULL, 1) != 1) {
        print_errors("SSL_use_cert_and_key");
        return 0;
    }
    if (SSL_set_ex_data(ssl, label_index, (void *)label) != 1) {
        print_errors("SSL_set_ex_data");
        return 0;
    }
    return 1;
}

static X509 *load_cert(const char *path) {
    BIO *bio = BIO_new_file(path, "r");
    if (!bio) return NULL;
    X509 *cert = PEM_read_bio_X509(bio, NULL, NULL, NULL);
    BIO_free(bio);
    return cert;
}

static EVP_PKEY *load_key(const char *path) {
    BIO *bio = BIO_new_file(path, "r");
    if (!bio) return NULL;
    EVP_PKEY *key = PEM_read_bio_PrivateKey(bio, NULL, NULL, NULL);
    BIO_free(bio);
    return key;
}

static int run_server(const char *port_text, const char *profile_id,
                      const char *groups, const char *sigalgs,
                      const char *ecert_path, const char *ekey_path,
                      const char *mcert_path, const char *mkey_path) {
    int rc = 1, fd = -1, client_fd = -1, port = atoi(port_text);
    SSL_CTX *ctx = NULL;
    SSL *ssl = NULL;
    credentials creds = {0};
    const char *fixed_label = NULL;
    struct sockaddr_in addr;
    if (!valid_profile(profile_id)) { fprintf(stderr, "ERROR\tunknown_server_profile\n"); return 2; }
    if (label_index < 0) label_index = SSL_get_ex_new_index(0, NULL, NULL, NULL, NULL);
    creds.ecdsa_cert = load_cert(ecert_path);
    creds.ecdsa_key = load_key(ekey_path);
    creds.mldsa_cert = load_cert(mcert_path);
    creds.mldsa_key = load_key(mkey_path);
    if (!creds.ecdsa_cert || !creds.ecdsa_key || !creds.mldsa_cert || !creds.mldsa_key) {
        print_errors("load_compatibility_credentials"); goto done;
    }
    ctx = SSL_CTX_new(TLS_server_method());
    if (!ctx || SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_max_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_ciphersuites(ctx, CIPHER) != 1 ||
        SSL_CTX_set1_groups_list(ctx, groups) != 1 ||
        SSL_CTX_set1_sigalgs_list(ctx, sigalgs) != 1) {
        print_errors("configure_server_profile"); goto done;
    }
    if (SSL_CTX_set_num_tickets(ctx, 0) != 1) {
        print_errors("disable_tls13_session_tickets"); goto done;
    }
    SSL_CTX_set_options(ctx, SSL_OP_NO_TICKET);
    SSL_CTX_set_session_cache_mode(ctx, SSL_SESS_CACHE_OFF);
    if (strcmp(profile_id, "D") == 0) {
        SSL_CTX_set_cert_cb(ctx, select_dual_certificate, &creds);
    } else {
        X509 *cert = strcmp(profile_id, "Q") == 0 ? creds.mldsa_cert : creds.ecdsa_cert;
        EVP_PKEY *key = strcmp(profile_id, "Q") == 0 ? creds.mldsa_key : creds.ecdsa_key;
        fixed_label = strcmp(profile_id, "Q") == 0 ? "ML-DSA-65" : "ECDSA-P-256";
        if (SSL_CTX_use_cert_and_key(ctx, cert, key, NULL, 1) != 1) {
            print_errors("configure_server_credential_capability"); goto done;
        }
    }
    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) { perror("socket"); goto done; }
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons((unsigned short)port);
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0 || listen(fd, 1) != 0) {
        perror("bind/listen"); goto done;
    }
    printf("READY\tprofile=%s\tport=%d\n", profile_id, port); fflush(stdout);
    client_fd = accept(fd, NULL, NULL);
    if (client_fd < 0) { perror("accept"); goto done; }
    ssl = SSL_new(ctx);
    if (!ssl || SSL_set_fd(ssl, client_fd) != 1) { print_errors("SSL_new/SSL_set_fd"); goto done; }
    if (fixed_label && SSL_set_ex_data(ssl, label_index, (void *)fixed_label) != 1) {
        print_errors("set_fixed_credential_label"); goto done;
    }
    if (SSL_accept(ssl) != 1) {
        print_errors("SSL_accept");
        const char *label = (const char *)SSL_get_ex_data(ssl, label_index);
        printf("SERVER_FAILURE\tprofile=%s\tselected_server_credential=%s\n",
               profile_id, label ? label : "(none)"); fflush(stdout);
        goto done;
    }
    const char *label = (const char *)SSL_get_ex_data(ssl, label_index);
    printf("SERVER_RESULT\tprofile=%s\tselected_server_credential=%s\ttls_version=%s\tcipher=%s\tgroup=%s\n",
           profile_id, label ? label : "(unset)", SSL_get_version(ssl),
           SSL_get_cipher_name(ssl), SSL_get0_group_name(ssl) ? SSL_get0_group_name(ssl) : "(unknown)");
    fflush(stdout);
    rc = 0;
done:
    if (ssl) SSL_free(ssl);
    if (client_fd >= 0) close(client_fd);
    if (fd >= 0) close(fd);
    if (ctx) SSL_CTX_free(ctx);
    X509_free(creds.ecdsa_cert); EVP_PKEY_free(creds.ecdsa_key);
    X509_free(creds.mldsa_cert); EVP_PKEY_free(creds.mldsa_key);
    return rc;
}

static int run_client(const char *port_text, const char *profile_id,
                      const char *groups, const char *sigalgs,
                      const char *ca_path, const char *hostname) {
    int rc = 1, fd = -1, port = atoi(port_text);
    SSL_CTX *ctx = NULL;
    SSL *ssl = NULL;
    X509 *peer = NULL;
    EVP_PKEY *pub = NULL;
    struct sockaddr_in addr;
    if (!valid_profile(profile_id)) { fprintf(stderr, "ERROR\tunknown_client_profile\n"); return 2; }
    ctx = SSL_CTX_new(TLS_client_method());
    if (!ctx || SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_max_proto_version(ctx, TLS1_3_VERSION) != 1 ||
        SSL_CTX_set_ciphersuites(ctx, CIPHER) != 1 ||
        SSL_CTX_set1_groups_list(ctx, groups) != 1 ||
        SSL_CTX_set1_sigalgs_list(ctx, sigalgs) != 1 ||
        SSL_CTX_load_verify_locations(ctx, ca_path, NULL) != 1) {
        print_errors("configure_client_profile"); goto done;
    }
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    SSL_CTX_set_options(ctx, SSL_OP_NO_TICKET);
    SSL_CTX_set_session_cache_mode(ctx, SSL_SESS_CACHE_OFF);
    fd = socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) { perror("socket"); goto done; }
    memset(&addr, 0, sizeof(addr));
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    addr.sin_port = htons((unsigned short)port);
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) != 0) { perror("connect"); goto done; }
    ssl = SSL_new(ctx);
    if (!ssl || SSL_set_fd(ssl, fd) != 1 ||
        SSL_set_tlsext_host_name(ssl, hostname) != 1 || SSL_set1_host(ssl, hostname) != 1) {
        print_errors("SSL_new/hostname"); goto done;
    }
    int handshake_ok = SSL_connect(ssl) == 1;
    if (!handshake_ok) print_errors("SSL_connect");
    long verify = SSL_get_verify_result(ssl);
    peer = SSL_get1_peer_certificate(ssl);
    pub = peer ? X509_get_pubkey(peer) : NULL;
    const char *pk_type = pub ? EVP_PKEY_get0_type_name(pub) : "(none)";
    const char *signature = NULL;
    SSL_get0_peer_signature_name(ssl, &signature);
    const char *group = SSL_get0_group_name(ssl);
    int host_ok = peer ? X509_check_host(peer, hostname, 0, 0, NULL) : 0;
    const char *chain_result = verify == X509_V_OK && peer ? "PASS" : (peer ? "FAIL" : "NOT_EVALUATED");
    const char *hostname_result = host_ok == 1 ? "PASS" : (peer ? "FAIL" : "NOT_EVALUATED");
    printf("CLIENT_RESULT\tprofile=%s\thandshake=%s\ttls_version=%s\tcipher=%s\tgroup=%s\tpeer_public_key_type=%s\tcertificate_verify_signature_scheme=%s\tchain_result=%s\thostname_result=%s\tverify_error=%s\n",
           profile_id, handshake_ok ? "PASS" : "FAIL", SSL_get_version(ssl),
           SSL_get_cipher_name(ssl) ? SSL_get_cipher_name(ssl) : "(none)",
           group ? group : "(none)", pk_type, signature ? signature : "(none)",
           chain_result, hostname_result, X509_verify_cert_error_string(verify));
    fflush(stdout);
    rc = (handshake_ok && verify == X509_V_OK && host_ok == 1 && peer && pub && signature) ? 0 : 1;
done:
    EVP_PKEY_free(pub); X509_free(peer);
    if (ssl) SSL_free(ssl);
    if (fd >= 0) close(fd);
    if (ctx) SSL_CTX_free(ctx);
    return rc;
}

int main(int argc, char **argv) {
    if (signal(SIGPIPE, SIG_IGN) == SIG_ERR) {
        perror("signal(SIGPIPE, SIG_IGN)");
        return 1;
    }
    if (argc == 10 && strcmp(argv[1], "server") == 0)
        return run_server(argv[2], argv[3], argv[4], argv[5], argv[6], argv[7], argv[8], argv[9]);
    if (argc == 8 && strcmp(argv[1], "client") == 0)
        return run_client(argv[2], argv[3], argv[4], argv[5], argv[6], argv[7]);
    fprintf(stderr, "usage: %s server PORT PROFILE GROUPS SIGALGS EC_CERT EC_KEY MLDSA_CERT MLDSA_KEY | client PORT PROFILE GROUPS SIGALGS CA HOSTNAME\n", argv[0]);
    return 2;
}
