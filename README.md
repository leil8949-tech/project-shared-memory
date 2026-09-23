# Project Shared Memory · V02

让同一个项目文件夹里的 Codex 任务，通过简短的项目快照与本地记录接续工作。

版本：**2.0.0（V02）**。调用名称保持 **`project-shared-memory`**。
需要 Python **3.9+**，仅使用标准库。

## 安装

在 Codex 中输入：

```text
$skill-installer 从 https://github.com/leil8949-tech/project-shared-memory 安装 Skill。Skill 位于仓库根目录，使用 --path . --name project-shared-memory。
```

如果使用安装器脚本，参数为：

```text
python "<skill-installer-dir>/scripts/install-skill-from-github.py" --repo leil8949-tech/project-shared-memory --path . --name project-shared-memory
```

把占位路径替换为实际安装器路径。安装后重新打开任务；若未发现 Skill，重启 Codex。
已安装旧版时，应先备份旧 Skill，再更新同名目录；安装器可能拒绝覆盖现有目录。
不要把个人项目历史复制进 Skill 安装目录或本仓库。

## 使用与旧项目升级

先在 Codex 中打开目标项目文件夹，再输入：

```text
$project-shared-memory 为当前项目初始化本地共享记忆。
```

已有 V01 项目使用：

```text
$project-shared-memory 将当前项目共享记忆升级为 V02，保留所有历史及 AGENTS.md 中的其他规则。
```

只检查时使用：

```text
$project-shared-memory 只检查当前项目共享记忆，不修改文件。
```

更新 Skill 安装包不会自动改写每个项目的规则；需要在相应项目中执行一次升级。
项目原有无标记的 V01 规则会保留，新 V02 规则作为独立标记段落添加。
如果自定义旧规则与新规则矛盾，需要核对具体冲突，不能盲目删除旧段落。

## V02 改进

- 合并、重复运行和升级只维护一个专用规则段落，保留其他项目规则和历史。
- 默认写入当天日期；拒绝空记录、非 UTF-8 文件、同名目录和链接目标。
- 阻止在磁盘根目录、用户主目录或 Skill 自身目录误建项目记忆。
- 用独占锁协调写入，用 SHA-256 检查旧内容，修改前保存本地备份。
- 新建文件采用排他创建；更新已有文件采用同目录临时文件和原子替换。
- 提供 init、repair、check、status、read、write，明确检查与修改的区别。
- 默认只读项目快照，继续任务时先检查是否变化，细节按需读取。
- 默认添加项目根目录下的 Git 忽略规则，并报告已跟踪或无法检查的状态。

## 本地文件结构

| 文件 | 作用 |
| --- | --- |
| `AGENTS.md` | 保留原规则，增加 V02 启动和回写规则 |
| `PROJECT_CONTEXT.md` | 默认读取的状态，最多 100 行、6000 字符 |
| `task_plan.md` | 目标、阶段、待办 |
| `findings.md` | 确认事实、来源及决定变更 |
| `progress.md` | 日期、完成事项、阶段检查点 |
| `.project-memory.json` | 当前规则版本与格式版本 |
| `.gitignore` | 根目录内记忆、备份、候选文件的忽略规则 |
| `.project-memory-backups/` | 改动前的私有备份，按原内容哈希命名 |

写入时临时创建 `.project-memory.lock`；正常结束会释放。
中断后留下的锁不会自动删除，需核实没有写入任务再处理。
备份保留历史副本，会占用空间；不会自动清理用户记录。

## 共享范围与实际边界

- A、B 两个独立项目分别初始化后各自读写自己的记忆。
- 子目录任务使用所属记忆根目录；显式初始化的独立子项目拥有自己的记忆。
- 多项目父层共享没有包含在 V02 中，不会自动扩展范围。
- 共享的是已确认并写入文件的状态，不会自动导入其他任务的完整聊天。
- 已打开的任务需要重新检查快照才能看到变化；没有后台实时同步服务。
- 不同物理目录、Git worktree、克隆或电脑不会因此自动共享文件。
- 文件夹隔离是任务行为约定，不是操作系统访问控制。
- 并发保护针对遵守同一 helper 协议的写入；直接编辑文件可绕过保护。
- 单文件替换具有原子性，多个记忆文件之间没有事务保证。中断后应核查已完成步骤。

## 隐私

本仓库只发布通用代码、模板、测试和说明，不应包含用户项目素材、个人路径、
聊天原文或生成后的项目记忆。初始化器没有网络上传、遥测或聊天记录读取功能。

记忆存储在使用者的本地项目中，但 Git、云盘、备份工具或手动分享仍可能将它们带走。
`.gitignore` 对已经跟踪的文件及历史提交无效，也无法限制云盘。脚本不自动删除 Git
记录、不取消文件跟踪、不改变云盘设置。Git 不可用时会明确报告未验证。
使用 Codex 读取文件仍受 Codex 本身的数据处理方式约束；本 Skill 不承诺离线推理。
不要记录密码、密钥或其他不应进入模型上下文的敏感内容。

## 手动运行与验证

以下 `<skill-dir>` 指此仓库/已安装 Skill 的目录，`<root>` 指明确的项目记忆根目录：

```text
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode init
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode repair
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode check
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode status
```

`--privacy local` 默认补充忽略规则；`--privacy unchanged` 不改变已有忽略配置。
检查或 status 不修改文件，输出简短 JSON。check 会指出缺失规则、异常文件和快照过长。
成功检查不等于已完成跨任务测试：在同一物理文件夹新开任务，询问一条已写入的无敏感
信息的确认事项，才能验证该环境中的接续效果。

需要回写时，先用 read 一次取得目标内容与对应 SHA，据此准备项目内部的 UTF-8
候选文件。不要把旧缓存内容与新取得的 SHA 配对：

```text
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode read --file PROJECT_CONTEXT.md
python "<skill-dir>/scripts/init_project_memory.py" --root "<root>" --mode write --file PROJECT_CONTEXT.md --expected-sha "<sha256>" --content-file "<root>/.project-memory-candidates/context.md"
```

追加进度时使用 `--file progress.md --append`，候选文件只写本次条目，并传入进度文件的
当前 SHA。冲突时重新读取并合并；不要绕开锁或强行使用旧版本覆盖。

运行回归测试：

```text
python -B -m unittest discover -s tests -v
```

测试只在临时目录创建合成项目，不需要真实项目素材或登录凭据。
