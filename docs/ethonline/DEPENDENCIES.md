# Toolchain and dependency record

## Current event runtime — 6 September 2026

Python 3.12.14 is the verified runtime. `pyproject.toml` pins direct runtime
dependencies and `sentinel/requirements.lock` pins the complete Linux verification
environment. Install the lock before installing the project with `--no-deps`.
Subgraph tooling remains pinned by its npm lockfile; Solidity uses 0.8.24.
The wheel includes all Sentinel submodules, Recipe JSON and the pinned official
ERC-7730 schema/license. See FINAL_AUDIT_2026-09-06.md for gate results.

The older preparation record below is retained as historical evidence.


> Verified locally on 3 September 2026. These are preparation-spike versions,
> not yet the final submission lock.

## Runtime and direct dependencies

| Component | Version | Scope | Evidence/status |
|---|---:|---|---|
| Python | 3.11.9 | write-path environment | installed; `.venv` created |
| `web3` | 7.16.0 | Python spike runtime | exact pin |
| `py-solc-x` | 2.0.5 | Solidity compilation | exact pin |
| `python-dotenv` | 1.2.3 | local environment loading | exact pin |
| Solidity compiler | 0.8.24 | spike contract | local binary; compile verified |
| Node.js | 22.17.1 | Graph CLI runtime | locally observed |
| `@graphprotocol/graph-cli` | 0.98.1 | local dev-only CLI | exact `package.json` + lockfile |

## Development checks

| Tool | Version | Last result |
|---|---:|---|
| pytest | 9.1.1 | 6 passed; one upstream `websockets.legacy` deprecation warning |
| Ruff | 0.16.6 | pass |
| mypy | 2.3.1 | strict pass for `deploy.py` and `pause_tx.py` |
| Gitleaks | 8.30.1 | first-party directory scan: no leaks |

## Known security/dependency risk

`npm audit` for Graph CLI reports 15 transitive advisories: 1 critical, 10 high,
4 moderate. The critical path includes `decompress@4.2.1`. A non-forced audit fix
does not clear them; `--force` proposes a breaking CLI downgrade to 0.91.1 and is
not accepted as remediation.

Controls:

- CLI is local, pinned, unprivileged and dev-only;
- use only our local ABI/config and official Graph endpoints/templates;
- never process untrusted archives or third-party project templates;
- keep deploy/query keys out of arguments, logs and Git;
- re-check upstream and `npm audit` before submission;
- record any version change and rerun codegen/build/deploy verification.

## Reproducibility boundary

Generated environments and binaries are ignored: `.venv`, `node_modules`,
`.solcx`, caches and deployment secrets. The reproducible inputs are exact
requirement files, `package.json`, `package-lock.json`, source files and setup
instructions. Final product dependencies require their own event-period lock and
clean-clone verification.

## Real-model rehearsal runtime, evening 6 September

- Ollama 0.33.3, local Docker CPU execution.
- Image digest: `ollama/ollama@sha256:32931b46719f673c05fdbaa81ccb26da18ea4a1c57590a754874ab28ba269eb2`.
- Model: `qwen3:4b-instruct-2507-q4_K_M`, 2,497,293,803 bytes, Apache-2.0.
- Model digest: `0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0`.
- Python 3.12.14 with the committed requirements lock.
- Local model port: 127.0.0.1:11434; evidence demo API: 127.0.0.1:8088.
- Benchmark request timeout can be explicitly set to 120 seconds for CPU runs;
  this does not modify the action classifier's timeout.

Official model metadata: https://ollama.com/library/qwen3:4b-instruct-2507-q4_K_M
Official container instructions: https://docs.ollama.com/docker

The owner approved the local installation. Model files persist in the
`nexguard-sentinel-ollama` Docker volume. Containers are local development tools,
not a production deployment. Keep a WSL session active while recording on this
host; WSL shutdown stops these non-restarting demo services.
