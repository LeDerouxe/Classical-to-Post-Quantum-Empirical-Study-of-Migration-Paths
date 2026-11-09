# Ubuntu-Windows Direction Comparison

## Comparison rule

This document compares only the direction of each platform's within-platform
median contrast against S0. It does not pool raw observations, subtract a
Windows latency from an Ubuntu latency, or estimate an operating-system effect.
The platforms used different native builds and timing implementations
(`CLOCK_MONOTONIC_RAW` on Ubuntu and QueryPerformanceCounter on Windows), even
though they used the same physical Intel Core i5-12450H, OpenSSL source commit,
TLS version, cipher suite, configurations, fresh-process design, batch count,
and nominal per-case sample size.

## Results

| Case | Ubuntu median ms | Ubuntu S0 contrast ms (95% CI) | Windows median ms | Windows S0 contrast ms (95% CI) | Contrast direction in five Ubuntu batches | Contrast direction in five Windows batches |
| --- | ---: | --- | ---: | --- | --- | --- |
| S0 | 0.834 | 0.000 | 1.439 | 0.000 | baseline | baseline |
| S2 | 0.989 | +0.156 [+0.115, +0.203] | 1.783 | +0.344 [+0.294, +0.406] | positive in 5/5 | positive in 5/5 |
| S3 | 1.436 | +0.603 [+0.501, +0.700] | 2.088 | +0.649 [+0.507, +0.788] | positive in 5/5 | positive in 5/5 |
| S4 | 1.312 | +0.478 [+0.383, +0.621] | 1.912 | +0.473 [+0.369, +0.631] | positive in 5/5 | positive in 5/5 |

All three non-classical configurations had a positive median contrast with S0
on both platforms, and every contrast had the same positive sign in every
observed batch on both platforms. The pooled median ordering was also the same
on the two platforms: S0 < S2 < S4 < S3.

These are qualitative direction checks. The numerical contrast sizes are
reported for transparency, but their cross-platform difference is not
interpreted: the experiment was not designed or powered as a paired
operating-system comparison, and the timing, operating-system, compiler, and
environmental contexts differ.

## Scope

The comparison adds same-device, cross-platform corroboration for contrast
direction only. It does not validate the Ubuntu communication and resource
descriptors on Windows, because those Linux-specific secondary measurements
were not replicated. It also does not support claims about external-network
performance or production interoperability.
