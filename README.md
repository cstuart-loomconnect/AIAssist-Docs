# AIAssist-Docs

The documentation site for the [AIAssist](https://github.com/cstuart-loomconnect/AIAssist) Salesforce package, built with MkDocs Material and published to GitHub Pages:
https://cstuart-loomconnect.github.io/AIAssist-Docs/

## Layout

| Path | What is in it |
|---|---|
| `documentation/` | The hand-written pages. `reference/`, `changelog.md`, `codebase-health.md` and `_stats.md` are generated on every build and are not committed. |
| `mkdocs.yml` | Site configuration and navigation. |
| `scripts/generate.py` | Builds the generated pages from a clone of AIAssist (Apex, objects, LWC, permission sets, git history). Standard library only. |
| `scripts/requirements.txt` | MkDocs Material. |
| `.github/workflows/deploy.yml` | Generates, builds with `--strict` and deploys to Pages. |

## Run it locally

Clone AIAssist next to this repo (with `master` checked out and full history), then:

```bash
pip install -r scripts/requirements.txt
python3 scripts/generate.py ../AIAssist
mkdocs serve
```

`generate.py` also accepts `AIASSIST_PATH`, or finds `./aiassist` or `../AIAssist` on its own.

## When it publishes

- Push to `master` here.
- Every merge into AIAssist `master`, when AIAssist has the `DOCS_DISPATCH_TOKEN` secret (a fine-grained token with **Contents: read and write** on this repo only).
- Daily at 06:00 UTC as a fallback.
- By hand from the Actions tab.

## One-off setup

**Settings > Pages > Build and deployment > Source = GitHub Actions.**

Then turn Pages off in the AIAssist repo (Settings > Pages), so the old site at `/AIAssist/` stops being served.
