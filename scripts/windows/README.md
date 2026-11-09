# Windows validation workflow

Run this workflow only for Step 4 of `docs/PROJECT_ROADMAP.md`. It is a
separate Windows validation campaign, not an extension of the Ubuntu primary
campaign and not a general operating-system comparison.

The workflow accepts exactly one mode:

```powershell
python scripts/windows/run_final_windows.py --preflight-only
python scripts/windows/run_final_windows.py --smoke-test
python scripts/windows/run_final_windows.py --run
```

Before any mode, connect AC power and have the researcher select the explicitly
recorded `High performance` power scheme. The workflow deliberately does not
change this setting. It compiles the native harness, confirms the pinned
OpenSSL source and credentials, selects two active, non-sibling processor sets
with the highest reported performance class, and records the environment. A failed
preflight or smoke test blocks collection.

`--preflight-only` and `--smoke-test` write evidence under
`evidence/windows-final-workflow/`; neither writes campaign CSVs. The smoke
test performs one fresh loopback handshake for each case. `--run` creates one
new campaign only. It never resumes, appends to, or overwrites another
campaign. Main CSVs and their metadata are written below `data/raw/windows/`
and `data/metadata/windows/` respectively.

The campaign consists of five batches. Every batch contains ten warm-ups and
thirty measured fresh handshakes for S0, S2, S3, and S4. Client timing is the
`QueryPerformanceCounter` interval around `SSL_connect()`; each client and
server process confirms its affinity mask in the captured result. The workflow
uses only `127.0.0.1`; it needs no Internet connection during collection.
