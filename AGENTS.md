# AGENTS.md

`codex-universal` is the reference container image for Codex environments — a Dockerfile plus setup and entrypoint shell scripts that install and select language runtimes. There is no application code, no package manager manifest, and no test suite; changes are validated by building the image and running `verify.sh`.

## Agent skills

### Issue tracker

Issues and specs live as GitHub issues in `bearsadsff/codex-universal`, driven through the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles use their default label strings (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: one `CONTEXT.md` at the repo root plus `docs/adr/` for decision records. Both are created lazily, so treat their absence as normal. See `docs/agents/domain.md`.

### Locally authored skills

`humanize` is authored here rather than installed from `mattpocock/skills`, so it has no `skills-lock.json` entry and the `skills` CLI does not manage it. Leave the lock file alone — an entry there would let a sync overwrite local edits. Edit the skill in place at `.kiro/skills/humanize/`, where `scripts/slopcheck.py` owns its target values.
