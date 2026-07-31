---
name: project-shared-memory
description: Initialize or repair a local project memory system that lets Codex conversations in the same folder share a concise current context and durable task history. Use when the user asks to make project chats remember previous work, share task history across new conversations, initialize folder memory, or set up cross-chat project continuity.
---

# Project Shared Memory

Deploy a local-only shared memory system in the current project root. Keep each project's memory isolated from parent directories and sibling projects.

## Workflow

1. Confirm the current working directory is the intended project root. Do not initialize a drive root, home directory, or a broad parent folder unless the user explicitly asks for a multi-project layer.
2. Run `scripts/init_project_memory.py --root <project-root>` using a usable Python interpreter.
3. Read the resulting `PROJECT_CONTEXT.md`. If `task_plan.md`, `findings.md`, or `progress.md` already existed, read them and replace the placeholder context with a concise, current snapshot. Do not overwrite existing historical detail.
4. Verify the five project files exist: `AGENTS.md`, `PROJECT_CONTEXT.md`, `task_plan.md`, `findings.md`, and `progress.md`.
5. Report the scope and the next-use prompt.

## Operating Rules

- `AGENTS.md` makes future conversations in this project load `PROJECT_CONTEXT.md` first and write back confirmed changes.
- Keep `PROJECT_CONTEXT.md` below 100 lines. Store only the current state, locked decisions, active work, latest verified change, next step, and links to detailed records.
- Keep `task_plan.md`, `findings.md`, and `progress.md` as the detailed history. Read them only when the current task needs the detail.
- Never copy raw conversation transcripts into project memory. Record only confirmed, reusable facts and decisions.
- Do not create a parent-level shared context or connect cloud storage in this workflow. Those are separate, explicit extensions.

## Re-run Behavior

The initializer is non-destructive: it creates missing files and leaves existing files unchanged. On a project that already has memory files, inspect and refresh the snapshot only when the user asks to synchronize or when the current work changes project state.

## Invocation

Use either form in a project-root conversation:

`$project-shared-memory 为当前项目初始化本地共享记忆。`

`使用 project-shared-memory 初始化当前项目的对话共享历史。`
