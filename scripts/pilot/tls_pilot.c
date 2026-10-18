#define _GNU_SOURCE
#include <arpa/inet.h>
#include <errno.h>
#include <netdb.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <linux/tcp.h>
#include <netinet/in.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/socket.h>
#include <time.h>
#include <unistd.h>

static uint64_t now_ns(void) {
    struct timespec t;
    if (clock_gettime(CLOCK_MONOTONIC_RAW, &t) != 0) return 0;
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_nsec;
}

static uint64_t timeval_ns(struct timeval t) {
    return (uint64_t)t.tv_sec * 1000000000ULL + (uint64_t)t.tv_usec * 1000ULL;
}

static void usage(const char *name) {
    fprintf(stderr, "usage:\n  %s server PORT CERT KEY GROUP SIGALG CIPHER\n  %s client PORT CA HOST GROUP SIGALG CIPHER\n", name, name);
    exit(2);
}

static SSL_CTX *new_context(int server, const char *group, const char *sigalg,
                            const char *cipher) {
    SSL_CTX *ctx = SSL_CTX_new(server ? TLS_server_method() : TLS_client_method());
    if (!ctx) return NULL;
    SSL_CTX_set_min_proto_version(ctx, TLS1_3_VERSION);
    SSL_CTX_set_max_proto_version(ctx, TLS1_3_VERSION);
    SSL_CTX_set_options(ctx, SSL_OP_NO_TICKET);
    SSL_CTX_set_num_tickets(ctx, 0);
    SSL_CTX_set_session_cache_mode(ctx, SSL_SESS_CACHE_OFF);
    if (!SSL_CTX_set_ciphersuites(ctx, cipher)
        || !SSL_CTX_set1_groups_list(ctx, group)
        || !SSL_CTX_set1_sigalgs_list(ctx, sigalg)) {
        SSL_CTX_free(ctx);
        return NULL;
    }
    return ctx;
}

static int tcp_counters(int fd, struct tcp_info *info) {
    socklen_t n = sizeof(*info);
    memset(info, 0, sizeof(*info));
    return getsockopt(fd, IPPROTO_TCP, TCP_INFO, info, &n);
}

static void usage_delta(struct rusage before, struct rusage after,
                        uint64_t *user, uint64_t *system) {
    *user = timeval_ns(after.ru_utime) - timeval_ns(before.ru_utime);
    *system = timeval_ns(after.ru_stime) - timeval_ns(before.ru_stime);
}

static int make_listener(const char *port) {
    struct sockaddr_in a;
    memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    a.sin_port = htons((uint16_t)strtoul(port, NULL, 10));
    int fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd < 0) return -1;
    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    if (bind(fd, (struct sockaddr *)&a, sizeof(a)) || listen(fd, 1)) {
        close(fd);
        return -1;
    }
    return fd;
}

static void print_ssl_fields(SSL *ssl, const char **version, const char **cipher,
                             const char **group, const char **sigalg, int server) {
    *version = SSL_get_version(ssl);
    *cipher = SSL_get_cipher_name(ssl);
    int id = SSL_get_negotiated_group(ssl);
    const char *g = id ? SSL_group_to_name(ssl, id) : NULL;
    *group = g ? g : "";
    const char *sig = NULL;
    if (server) SSL_get0_signature_name(ssl, &sig);
    else SSL_get0_peer_signature_name(ssl, &sig);
    *sigalg = sig ? sig : "";
}

static int server_mode(int argc, char **argv) {
    if (argc != 8) usage(argv[0]);
    const char *port = argv[2], *cert = argv[3], *key = argv[4];
    const char *group = argv[5], *sigalg = argv[6], *cipher = argv[7];
    SSL_CTX *ctx = new_context(1, group, sigalg, cipher);
    if (!ctx || SSL_CTX_use_certificate_chain_file(ctx, cert) != 1
        || SSL_CTX_use_PrivateKey_file(ctx, key, SSL_FILETYPE_PEM) != 1
        || SSL_CTX_check_private_key(ctx) != 1) {
        ERR_print_errors_fp(stderr);
        if (ctx) SSL_CTX_free(ctx);
        return 10;
    }
    int listener = make_listener(port);
    if (listener < 0) { perror("server listen"); SSL_CTX_free(ctx); return 11; }
    puts("READY");
    fflush(stdout);
    int fd;
    do { fd = accept4(listener, NULL, NULL, SOCK_CLOEXEC); } while (fd < 0 && errno == EINTR);
    if (fd < 0) { perror("accept"); close(listener); SSL_CTX_free(ctx); return 12; }

    SSL *ssl = SSL_new(ctx);
    if (!ssl || SSL_set_fd(ssl, fd) != 1) {
        ERR_print_errors_fp(stderr);
        if (ssl) SSL_free(ssl);
        close(fd); close(listener); SSL_CTX_free(ctx); return 13;
    }
    struct rusage before, after, peak;
    getrusage(RUSAGE_THREAD, &before);
    int rc = SSL_accept(ssl);
    getrusage(RUSAGE_THREAD, &after);
    getrusage(RUSAGE_SELF, &peak);
    uint64_t user_ns, system_ns;
    usage_delta(before, after, &user_ns, &system_ns);
    struct tcp_info ti;
    int ti_ok = tcp_counters(fd, &ti) == 0;
    const char *version = "", *cipher_name = "", *observed_group = "", *observed_sig = "";
    if (rc == 1) print_ssl_fields(ssl, &version, &cipher_name, &observed_group, &observed_sig, 1);
    fprintf(stdout, "RESULT\t%d\t%s\t%s\t%s\t%s\t%llu\t%llu\t%ld\t%llu\t%llu\t%u\t%u\t%s\n",
            rc == 1, version, cipher_name, observed_group, observed_sig,
            (unsigned long long)user_ns, (unsigned long long)system_ns, peak.ru_maxrss,
            (unsigned long long)(ti_ok ? ti.tcpi_bytes_sent : 0),
            (unsigned long long)(ti_ok ? ti.tcpi_bytes_received : 0),
            ti_ok ? ti.tcpi_segs_out : 0, ti_ok ? ti.tcpi_segs_in : 0,
            !ti_ok ? "TCP_INFO unavailable" : (rc == 1 ? "" : "SSL_accept failed"));
    fflush(stdout);
    if (rc != 1) ERR_print_errors_fp(stderr);
    SSL_free(ssl); close(fd); close(listener); SSL_CTX_free(ctx);
    return rc == 1 && ti_ok ? 0 : 14;
}

static int client_mode(int argc, char **argv) {
    if (argc != 8) usage(argv[0]);
    const char *port = argv[2], *ca = argv[3], *host = argv[4];
    const char *group = argv[5], *sigalg = argv[6], *cipher = argv[7];
    SSL_CTX *ctx = new_context(0, group, sigalg, cipher);
    if (!ctx || SSL_CTX_load_verify_locations(ctx, ca, NULL) != 1) {
        ERR_print_errors_fp(stderr);
        if (ctx) SSL_CTX_free(ctx);
        return 20;
    }
    SSL_CTX_set_verify(ctx, SSL_VERIFY_PEER, NULL);
    SSL *ssl = SSL_new(ctx);
    if (!ssl || SSL_set1_host(ssl, host) != 1 || SSL_set_tlsext_host_name(ssl, host) != 1) {
        ERR_print_errors_fp(stderr);
        if (ssl) SSL_free(ssl);
        SSL_CTX_free(ctx); return 21;
    }
    struct sockaddr_in a;
    memset(&a, 0, sizeof(a));
    a.sin_family = AF_INET;
    a.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
    a.sin_port = htons((uint16_t)strtoul(port, NULL, 10));
    int fd = socket(AF_INET, SOCK_STREAM | SOCK_CLOEXEC, 0);
    if (fd < 0) { perror("client socket"); SSL_free(ssl); SSL_CTX_free(ctx); return 22; }
    SSL_set_fd(ssl, fd);
    struct rusage cpu_before, cpu_after, peak;
    uint64_t connect_start = now_ns();
    getrusage(RUSAGE_THREAD, &cpu_before);
    int cr = connect(fd, (struct sockaddr *)&a, sizeof(a));
    uint64_t connect_ns = now_ns() - connect_start;
    uint64_t handshake_ns = 0;
    int hr = 0;
    if (cr == 0) {
        uint64_t handshake_start = now_ns();
        hr = SSL_connect(ssl);
        handshake_ns = now_ns() - handshake_start;
    }
    getrusage(RUSAGE_THREAD, &cpu_after);
    getrusage(RUSAGE_SELF, &peak);
    uint64_t user_ns, system_ns;
    usage_delta(cpu_before, cpu_after, &user_ns, &system_ns);
    struct tcp_info ti;
    int ti_ok = tcp_counters(fd, &ti) == 0;
    const char *version = "", *cipher_name = "", *observed_group = "", *observed_sig = "";
    if (hr == 1) print_ssl_fields(ssl, &version, &cipher_name, &observed_group, &observed_sig, 0);
    const char *error = !ti_ok ? "TCP_INFO unavailable" :
                        (cr != 0 ? "connect failed" : (hr != 1 ? "SSL_connect failed" : ""));
    fprintf(stdout, "RESULT\t%d\t%s\t%s\t%s\t%s\t%llu\t%llu\t%llu\t%llu\t%ld\t%llu\t%llu\t%u\t%u\t%s\n",
            hr == 1 && ti_ok, version, cipher_name, observed_group, observed_sig,
            (unsigned long long)connect_ns, (unsigned long long)handshake_ns,
            (unsigned long long)user_ns, (unsigned long long)system_ns, peak.ru_maxrss,
            (unsigned long long)(ti_ok ? ti.tcpi_bytes_sent : 0),
            (unsigned long long)(ti_ok ? ti.tcpi_bytes_received : 0),
            ti_ok ? ti.tcpi_segs_out : 0, ti_ok ? ti.tcpi_segs_in : 0, error);
    fflush(stdout);
    if (hr != 1) ERR_print_errors_fp(stderr);
    SSL_free(ssl); close(fd); SSL_CTX_free(ctx);
    return hr == 1 && ti_ok ? 0 : 23;
}

int main(int argc, char **argv) {
    signal(SIGPIPE, SIG_IGN);
    if (argc < 2) usage(argv[0]);
    if (!strcmp(argv[1], "server")) return server_mode(argc, argv);
    if (!strcmp(argv[1], "client")) return client_mode(argc, argv);
    usage(argv[0]);
    return 2;
}
