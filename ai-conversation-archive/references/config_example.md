# 配置与列表文件示例

## data/config.json（可选）

本 skill 在 **data/config.json** 中已提供默认 `summary_command`，指向自带的 **scripts/summarize.py**，会从 `*_raw.json` 生成含「## 摘要」「## 标签」的 `*_abstract.md`。如需改用自家总结逻辑，可修改为：

```json
{
  "summary_command": "python /path/to/your/summarize.py --input {input_json} --output {output_md}",
  "platforms": {
    "deepseek": {},
    "kimi": {}
  }
}
```

- **summary_command**：生成摘要的脚本或命令。占位符 `{input_json}`、`{output_md}` 会被替换为实际路径。默认使用 **scripts/summarize.py**（位置：skill 目录下 `scripts/summarize.py`），可直接用或按需修改 data/config.json。
- **platforms**：要同步的平台键名；若为空，脚本会扫描 `data/<platform>_list.json` 自动发现。

## 平台列表文件 data/<platform>_list.json

无 API 时由你或 agent 维护，每行一条会话摘要，供 `sync_index.py` 合并进 database.json。

```json
[
  {
    "session_id": "平台返回的会话ID",
    "title": "会话标题或首条消息摘要",
    "dateinfo": "2024-01-14",
    "last_message_timestamp": "2024-01-15T10:30:00Z",
    "original_data_url": "https://platform.example.com/chat/xxx"
  }
]
```

- **session_id** 必填；**title** 建议填；**last_message_timestamp** 用于增量判断，建议填。
- 执行 `python scripts/sync_index.py` 后，新会话会以 `pending` 写入 database.json，已有会话若时间更新会标为 `updating`。

**旧命名说明**：若你之前已有以 `{global_session_id}.json` / `.md` 命名的文件，脚本现已改为使用 `{platform}_{session_id}_raw.json` 与 `{platform}_{session_id}_abstract.md`。可据 database.json 中的 `session_sourceplatform` 与 `session_id` 将旧文件重命名，或保留旧文件仅作备份，新任务会按新命名读写。
