---
name: idm-scope-guard
description: Use whenever modifying files in the IDM symbolic-regression repository. Do not use for read-only audits unless the prompt asks for scope analysis.
---

# IDM Scope Guard

Use this skill to prevent hidden scope expansion.

## Before Editing

1. Inspect the current branch.
2. Run `git status --short`.
3. Identify pre-existing user changes.
4. Define the allowed file set from the prompt or authority document.
5. Stop if the requested edit would require files outside the allowed set.

## After Editing

Run:

```bash
git diff --name-only
git diff --stat
git status --short
```

## Allowed Files vs Changed Files Check

Use this pattern:

```text
allowed_files = prompt_authorized_files
changed_files = git diff --name-only plus untracked files from git status --short
outside_scope = changed_files - allowed_files
```

If `outside_scope` is not empty, stop and report `HALT_BLOCKED`.

## Rules

- Modify only allowed files.
- Preserve unrelated user work.
- Never silently expand scope.
- Never stage, commit, push, merge, or delete branches unless the operator explicitly authorizes that Git action.
