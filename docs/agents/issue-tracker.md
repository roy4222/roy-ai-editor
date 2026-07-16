# Issue tracker: GitHub

Issues and specs for this repo live as GitHub Issues in `roy4222/roy-ai-editor`.

## Conventions

- When a skill says to publish to the issue tracker, create a GitHub issue.
- Prefer the connected GitHub tools for issue reads and writes. The `gh` CLI is an acceptable fallback when it is installed and authenticated.
- Infer the repository from `git remote -v`; do not silently publish to a different repository.
- Read the issue body, labels, and comments before acting on an existing issue.
- Apply and remove labels using the vocabulary in `docs/agents/triage-labels.md`.

## Pull requests as a triage surface

**PRs as a request surface: no.**

Pull requests are implementation and review surfaces, not substitutes for feature requests or specs. GitHub shares one number space across issues and PRs, so resolve the item type before acting on a bare number.
