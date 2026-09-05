---
name: ai-dev-zoomcamp-git-ops
description: Use for ANY direct GitHub operation against the ai-dev-zoomcamp repo (Chemoday/ai-dev-zoomcamp) — commit/push, branches, pull requests, issues, releases, GitHub Actions runs/deploys, or repo settings. The configured token has full repository-wide access, so this skill is the entry point whenever the user asks to commit, push, sync, deploy, or otherwise manipulate this repo on GitHub.
---

# ai-dev-zoomcamp git ops

## Authentication

- The GitHub token lives in `$GITHUB_AI_DEV_ZOOMCAMP_TOKEN`, persisted in
  `~/.bashrc`.
- `~/.bashrc` only exports it for **interactive** shells (it has the
  standard `case $- in *i*) ;; *) return;; esac` guard near the top). Every
  `git` or `gh` command in this skill MUST be wrapped like this or the
  token will not be in scope and auth will fail:

  ```
  bash -ic '<command>'
  ```

- This repo's local `.git/config` already has a `credential.https://github.com.helper`
  configured to read that variable at push time. The token is never
  written to disk and never needs to be passed explicitly.
- Never print, echo, or otherwise include the raw token value in any
  command, file, or output.
- The `bash -ic` subshell starts in `$HOME`, not the repo directory —
  every command must `cd` back into the repo first, e.g.:

  ```
  bash -ic 'cd /mnt/d/Projects/Github/ai-dev-zoomcamp; git push -u origin main'
  ```

## Committing and pushing

1. `bash -ic 'git status'` — review what changed before staging anything.
2. Stage specific files by name (not `git add -A` / `git add .`) unless the
   user clearly wants everything staged.
3. Commit with a concise message describing *why*, in a HEREDOC to avoid
   quoting issues:
   ```
   bash -ic 'git commit -m "$(cat <<"EOF"
   <message>
   EOF
   )"'
   ```
4. Push: `bash -ic 'git push -u origin <branch>'` (only use `-u` the first
   time a new branch is pushed).
5. Confirm the push succeeded (check command exit status / `git status`).

## Branch management

- Create and switch: `bash -ic 'git checkout -b <branch-name>'`
- Switch: `bash -ic 'git checkout <branch-name>'`
- Push a new branch: `bash -ic 'git push -u origin <branch-name>'`
- Delete a local branch: `bash -ic 'git branch -d <branch-name>'`
- Delete a remote branch: `bash -ic 'git push origin --delete <branch-name>'`

## Other GitHub operations

The token has full repository-wide access, so any `gh` subcommand works
against this repo the same way, using the same `bash -ic '<command>'`
wrapper for auth:

- Pull requests: `gh pr create`, `gh pr merge`, `gh pr view`, etc.
- Issues: `gh issue create`, `gh issue list`, etc.
- Releases: `gh release create`, `gh release upload`, etc.
- Actions / deploys: `gh workflow run <name>`, `gh run watch`, `gh run view`.
- Anything not covered by a dedicated `gh` subcommand: `gh api ...`.

## Safety rules

- Never force-push (`--force` / `-f`) unless the user explicitly asks for it.
- Confirm with the user before: pushing directly to `main`, deleting any
  branch (local or remote) or the repo itself, merging a PR, publishing a
  release, triggering a deploy/workflow, changing repo visibility/settings,
  or any other action visible outside this local checkout.
- Only commit files the user would expect to be committed — flag anything
  that looks like a secret or credential before staging it.
- Because this token is full-access, treat every write operation as
  irreversible-until-proven-otherwise: state what you're about to do and
  get explicit confirmation first, rather than assuming broad scope means
  broad license to act unprompted.
