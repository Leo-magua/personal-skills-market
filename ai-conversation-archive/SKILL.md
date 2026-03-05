---
name: ai-conversation-archive
description: 将各 AI 平台（如 deepseek、chatgpt、kimi）的对话记录同步到本地，维护 database.json 索引，并产出每会话的原始 JSON 与总结 MD。使用本 skill 当需要（1）从平台拉取会话列表并更新索引、（2）执行待处理/更新任务（抓取、保存、总结、更新索引）、（3）按需用浏览器抓取单则会话以补齐无 API 的平台、（4）查看或排错归档状态与日志。严禁自行编写批量化循环或任务队列逻辑，所有批处理与状态机均由技能内脚本完成。
---

# AI 对话本地归档

## 原则

- **索引与任务由脚本驱动**：`database.json` 的维护、pending/updating → completed 的状态流转、增量合并、写 action.log 均由 `scripts/` 下脚本完成。你不要实现“遍历所有会话并逐个处理”的代码。
- **你只做两件事**：（1）在合适时机**运行脚本**（sync_index、run_tasks、precheck_stale）；（2）当脚本报告某会话需要**浏览器抓取**时，用浏览器打开对应会话页，把单则会话的 user/assistant 对话保存为脚本要求的 `{session_sourceplatform}_{session_id}_raw.json`，然后再次运行 `run_tasks`。
- **单则会话抓取**：若平台无 API 或脚本标记为 `REQUIRES_BROWSER_FETCH`，你仅针对该会话用浏览器访问并保存为指定路径的 JSON，不写循环。**抓取前**：对话列表页需**下拉加载更早的对话**；进入单则会话详情页后，若页面有懒加载/分页，也需**滚动到底**以加载全部消息后再导出。

## 工作流速览

1. **维护索引**：运行 `scripts/sync_index.py`（或按 references 配置各平台列表来源），使 `database.json` 中出现新会话或已有会话被标为待更新。
2. **执行任务**：运行 `scripts/run_tasks.py`。脚本会处理所有 `pending` / `updating`：能通过 API 拉取的由脚本拉取；不能的会输出 `REQUIRES_BROWSER_FETCH` 及 `SAVE_AS_JSON <文件名>`，由你用浏览器抓取并保存为 data 目录下对应的 `{platform}_{session_id}_raw.json` 后重跑。
3. **总结与更新**：脚本在每次保存好 `{platform}_{session_id}_raw.json` 后，会调用 `data/config.json` 中的 summary_command 生成 `{platform}_{session_id}_abstract.md`，并回写 `session_abstract`、`session_tags` 与状态到 `database.json`。默认使用本 skill 自带的 `scripts/summarize.py`（见下方「总结脚本」）。
4. **定期重检**（可选）：运行 `scripts/precheck_stale.py`，将超过设定天数的已完成会话标为 `updating`，下次 `run_tasks` 时会做增量更新。

## 何时使用本 Skill

- 用户要求把某平台或全部平台的对话同步到本地、批量导出、或“把对话存档”。
- 用户要求更新已有归档（增量）、或重新生成摘要/标签。
- 用户要求检查归档状态、查看 action.log 或 database.json、或排查失败任务。

## 脚本用法（必读）

- **sync_index**  
  `python scripts/sync_index.py [--data-dir DIR] [--platform PLATFORM]`  
  从各平台列表源（API 或 references 中约定的列表文件）拉取会话列表，更新 `database.json`：新增为 `pending`，已有会话若平台侧时间更新则标为 `updating`。不抓取详情。

- **run_tasks**  
  `python scripts/run_tasks.py [--data-dir DIR] [--once]`  
  - 默认：持续处理所有 `pending`/`updating` 直到没有为止。  
  - `--once`：只处理一个任务后退出。  
  - 脚本会为每个任务：锁定状态、拉取或使用已有的 `{platform}_{session_id}_raw.json`、生成/更新 `{platform}_{session_id}_abstract.md`、更新索引与 `last_message_timestamp`、写 action.log。若某任务需浏览器抓取，脚本会打印 `REQUIRES_BROWSER_FETCH` 和 `SAVE_AS_JSON <文件名>`，此时你为该会话做一次浏览器抓取并保存为 data 目录下该文件名，再运行 `run_tasks`。

- **precheck_stale**  
  `python scripts/precheck_stale.py [--data-dir DIR] [--days 7]`  
  将 `database.json` 中 `completed` 且距 `last_message_timestamp`（或 `update_date`）超过 `--days` 天的记录改为 `updating`，供后续增量更新。

数据目录 `DIR` 默认为 skill 下的 `data/`，其中包含 `database.json`、`action.log`、`config.json`（含 summary_command）、`{session_sourceplatform}_{session_id}_raw.json`（原始对话）、`{session_sourceplatform}_{session_id}_abstract.md`（摘要）。**请在 skill 根目录下执行脚本**，例如：`python scripts/sync_index.py`、`python scripts/run_tasks.py`。

**总结脚本**：默认可用的摘要生成脚本位于 **`scripts/summarize.py`**。`data/config.json` 中已配置 `summary_command` 指向该脚本（路径可按需修改）。生成的 .md 包含标题、## 摘要、## 标签，你可直接编辑 _abstract.md 或更换 summary_command 使用自己的总结逻辑。

## 你禁止做的事

- 不要写“遍历 database.json 中所有 pending 并逐个请求/保存”的代码。
- 不要自己实现 pending → updating → completed 的状态更新逻辑或任务队列。
- 不要用自定义脚本替代本 skill 提供的 `sync_index` / `run_tasks` / `precheck_stale`。

## 参考资料

- **database 结构与字段**：见 `references/database_schema.md`。
- **平台列表与抓取方式（API vs 浏览器）**：见 `references/platforms.md`。新增平台或修改列表来源时只改配置/引用，不改核心流程。
