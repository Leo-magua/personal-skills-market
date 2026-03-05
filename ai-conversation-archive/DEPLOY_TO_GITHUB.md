# 同步到 GitHub（personal skills market 仓库）

## 1. 在 GitHub 上创建仓库

- 仓库名建议：`personal-skills-market` 或 `openclaw-skills`
- 可见性：Private（仅备份）或 Public（若想分享）
- 创建时**不要**勾选 “Add a README file”，保留空仓库

## 2. 本地准备并推送

在终端执行（将 `YOUR_USERNAME` 换成你的 GitHub 用户名）：

```bash
# 新建仓库目录（可与 openclaw 分离，便于单独备份）
mkdir -p ~/personal-skills-market
cd ~/personal-skills-market

# 若尚未 git init
git init

# 复制本 skill 到仓库（若已存在可跳过或覆盖）
cp -r /Users/zhang.longqiang/.openclaw/workspace/skills/ai-conversation-archive .

# 仓库根目录 .gitignore（忽略各 skill 下的本地数据）
cat > .gitignore << 'EOF'
# 各 skill 的 data 目录下的本地数据不提交
**/data/database.json
**/data/action.log
**/data/config.json
**/data/*_list.json
**/data/*_raw.json
**/data/*_abstract.md
**/__pycache__/
*.pyc
EOF

# 可选：仓库根 README
echo "# Personal Skills Market\n\nOpenClaw 等可用的个人技能备份。\n\n- **ai-conversation-archive**：各 AI 平台对话本地归档。" > README.md

# 添加、提交、关联远程、推送
git add .
git commit -m "Add ai-conversation-archive skill"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/personal-skills-market.git
git push -u origin main
```

## 3. 之后更新备份

在仓库目录下：

```bash
cd ~/personal-skills-market
cp -r /Users/zhang.longqiang/.openclaw/workspace/skills/ai-conversation-archive .
git add .
git commit -m "Update ai-conversation-archive"
git push
```

说明：`.gitignore` 已排除 `data/` 下的对话与索引文件，推送的只是技能代码与说明，不会包含你的对话内容。
