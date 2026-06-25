---
name: idm-git-pr-publish
description: Use when the operator asks to git-track accepted local work by creating a branch, staging intended files, committing, pushing, opening a PR, and returning the PR link plus the local-main git pull command. Do not use for unaccepted work, read-only audits, or partial Git actions.
---

# IDM Git PR Publish

Use this skill to turn accepted local work into a reviewable GitHub PR without re-planning the whole workflow.

## Preconditions

1. Confirm the operator has accepted the work or explicitly requested publication.
2. Inspect branch, remote, and worktree state.
3. Identify the exact intended changed-file set, including untracked files.
4. Stop if unrelated or ambiguous changes are present.

## Workflow

1. Create or switch to a `codex/` branch unless the operator specified another branch name.
2. Stage only the intended files.
3. Run scope and whitespace checks before committing:

```bash
git status --short
git diff --cached --name-only
git diff --cached --stat
git diff --cached --check
```

4. Commit with a terse message that describes the full diff.
5. Run any lightweight validation relevant to the changed files.
6. Push the branch with upstream tracking.
7. Open a ready PR when the operator asks for a merge link; otherwise default to draft.
8. Verify the PR URL, base branch, head branch, and mergeability when possible.
9. Report the branch, commit, PR link, validation, and local-main update command.

## Safety Rules

- Never stage unrelated files silently.
- Never use `git add -A` when the worktree is mixed.
- Never force-push, reset, rebase, delete branches, or merge without explicit operator authorization.
- Keep scientific claims provisional unless the accepted work already contains reviewed evidence.

## Required Final Command

Include the corresponding local-main update command:

```bash
git switch main
git pull --ff-only origin main
```
