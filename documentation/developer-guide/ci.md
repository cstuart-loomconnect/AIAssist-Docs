# CI and releases

This page says what runs on a pull request, where the workflows live, the pull request and commit conventions, and how this documentation site is built and published.

## Where the workflows live

The checks are in their own repository, [AIAssist-CICD](https://github.com/cstuart-loomconnect/AIAssist-CICD), as reusable workflows. AIAssist keeps only small caller workflows in `.github/workflows/` that point at them, pinned to the `v1` release branch (`@v1`), so a change to CI never lands in the package repo by accident.

| Caller in AIAssist | Runs (in AIAssist-CICD) | Trigger |
|---|---|---|
| `pr-validation.yml` | `pr-validation.yml`, which calls `scratch-org-tests.yml` | Pull request into `development` or `master` |
| `pr-hygiene.yml` | `pr-hygiene.yml` | Pull request into `development` or `master` (opened, edited, updated) |
| `nightly.yml` | `nightly.yml`, which calls `scratch-org-tests.yml` | Manual only for now. The schedule is commented out. |

Each reusable workflow checks out AIAssist at the root and AIAssist-CICD into `.cicd/`, so the scripts and config in AIAssist-CICD run against `force-app`.

### What PR Validation checks

| Job | Check |
|---|---|
| Prettier + ESLint | `npm run prettier:verify` and ESLint over the `aura` and `lwc` folders. |
| SLDS Validator | SLDS styling rules in LWC HTML and CSS. |
| Salesforce Code Analyzer | PMD, ESLint, regex, retire-js and security rules with the `Recommended` and `AppExchange` selectors. Fails on severity 2 (High) or worse. Configured in `config/code-analyzer.yml` in AIAssist-CICD. |
| Dependency audit | `npm audit --audit-level=high` (does not fail the run). |
| Naming conventions | `scripts/check-naming.js` in AIAssist-CICD. Exceptions go in its `config/naming-exceptions.txt`. |
| Scratch org + Apex tests | Runs when the checks above have not failed. Creates a scratch org from `config/project-scratch-def.json`, does a check-only deploy, deploys, assigns the permission sets (`assign-permsets.js`), runs `RunLocalTests` and requires 75% coverage (`check-coverage.js`). |
| Post results to PR | On a pull request, posts one comment with the results (`pr-comment.js`). |

The scratch org job needs a secret in the AIAssist repo, `DEVHUB_SFDX_AUTH_URL`, created with `sf org auth show-sfdx-auth-url --target-org <devhub> --no-prompt`.

Dependabot (`.github/dependabot.yml` in AIAssist) opens weekly update pull requests for npm and GitHub Actions, targeting `development`.

### Changing a check

Open a pull request in AIAssist-CICD. Once it is merged into `main`, fast-forward the `v1` branch to `main`; AIAssist picks it up on its next pull request. A breaking change (a new required input or secret) gets a new branch, `v2`, and the callers in AIAssist are updated to match. The AIAssist-CICD README has the steps.

To run the checks locally, clone AIAssist-CICD next to AIAssist, then from AIAssist:

```bash
node ../AIAssist-CICD/scripts/check-naming.js force-app ../AIAssist-CICD/config/naming-exceptions.txt
```

## Branches

| Branch | Use |
|---|---|
| `development` | The main branch. Features merge here and the nightly build targets it. |
| `feature/<name>` | One branch per piece of work, created from `development`. |
| `master` | Release-ready code only, and the GitHub default branch. Merge `development` into it only for a release. The docs site is built from it. |

Scheduled workflows only run from the default branch, so the nightly schedule would only start working once it reaches `master`.

## Pull requests and commits

Open pull requests from `feature/*` into `development`. The title (and the commit messages in this repository's history) use `type: subject`, with a lowercase subject.

| Type | Use for |
|---|---|
| `feat` | A new capability |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `refactor` | A change that does not alter behaviour |
| `test` | Tests only |
| `perf` | A performance change |
| `build` | Build or dependency changes |
| `ci` | Workflows and CI scripts |
| `chore` | Anything else that is housekeeping |

Examples: `feat: add agent wizard`, `fix: handle empty message queue`. Dependabot titles are exempt.

PRs are labelled from the files they change (`config/labeler.yml` in AIAssist-CICD):

| Label | Files |
|---|---|
| `apex` | `classes`, `triggers` |
| `lwc` | `lwc` |
| `aura` | `aura` |
| `objects` | `objects`, `customMetadata` |
| `flows` | `flows` |
| `security` | `permissionsets`, `externalCredentials`, `namedCredentials` |
| `ci` | `.github`, `.husky`, `package.json`, `sfdx-project.json` |
| `docs` | any `.md` file |

API names must follow the table in `CONTRIBUTING.md` (PascalCase for objects, fields, classes and permission sets; camelCase for Lightning web components; letters and digits only for Aura). Run `check-naming.js` from AIAssist-CICD (see above) to check before you push.

A pre-commit hook (`.husky`) runs `lint-staged`: Prettier and ESLint on the files you changed, plus `sfdx-lwc-jest` on related LWC files with `--passWithNoTests`.

## The documentation site

The site is MkDocs Material and lives in its own repository, [AIAssist-Docs](https://github.com/cstuart-loomconnect/AIAssist-Docs). The hand-written pages are in `documentation/` and the navigation is in `mkdocs.yml`. Some pages are generated from the AIAssist source on every build, so they cannot go stale, and are not committed (they are listed in `.gitignore`):

| Generated | Contents |
|---|---|
| `documentation/_stats.md` | The numbers on the home page |
| `documentation/changelog.md` | Merged pull requests, from the AIAssist git history |
| `documentation/codebase-health.md` | Checks worked out from the AIAssist source |
| `documentation/reference/` | Apex, data model and object pages, Lightning web components, permission sets |

`scripts/generate.py` writes them. It reads a clone of AIAssist, so it needs to know where that is: pass the path, set `AIASSIST_PATH`, or keep the two repos side by side. Use a clone with full history and `master` checked out for a complete changelog.

### Run it locally

```bash
# from AIAssist-Docs, with AIAssist cloned next to it
pip install -r scripts/requirements.txt
python3 scripts/generate.py ../AIAssist
mkdocs serve
```

Use `mkdocs build --strict` to check for broken links: the publish workflow uses it, so a warning fails the build.

### How it is published

`deploy.yml` in AIAssist-Docs checks out this repo and AIAssist's `master` branch with full history, runs `generate.py`, then `mkdocs build --strict`, and deploys the `site` folder to GitHub Pages. It runs when:

- a page in AIAssist-Docs changes on `main`,
- a pull request is merged into AIAssist's `master`, if the docs trigger is set up (below),
- every morning at 06:00 UTC, as a fallback,
- or by hand from the Actions tab.

One-off setup in AIAssist-Docs: **Settings > Pages > Build and deployment > Source = GitHub Actions**.

For an immediate rebuild after each release merge: create a fine-grained personal access token with **Contents: read and write** on AIAssist-Docs only, and save it in AIAssist as the secret `DOCS_DISPATCH_TOKEN`. The `docs-trigger.yml` caller in AIAssist then pings AIAssist-Docs on every push to `master`. Without the secret it does nothing, and the daily build picks up the change.

To edit a hand-written page, change the file under `documentation/` in AIAssist-Docs and open a `docs:` pull request there. Do not edit generated pages: change the AIAssist source, or `scripts/generate.py`.
