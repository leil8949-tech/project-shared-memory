---
name: project-shared-memory
description: Initialize, repair or upgrade folder-scoped local project memory so Codex tasks can reuse a concise snapshot and confirmed history. Use for project-memory setup, V01 migration, explicit state synchronization or memory health checks; not raw chat export or cloud synchronization.
metadata:
  version: "2.0.0"
---

# Project Shared Memory — V02

Maintain a concise project snapshot and durable local records. Installing this
Skill does not initialize every project or synchronize running tasks automatically.

## Select the operation and root

- **Initialize** a new project: `--mode init` (the default).
- **Repair / upgrade** an existing project: `--mode repair`. Preserve records and
  custom AGENTS.md rules; update only this Skill's marked block, with local backups.
- **Inspect** without changes: `--mode check`. Do not initialize during a review.
- **Synchronize state** when asked: read the snapshot and only relevant recent
  history, resolve conflicting decisions, then use the guarded write workflow below.

Use the project root selected by the user, not an incidental shell subdirectory.
For a descendant task, use the known directory containing its memory AGENTS.md.
Do not scan above the selected workspace to discover unrelated memory. If there
is an independently initialized child root, use that child's memory; a shared
multi-project parent is a separate design requiring an explicit user request.

Locate `scripts/init_project_memory.py` **relative to this installed SKILL.md** and
run it by absolute path with an available Python 3.9+ interpreter. Quote paths.
No third-party Python package, network service or project code index is required.

```text
python "<skill-dir>/scripts/init_project_memory.py" --root "<project-root>" --mode init
python "<skill-dir>/scripts/init_project_memory.py" --root "<project-root>" --mode check
```

Initialization creates missing records, appends/updates one managed AGENTS.md
block, adds root-scoped Git ignore patterns and writes `.project-memory.json`.
It never summarizes history automatically. If a new snapshot accompanies existing
history, inspect relevant recent sections and write a verified summary. If a valid
snapshot already exists, do not load all historical files or refresh it needlessly.
An empty, non-UTF-8, linked or directory-shaped record is an error, not a license
to overwrite it. Investigate the named file and preserve the original.

## Read and write cheaply

At task start read PROJECT_CONTEXT.md. When continuing state-dependent work,
`--mode status` returns only its hash and size; reread only if changed or unavailable
in context. Detailed history is read by relevant section, never by default.

Before a confirmed change, use `--mode read` to get the affected record and its
hash in one response. Build the candidate from that content/hash pair, not from
an earlier cached read and a newer hash. Prepare a UTF-8 candidate under
`<project-root>/.project-memory-candidates/`.
Use the helper to write; do not directly overwrite shared records:

```text
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode read --file PROJECT_CONTEXT.md
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode write --file PROJECT_CONTEXT.md --expected-sha "<sha256>" --content-file "<root>/.project-memory-candidates/context.md"
```

Use `--file progress.md --append` with a candidate containing only the new dated
entry and the current progress hash. On conflict, reread, merge and retry; do not
reuse an old hash or bypass a lock. A persistent lock requires verifying the writer
has stopped before removal. Writes are atomic per existing file, not a transaction
across all records. On interruption inspect the snapshot and last progress entries
before resuming; retain checkpoints distinguishing completed and unverified work.

Keep the snapshot within 100 lines and 6000 characters (not a token guarantee).
Keep historical detail in the existing records; archive large records only when
useful and authorized, retaining links and facts. Cite confirmation dates/sources
for important decisions and explicitly mark superseded ones. Never record raw
chat transcripts, credentials or unconfirmed ideas.

## Boundaries and verification

Folder scope is an instruction convention, not an OS sandbox. Cooperative locks
coordinate helper users; external editors can bypass them. There is no daemon,
live cross-task event stream or automatic cross-worktree/cloud synchronization.
Memory on disk is local, but using Codex to read it is subject to Codex's normal
data handling; this Skill does not promise offline inference.

`--privacy local` is the default and adds Git ignore rules without removing tracked
files. Report any `tracked` or `unknown` Git status honestly. Do not untrack files,
rewrite commits or change cloud backup settings without a separate request.
`--privacy unchanged` preserves existing ignore configuration. Backups/candidates
also contain private project data; keep them out of the public Skill package.

After setup run `--mode check`, report the exact root, changes and any warnings.
Check success verifies files/rules, not real cross-task behavior. When asked for
end-to-end verification, have a new task read a harmless confirmed test fact from
the same physical root. Do not claim task or worktree sharing without that test.

## Invocation

`$project-shared-memory 为当前项目初始化本地共享记忆。`

`$project-shared-memory 将当前项目已有共享记忆规则升级为 V02，保留历史和其他规则。`

`$project-shared-memory 只检查当前项目共享记忆，不修改文件。`
