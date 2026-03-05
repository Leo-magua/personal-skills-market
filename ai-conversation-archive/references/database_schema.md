# database.json 结构说明

根结构为 **JSON 数组**，每个元素为一条会话元数据。

| 字段名 | 说明 | 必需 | 备注 |
|--------|------|------|------|
| global_session_id | 全局唯一标识（UUID） | 是 | 索引唯一键；文件命名用 platform+session_id：`{session_sourceplatform}_{session_id}_raw.json`、`{session_sourceplatform}_{session_id}_abstract.md` |
| session_id | 对话在原始平台的 ID | 是 | 仅用于参考和平台 API 调用 |
| session_sourceplatform | 对话来源平台 | 是 | 如 deepseek, chatgpt, kimi |
| session_title | 会话标题/摘要 | 是 | 初始可抓取网页标题，后续由总结更新 |
| session_status | 抓取状态 | 是 | pending \| completed \| updating |
| update_num | 更新次数 | 是 | 首次抓取为 0，每次增量更新后 +1 |
| session_abstract | 会话内容摘要 | 是 | 由总结生成，首次抓取后填充 |
| session_tags | 标签 | 是 | 逗号分隔字符串，如 "工作,Python,规划" |
| create_date | 记录创建时间（本地） | 是 | ISO 8601，如 "2024-01-15T10:30:00Z" |
| update_date | 记录最后更新时间（本地） | 是 | 同格式 |
| dateinfo | 对话在平台的原始日期 | 否 | 如 "2024-01-14" |
| last_message_timestamp | 对话最后一条消息的时间戳（平台） | 强烈建议 | 增量更新依据，判断是否有新消息 |
| original_data_url | 原始对话数据的 URL 或引用 | 否 | 某些平台提供永久链接 |

## 状态含义

- **pending**：未抓取，待首次拉取并生成 JSON + MD。
- **updating**：已锁定或标记为需更新，待拉取（含增量）并刷新 JSON + MD。
- **completed**：已抓取并完成总结，索引与文件一致。

## 唯一性

- 同一平台下以 `session_id` 唯一；跨平台用 `global_session_id`（UUID）区分，新增记录时生成并保持不变，便于文件命名与增量更新时复用同一 JSON/MD。
