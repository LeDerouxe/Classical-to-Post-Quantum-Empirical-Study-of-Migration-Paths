# Controlled Network-Sensitivity Analysis

## Scope and inclusion rule

- Campaign: `campaign-20261114T202013Z-44a824c91fb9`.
- This is a separate native Ubuntu namespace/veth/netem study. It neither replaces nor pools with the completed loopback or Windows campaigns.
- The 1,000 protocol-defined warm-ups remain in raw data but are excluded from analysis. All 3,000 measured observations are retained; no statistical outlier is removed.
- Each RTT condition is analyzed separately. The 0-ms condition is a namespace/veth topology control, not a duplicate of the primary loopback campaign.

## Integrity gate

- Raw rows: 4000; warm-ups: 1000; measured rows: 3000.
- Validation errors: none.
- All CIs below use 20,000 percentile bootstrap resamples that first resample the five batches of the stated RTT and then rows inside selected batches. With five batches, the intervals describe uncertainty and are not null-hypothesis tests.

## TLS handshake duration by added RTT

All values are milliseconds. `Contrast vs S0` is the condition-specific median(case) minus median(S0).

| condition | case | n | median_ms | median_ci_low_ms | median_ci_high_ms | iqr_ms | mean_ms | sd_ms | p95_ms_descriptive | min_ms | max_ms | contrast_vs_s0_ms | contrast_ci_low_ms | contrast_ci_high_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rtt-000ms | S0 | 150 | 0.830 | 0.819 | 0.855 | 0.099 | 0.873 | 0.274 | 0.959 | 0.714 | 3.725 | 0.000 | 0.000 | 0.000 |
| rtt-000ms | S2 | 150 | 0.996 | 0.979 | 1.011 | 0.081 | 1.024 | 0.140 | 1.191 | 0.873 | 2.016 | 0.166 | 0.140 | 0.181 |
| rtt-000ms | S3 | 150 | 1.446 | 1.366 | 1.588 | 0.554 | 1.612 | 0.551 | 2.471 | 1.070 | 4.560 | 0.615 | 0.530 | 0.758 |
| rtt-000ms | S4 | 150 | 1.391 | 1.314 | 1.476 | 0.605 | 1.548 | 0.544 | 2.580 | 0.940 | 3.833 | 0.560 | 0.478 | 0.644 |
| rtt-001ms | S0 | 150 | 1.897 | 1.877 | 1.908 | 0.089 | 1.895 | 0.097 | 1.994 | 1.727 | 2.687 | 0.000 | 0.000 | 0.000 |
| rtt-001ms | S2 | 150 | 2.019 | 2.010 | 2.029 | 0.058 | 2.031 | 0.085 | 2.130 | 1.842 | 2.584 | 0.123 | 0.109 | 0.140 |
| rtt-001ms | S3 | 150 | 2.812 | 2.796 | 2.832 | 0.263 | 3.185 | 0.763 | 4.810 | 2.671 | 6.893 | 0.916 | 0.896 | 0.937 |
| rtt-001ms | S4 | 150 | 2.707 | 2.679 | 2.734 | 0.144 | 2.945 | 0.613 | 4.361 | 2.555 | 5.753 | 0.811 | 0.779 | 0.843 |
| rtt-010ms | S0 | 150 | 11.021 | 10.989 | 11.054 | 0.131 | 11.028 | 0.103 | 11.175 | 10.797 | 11.460 | 0.000 | 0.000 | 0.000 |
| rtt-010ms | S2 | 150 | 11.162 | 11.139 | 11.194 | 0.102 | 11.169 | 0.083 | 11.307 | 10.971 | 11.435 | 0.141 | 0.107 | 0.188 |
| rtt-010ms | S3 | 150 | 21.116 | 21.082 | 21.159 | 0.197 | 21.122 | 0.127 | 21.304 | 20.801 | 21.416 | 10.095 | 10.048 | 10.157 |
| rtt-010ms | S4 | 150 | 21.035 | 20.980 | 21.094 | 0.196 | 21.048 | 0.178 | 21.290 | 20.757 | 22.271 | 10.014 | 9.954 | 10.075 |
| rtt-050ms | S0 | 150 | 51.118 | 51.107 | 51.131 | 0.078 | 51.125 | 0.076 | 51.252 | 50.949 | 51.501 | 0.000 | 0.000 | 0.000 |
| rtt-050ms | S2 | 150 | 51.313 | 51.297 | 51.319 | 0.078 | 51.324 | 0.117 | 51.449 | 51.170 | 52.286 | 0.195 | 0.179 | 0.208 |
| rtt-050ms | S3 | 150 | 101.260 | 101.213 | 101.291 | 0.183 | 101.251 | 0.127 | 101.440 | 100.928 | 101.743 | 50.141 | 50.093 | 50.172 |
| rtt-050ms | S4 | 150 | 101.179 | 101.136 | 101.208 | 0.150 | 101.193 | 0.213 | 101.353 | 100.891 | 103.420 | 50.061 | 50.020 | 50.091 |
| rtt-100ms | S0 | 150 | 101.224 | 101.179 | 101.258 | 0.186 | 101.222 | 0.158 | 101.388 | 100.951 | 102.460 | 0.000 | 0.000 | 0.000 |
| rtt-100ms | S2 | 150 | 101.351 | 101.320 | 101.377 | 0.120 | 101.375 | 0.187 | 101.573 | 101.152 | 103.043 | 0.127 | 0.086 | 0.182 |
| rtt-100ms | S3 | 150 | 201.305 | 201.248 | 201.372 | 0.219 | 201.309 | 0.172 | 201.540 | 201.002 | 202.257 | 100.081 | 100.005 | 100.164 |
| rtt-100ms | S4 | 150 | 201.214 | 201.155 | 201.268 | 0.222 | 201.219 | 0.164 | 201.475 | 200.903 | 201.755 | 99.990 | 99.922 | 100.074 |

## Consistency across condition-specific batches

For S2--S4, `positive batches` counts the five observed batches whose median contrast with S0 was above zero. The full batch table is retained as a derived CSV, rather than repeated here.

| condition | case | batches | positive_batches | min_batch_contrast_ms | max_batch_contrast_ms |
| --- | --- | --- | --- | --- | --- |
| rtt-000ms | S0 | 5 | 0 | 0.000 | 0.000 |
| rtt-000ms | S2 | 5 | 5 | 0.136 | 0.177 |
| rtt-000ms | S3 | 5 | 5 | 0.529 | 0.753 |
| rtt-000ms | S4 | 5 | 5 | 0.477 | 0.606 |
| rtt-001ms | S0 | 5 | 0 | 0.000 | 0.000 |
| rtt-001ms | S2 | 5 | 5 | 0.111 | 0.139 |
| rtt-001ms | S3 | 5 | 5 | 0.899 | 0.921 |
| rtt-001ms | S4 | 5 | 5 | 0.786 | 0.850 |
| rtt-010ms | S0 | 5 | 0 | 0.000 | 0.000 |
| rtt-010ms | S2 | 5 | 5 | 0.097 | 0.195 |
| rtt-010ms | S3 | 5 | 5 | 10.043 | 10.168 |
| rtt-010ms | S4 | 5 | 5 | 9.953 | 10.069 |
| rtt-050ms | S0 | 5 | 0 | 0.000 | 0.000 |
| rtt-050ms | S2 | 5 | 5 | 0.187 | 0.206 |
| rtt-050ms | S3 | 5 | 5 | 50.078 | 50.168 |
| rtt-050ms | S4 | 5 | 5 | 50.019 | 50.083 |
| rtt-100ms | S0 | 5 | 0 | 0.000 | 0.000 |
| rtt-100ms | S2 | 5 | 5 | 0.104 | 0.194 |
| rtt-100ms | S3 | 5 | 5 | 100.004 | 100.180 |
| rtt-100ms | S4 | 5 | 5 | 99.885 | 100.084 |

## Observed pattern

At 10, 50, and 100 ms added RTT, S2 remains close to S0 in this harness, whereas S3 and S4 are about one added RTT above S0. That is an observation of these specific fresh TLS handshakes and their recorded packetization, not a general claim about all PQ TLS implementations or applications.

## Communication and TCP-connect descriptors

Bytes and packets are client-side TCP_INFO counters at SSL_connect completion. They do not include close packets or link/IP/TCP headers.

| condition | case | n | handshake_bytes_median | handshake_bytes_iqr | packet_count_median | packet_count_iqr | tcp_connect_ms_median | tcp_connect_ms_iqr |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rtt-000ms | S0 | 150 | 996.000 | 1.000 | 8.000 | 0.000 | 0.055 | 0.006 |
| rtt-000ms | S2 | 150 | 3260.000 | 1.000 | 9.000 | 0.000 | 0.054 | 0.006 |
| rtt-000ms | S3 | 150 | 11623.000 | 0.000 | 17.000 | 0.000 | 0.054 | 0.005 |
| rtt-000ms | S4 | 150 | 11559.000 | 0.000 | 17.000 | 0.000 | 0.054 | 0.007 |
| rtt-001ms | S0 | 150 | 996.000 | 2.000 | 8.000 | 0.000 | 1.125 | 0.049 |
| rtt-001ms | S2 | 150 | 3260.000 | 1.000 | 9.000 | 0.000 | 1.116 | 0.040 |
| rtt-001ms | S3 | 150 | 11623.000 | 0.000 | 18.000 | 0.000 | 1.121 | 0.039 |
| rtt-001ms | S4 | 150 | 11559.000 | 0.000 | 18.000 | 0.000 | 1.123 | 0.048 |
| rtt-010ms | S0 | 150 | 996.000 | 1.000 | 8.000 | 0.000 | 10.148 | 0.073 |
| rtt-010ms | S2 | 150 | 3260.000 | 1.000 | 9.000 | 0.000 | 10.158 | 0.107 |
| rtt-010ms | S3 | 150 | 11623.000 | 0.000 | 19.000 | 0.000 | 10.150 | 0.089 |
| rtt-010ms | S4 | 150 | 11559.000 | 0.000 | 19.000 | 0.000 | 10.152 | 0.064 |
| rtt-050ms | S0 | 150 | 996.000 | 1.000 | 8.000 | 0.000 | 50.379 | 0.147 |
| rtt-050ms | S2 | 150 | 3260.000 | 2.000 | 9.000 | 0.000 | 50.352 | 0.154 |
| rtt-050ms | S3 | 150 | 11623.000 | 0.000 | 19.000 | 0.000 | 50.364 | 0.133 |
| rtt-050ms | S4 | 150 | 11559.000 | 0.000 | 19.000 | 0.000 | 50.364 | 0.126 |
| rtt-100ms | S0 | 150 | 996.000 | 1.000 | 8.000 | 0.000 | 100.299 | 0.132 |
| rtt-100ms | S2 | 150 | 3260.000 | 1.000 | 9.000 | 0.000 | 100.285 | 0.148 |
| rtt-100ms | S3 | 150 | 11623.000 | 0.000 | 19.000 | 0.000 | 100.285 | 0.141 |
| rtt-100ms | S4 | 150 | 11559.000 | 0.000 | 19.000 | 0.000 | 100.290 | 0.158 |

## Interpretation boundary

The results characterize this one native Linux namespace/veth/netem case study with fixed symmetric delay, one OpenSSL build, fresh local processes, and local test credentials. They do not estimate browser behavior, public-PKI interoperability, Internet behavior, loss, congestion, bandwidth limitation, jitter, other hosts, or production workload effects.
