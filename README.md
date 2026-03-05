# Personal Skills Market

个人可复用技能汇总，供 [OpenClaw](https://github.com/openclaw/OpenClaw) 等 AI 工作流使用。每个子目录为一个独立 skill，可直接拷贝到本机的 skills 目录使用。

---

## 技能列表

| Skill | 说明 |
|-------|------|
| [ai-conversation-archive](./ai-conversation-archive/) | 将各 AI 平台（DeepSeek、ChatGPT、Kimi 等）的对话记录同步到本地，维护索引并产出原始 JSON 与摘要 MD；支持浏览器抓取与增量更新。 |
| [zhihu-hot-search](./zhihu-hot-search/) | 知乎热榜抓取与展示。 |

*后续可在此继续追加你写的好用 skills。*

---

## 使用方式

1. **克隆本仓库**（或只下载需要的 skill 目录）：
   ```bash
   git clone git@github.com:Leo-magua/personal-skills-market.git
   ```

2. **安装到 OpenClaw**：将需要的 skill 目录拷贝到 OpenClaw 的 skills 目录下，例如：
   ```bash
   cp -r ai-conversation-archive ~/.openclaw/workspace/skills/
   ```

3. 各 skill 的详细用法见其目录内的 `SKILL.md` 或 `README.md`。

---

## 维护说明

- 本仓库仅备份 skill 的**代码与配置结构**，各 skill 的 `data/` 下本地数据（如对话归档、热榜缓存等）已通过 `.gitignore` 排除，不会提交。
- 新增或更新 skill 后，在仓库根目录执行 `git add`、`git commit`、`git push` 即可同步到 GitHub。
