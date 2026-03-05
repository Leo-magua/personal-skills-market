# 平台列表与抓取方式

## 列表来源

- **有 API 的平台**：在配置或环境变量中设置 API 端点/密钥，`sync_index.py` 调用平台“会话列表”接口，得到 `session_id`、标题、时间等，写入或更新 `database.json`。
- **无 API / 仅浏览器**：列表可由你（或用户）维护，例如将“待归档会话”写成 `data/<platform>_list.json`，格式为数组，每项含 `session_id`、`title`、`dateinfo`、`original_data_url` 等；`sync_index.py` 读取该文件并合并进 `database.json`，新会话为 `pending`。

## 详情抓取（单则会话）

- **API**：`run_tasks.py` 内对该平台调用“会话详情”接口，直接得到完整对话并写入 `{platform}_{session_id}_raw.json`。
- **仅浏览器**：脚本无法拉取详情时，会输出 `REQUIRES_BROWSER_FETCH` 与 `SAVE_AS_JSON <文件名>`。由 agent 用浏览器打开该会话页（可用 `original_data_url` 或平台会话 URL 模板），将当前会话的 user/assistant 消息保存为约定格式的 JSON，写到 `data/<文件名>`（文件名为 `{platform}_{session_id}_raw.json`，session_id 中非法文件名字符会替换为下划线），再运行 `run_tasks.py`；脚本只负责合并、总结、更新索引。

## 浏览器抓取时：下拉加载更早对话

- **对话列表页**：各平台“历史对话列表”往往采用懒加载，只显示最近若干条；**需要向下滚动或点击“加载更多”**，直到更早的会话全部加载出来，再从中选择要归档的会话或获取完整列表。
- **单则会话详情页**：进入某条对话后，若页面只先加载最近几条消息，**需要滚动到底部或多次下拉/点击加载**，确保整段对话历史都加载完毕，再执行导出或保存为 `*_raw.json`，否则会漏掉更早的消息。

## 文件命名

- 原始对话：`{session_sourceplatform}_{session_id}_raw.json`（如 `deepseek_4846a5df-491e-4923-b31c-fe2e57f63c94_raw.json`）。
- 摘要：`{session_sourceplatform}_{session_id}_abstract.md`。session_id 中不宜作为文件名的字符会替换为下划线。

## 约定 JSON 格式（单则会话原始数据）

每个 `*_raw.json` 建议结构（供总结与增量合并）：

```json
{
  "session_id": "平台原始ID",
  "platform": "deepseek|chatgpt|kimi|...",
  "messages": [
    { "role": "user", "content": "...", "timestamp": "可选" },
    { "role": "assistant", "content": "...", "timestamp": "可选" }
  ],
  "last_message_timestamp": "最后一条消息的平台时间戳或 ISO 8601"
}
```

增量更新时，脚本根据 `last_message_timestamp` 只追加新消息，再重跑总结生成新 MD。

## 当前平台占位

- **deepseek**：若提供列表/详情 API，在 sync_index / run_tasks 的配置中填入；否则走浏览器 + `*_list.json`。
- **chatgpt**：同上。
- **kimi**：同上。

新增平台时在脚本的“平台配置”中增加一项，并注明 list/detail 是 `api` 还是 `browser`，不改变主流程。
