# Project Shared Memory

A portable Codex Skill for folder-scoped, cross-conversation project memory.

这是一个可移植的 Codex Skill，用于在同一个项目文件夹内建立轻量、可持续的跨任务共享记忆。

## 功能特点

- **文件夹隔离**：记忆只在当前项目目录及其子目录生效。
- **轻量加载**：新任务默认只读取简短的 `PROJECT_CONTEXT.md`。
- **按需读取**：需要细节时才加载计划、发现和进度记录。
- **安全初始化**：只创建缺失的文件，不覆盖已有内容。
- **本地保存**：不上传聊天记录，不默认连接云端，也不读取父目录或兄弟项目。

## 安装

在 Codex 中运行：

```text
$skill-installer 请从 https://github.com/leil8949-tech/project-shared-memory 安装 project-shared-memory
```

安装后如未立即出现在 Skill 列表中，请新建一个任务或重启 Codex。

## 使用

先在 Codex 中打开需要启用共享记忆的项目文件夹，然后运行：

```text
$project-shared-memory 为当前项目初始化本地共享记忆。
```

Skill 会在当前项目根目录创建以下文件：

- `AGENTS.md`：规定新任务如何读取和回写共享记忆。
- `PROJECT_CONTEXT.md`：默认加载的精简项目状态。
- `task_plan.md`：项目目标、阶段和待办。
- `findings.md`：素材、事实、时间码和验证结论。
- `progress.md`：按日期记录完成事项和交接。

## 工作方式

这不是完整聊天记录的自动同步。Codex 会把已经确认的项目状态、决定和下一步写入本地 Markdown 文件；其他在同一文件夹中开启的任务通过读取这些文件获得连续上下文。

例如：

- 在文件夹 A 中运行后，A 内的任务共享 A 的记忆。
- 在文件夹 B 中单独运行后，B 内的任务共享 B 的记忆。
- A 与 B 的记忆相互隔离，不会因为安装了同一个 Skill 而互相泄露。

## 隐私边界

本仓库只包含通用 Skill 指令和初始化脚本，不包含任何用户的项目素材、聊天历史或项目路径。实际记忆始终保存在使用者自己的项目文件夹中。
