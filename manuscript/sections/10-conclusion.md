# 10 Conclusion

This work reports a reproducible, controlled TLS 1.3/OpenSSL migration case
study rather than a universal benchmark. In the primary Ubuntu campaign, the
three selected non-classical configurations had positive fresh-handshake
latency contrasts relative to the X25519/ECDSA P-256 baseline in every
retained batch. The hybrid-key-establishment/ECDSA case had the smallest
contrast, while the ML-DSA-65 cases had larger contrasts and higher measured
handshake byte and packet descriptors.

The follow-ups clarify why a migration decision cannot be based on one local
latency number. The local compatibility matrix showed that the defined
dual-capable profile bridged the other evaluated profiles, whereas some strict
profile pairings failed before certificate verification because they had no
common group. The Windows campaign reproduced the direction of the
within-platform contrasts without supporting an absolute operating-system
comparison. Under the fixed-delay network topology, the S3 and S4 contrasts
were close to one added RTT at 10, 50, and 100 ms, whereas S2 stayed close to
the baseline.

These results are specific to the pinned OpenSSL implementation, four chosen
configurations, local credentials, tested hardware, and controlled transport
conditions. They neither predict Internet-scale interoperability nor prescribe
a production migration sequence. Their contribution is a traceable method and
evidence set that separates configuration behavior, transition compatibility,
and network sensitivity. Future work should independently replicate the
campaign across TLS stacks and hardware, extend the network model to loss and
congestion, and evaluate real peer and public-PKI constraints before making
deployment-wide claims.
