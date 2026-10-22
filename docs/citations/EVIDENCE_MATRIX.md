# Citation Evidence Matrix

This is the pre-insertion evidence record for manuscript citations.  A source
may be cited in prose only for one of the claim forms recorded below.  It is
not a general bibliography and it does not license broader claims.

**Verification date:** 2026-10-22
**Verifier:** CDX  
**Scope of this first batch:** normative TLS/PQC terminology and standards.
Empirical findings and related-work sources will be recorded in later batches,
after their publisher records and supporting passages have been checked.

## Approved sources and claim bounds

| ID | Complete bibliographic record | Stable identifier | Exact supporting location | Claim wording approved for this manuscript | Status / caveat |
| --- | --- | --- | --- | --- | --- |
| TLS-9846 | E. Rescorla, *The Transport Layer Security (TLS) Protocol Version 1.3*, RFC 9846, IETF, July 2026. | DOI: [10.17487/RFC9846](https://doi.org/10.17487/RFC9846) | Abstract; §§1, 1.2, and 2. | “TLS 1.3 establishes a secure channel through a handshake that negotiates cryptographic parameters, authenticates peers, and establishes shared keying material.” | **Approved.** RFC 9846 is the current TLS 1.3 specification and obsoletes RFC 8446. Do not cite RFC 8446 as the current normative TLS source. |
| NIST-203 | National Institute of Standards and Technology, *Module-Lattice-Based Key-Encapsulation Mechanism Standard*, FIPS 203, August 2024. | DOI: [10.6028/NIST.FIPS.203](https://doi.org/10.6028/NIST.FIPS.203) | Abstract; parameter-set statement. | “FIPS 203 specifies ML-KEM, including ML-KEM-512, ML-KEM-768, and ML-KEM-1024.” | **Approved.** NIST lists a future errata/update notice; do not claim that no errata exist. The allowed statement is unaffected by that notice. |
| NIST-204 | National Institute of Standards and Technology, *Module-Lattice-Based Digital Signature Standard*, FIPS 204, August 2024. | DOI: [10.6028/NIST.FIPS.204](https://doi.org/10.6028/NIST.FIPS.204) | Abstract. | “FIPS 204 specifies ML-DSA for digital-signature generation and verification.” | **Approved.** NIST lists potential future minor corrections; do not make claims about the absence of errata. |
| NIST-227 | G. Alagic, E. Barker, L. Chen, D. Moody, A. Robinson, H. Silberg, and N. Waller, *Recommendations for Key-Encapsulation Mechanisms*, NIST SP 800-227, September 2025. | DOI: [10.6028/NIST.SP.800-227](https://doi.org/10.6028/NIST.SP.800-227) | Abstract; §4.6 when hybrid-combiner details are needed. | “NIST SP 800-227 provides recommendations for the secure implementation and use of KEMs.” | **Approved.** Use only for KEM design/use guidance; it is not evidence of measured TLS performance. |
| RFC-10024 | K. Kwiatkowski, P. Kampanakis, B. E. Westerbaan, and D. Stebila, *Post-Quantum Traditional (PQ/T) Hybrid Key Agreement Mechanisms for TLS 1.3*, RFC 10024, IETF, August 2026. | DOI: [10.17487/RFC10024](https://doi.org/10.17487/RFC10024) | Abstract; §§1–4; §7.1. | “RFC 10024 standardizes X25519MLKEM768 as a TLS 1.3 hybrid key-agreement group combining X25519 ECDHE and ML-KEM-768.” | **Approved.** This supports the label and standardization status of S2/S3’s group. It must not be used to describe S4 as standardized or hybrid. |
| SIKERIDIS-2020 | D. Sikeridis, P. Kampanakis, and M. Devetsikiotis, “Post-Quantum Authentication in TLS 1.3: A Performance Study,” *Network and Distributed System Security Symposium (NDSS)*, 2020. | DOI: [10.14722/ndss.2020.24203](https://doi.org/10.14722/ndss.2020.24203) | Abstract; performance-evaluation description; NDSS paper record. | “Prior work has evaluated the latency and throughput implications of post-quantum authentication in TLS 1.3 under realistic network conditions.” | **Approved.** This is evidence of the study’s scope, not a transferable magnitude or ranking for the present study. |
| SOSNOWSKI-2023 | M. Sosnowski, F. Wiedner, E. Hauser, L. Steger, D. Schoinianakis, S. Gallenmüller, and G. Carle, “The Performance of Post-Quantum TLS 1.3,” in *Companion of the 19th International Conference on emerging Networking EXperiments and Technologies (CoNEXT Companion ’23)*, 2023, pp. 19–27. | DOI: [10.1145/3624354.3630585](https://doi.org/10.1145/3624354.3630585) | Abstract; §§1–3; reproducibility-artifact record. | “Prior work has jointly examined post-quantum key-agreement and signature choices in TLS 1.3, including end-to-end latency, transmitted volume, and constrained-network conditions.” | **Approved.** The paper used its own algorithms, implementation and measurement design. Do not compare its numerical results directly with ours. |
| MONTENEGRO-2026 | J. A. Montenegro, R. Rios, and J. López-Cerezo, “A Performance Evaluation Framework for Post-Quantum TLS,” *Future Generation Computer Systems*, vol. 175, Art. 108062, 2026. | DOI: [10.1016/j.future.2025.108062](https://doi.org/10.1016/j.future.2025.108062) | Abstract; §§1–2. | “Recent work provides an OpenSSL/OQS-based framework for comparing classical, hybrid and post-quantum TLS configurations across controlled and scenario-based conditions.” | **Approved.** It uses an OpenSSL/OQS integration; do not represent it as evidence about native OpenSSL 3.5.9 behavior. |

## Manuscript insertion rules

1. Citation labels above are provisional authoring keys, not final IEEE
   reference numbers. Numbering is assigned only after the final bibliography
   is frozen.
2. Every prose claim that goes beyond an approved wording requires a new row
   with a verified supporting passage. In particular, do not infer deployment
   prevalence, production interoperability, security guarantees beyond the
   standard's own wording, or measured overhead from these sources.
3. The terminology in the current methodology is intentionally exact:
   `X25519MLKEM768` may be called an RFC 10024 hybrid group; `MLKEM768` in S4
   is described only as implementation-supported in the pinned OpenSSL build.
4. Vendor documentation may document the pinned OpenSSL implementation, but
   cannot substantiate protocol-standard or research-performance claims.

## Evidence still required before finalizing related work

- Sources for migration/crypto-agility framing, with claim-level evidence.
- OpenSSL 3.5.9 release/API evidence only where the manuscript needs an
  implementation-specific fact beyond what the reproducibility artifacts show.

