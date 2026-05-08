# bilibili-reader Skill 发布指南

> 本文档说明如何将 bilibili-reader skill 发布到各大 Agent 平台的官方 Skill 市场中。

---

## 一、发布渠道总览

| 平台 | 渠道名称 | 提交方式 | 审核 | 付费支持 |
|------|----------|----------|------|----------|
| Hermes Agent | **HermesHub** | GitHub PR / Web 提交 | 安全扫描 (65+规则) | 支持 (x402 微支付) |
| OpenClaw | **ClawHub** | `clawhub` CLI 提交 | 管理员审核 | 支持 |
| Claude Code | — | 放入 `~/.claude/skills/` | 无 | 不支持 |
| AgentSkills.io | — | 开放标准，无中心化市场 | — | — |

你的 `SKILL.md` 已经完全符合 `agentskills.io` 开放标准，天然兼容所有平台。以下是具体提交流程。

---

## 二、HermesHub（推荐首选）

### 2.1 方式一：通过 GitHub PR 提交（推荐）

**HermesHub 仓库地址：** `https://github.com/amanning3390/hermeshub`

1. **Fork 仓库**
   ```
   在 GitHub 上 fork https://github.com/amanning3390/hermeshub
   ```

2. **在你的 Fork 中创建 skill 目录**
   ```
   skills/bilibili-reader/
   ├── SKILL.md          ← 你的 SKILL.md
   ├── references/       ← 你的 references/ 目录（如果有）
   ├── scripts/          ← 你的 scripts/ 目录（如果有）
   └── assets/          ← 你的 assets/ 目录（如果有）
   ```

3. **调整 SKILL.md 中的路径**
   你的 SKILL.md 中硬编码了 `~/.hermes/skills/media/bilibili-reader`，但 HermesHub 的 skill 会被安装到其他路径。需要改为使用环境变量 `${HERMES_SKILL_DIR}`：

   ```bash
   # 找到所有 hardcoded 路径，替换为 ${HERMES_SKILL_DIR}
   cd ~/.hermes/skills/media/bilibili-reader
   ↓ 改为
   cd ${HERMES_SKILL_DIR}
   ```

   > 注：`${HERMES_SKILL_DIR}` 是 Hermes Agent 内置的环境变量，运行时会被自动替换为 skill 的实际安装路径。

4. **提交 PR**
   - 在你的 Fork 中提交 commit
   - 创建 Pull Request 到 `amanning3390/hermeshub:main`
   - HermesHub 会自动运行安全扫描（65+ 威胁规则）
   - 通过扫描后，管理员审核通过即可上线

### 2.2 方式二：通过 HermesHub 网站提交

1. 访问 **hermeshub.io**（或 Hermes Agent 官网的 Skills Hub 页面）
2. 使用 GitHub OAuth 登录
3. 进入 Creator Dashboard，点击 "Submit Skill"
4. 上传你的 skill 文件（或粘贴 GitHub 仓库 URL）
5. 填写 metadata（名称、描述、分类、标签）
6. 提交后自动进入安全扫描流程

### 2.3 安全扫描注意事项

HermesHub 会检测以下类别的问题：

| 类别 | 说明 |
|------|------|
| 数据泄露 | hardcoded API key、token、密码 |
| 提示词注入 | 可被用户输入劫持的指令 |
| 破坏性命令 | `rm -rf /` 等危险操作 |
| 混淆 | Base64 编码、动态执行的 shell |
| 网络滥用 | 非预期的外部网络请求 |
| 环境滥用 | 未申报的环境变量依赖 |

你的 skill **已通过** 上述检查（无硬编码凭证、无危险命令）。但提交前请再次确认：

- `.env` 文件**不要**提交到 GitHub（已在 `.gitignore` 中）
- `data/` 目录**不要**提交（已在 `.gitignore` 中）
- 所有依赖都在 `requirements.txt` 中声明

### 2.4 发布后安装方式

```bash
hermes skills install github:amanning3390/hermeshub/skills/bilibili-reader
```

---

## 三、ClawHub（OpenClaw 平台）

### 3.1 前置准备

1. **安装 OpenClaw CLI**
   ```bash
   # macOS/Linux
   curl -fsSL https://get.openclaw.ai | sh

   # 或通过 npm
   npm install -g @openclaw/cli
   ```

2. **登录 ClawHub**
   ```bash
   clawhub login
   # 会打开浏览器，用 GitHub OAuth 认证
   ```

### 3.2 发布 Skill

```bash
# 在项目根目录执行
clawhub skill publish bilibili-reader

# 或指定版本
clawhub skill publish bilibili-reader --version 2.0.0
```

ClawHub CLI 会：
1. 读取项目中的 `SKILL.md`
2. 验证格式是否符合 agentskills.io 标准
3. 上传到 ClawHub 平台
4. 返回 skill 的 Slug（用于安装）

### 3.3 发布后安装方式

```bash
# 通过 Slug 安装
clawhub install bilibili-reader

# 或通过 GitHub 安装（和 Hermes 一样）
openclaw skills install mistake-12/bilibili-reader-skill
```

### 3.4 额外元数据建议

你的 `SKILL.md` 中的 `metadata.openclaw` 部分已经配置好了。为了在 ClawHub 中获得更好的展示效果，建议补充以下可选字段：

```yaml
metadata:
  openclaw:
    requires:
      bins:
        - python3
        - uv
      env:
        - BILIBILI_SESSDATA
        - BILIBILI_BILI_JCT
        - BILIBILI_BUVID3
    tags:
      - bilibili
      - video
      - summary
      - pdf
      - chinese
      - bilingual
      - reading
      - favorites
    # 建议补充以下字段
    homepage: https://github.com/mistake-12/bilibili-reader-skill
    repository: https://github.com/mistake-12/bilibili-reader-skill
    license: MIT
```

---

## 四、Claude Code / 其他 Agent

Claude Code 和其他遵循 agentskills.io 标准的 Agent 可以直接使用你的 skill，无需额外发布。

用户只需要：

```bash
# Claude Code
git clone https://github.com/mistake-12/bilibili-reader-skill.git ~/.claude/skills/bilibili-reader

# 其他 Agent（通用）
git clone https://github.com/mistake-12/bilibili-reader-skill.git <agent-skills-dir>/bilibili-reader
```

你的 README.md 已经说明了这些方式。

---

## 五、AgentSkills.io 开放标准

你的 `SKILL.md` 已经完全符合 [agentskills.io 规范](https://agentskills.io/specification)，包括：

- ✅ 标准 YAML frontmatter（`name`, `description`, `version`, `author`, `license`）
- ✅ `prerequisites` 声明（环境变量、命令依赖）
- ✅ `metadata.hermes` 和 `metadata.openclaw` 平台特定配置
- ✅ Progressive disclosure 结构（SKILL.md 为主 + references/ 为辅）
- ✅ 条件激活机制（通过 `When to Use` 描述触发条件）

无需额外修改即可兼容所有 agentskills.io 标准的平台。

---

## 六、发布前检查清单

在提交到 HermesHub / ClawHub 之前，请确认：

### 6.1 文件结构

```
bilibili-reader-skill/
├── SKILL.md                  ✅ 存在，格式正确
├── requirements.txt           ✅ 存在
├── .gitignore                ✅ 存在（排除 .env, data/, __pycache__/ 等）
├── src/                      ✅ 核心代码
├── scripts/                  ✅ 辅助脚本
│   ├── fetch_data.py
│   ├── render_pdf.py
│   └── run_noninteractive.py
├── templates/                 ✅ PDF 模板
├── references/                ✅ API 参考文档（可选）
├── .claude/skills/           ✅ Cursor skill（这个不用发布）
│   └── skills-slides/
├── docs/                     ✅ 开发文档（不用发布）
├── assets/                   ✅ 资源文件
├── .env.example              ✅ 示例配置
└── README.md                  ✅ 项目说明
```

### 6.2 SKILL.md 路径兼容性

**重要**：你的 SKILL.md 中有多处硬编码路径，需要在发布前改为 `${HERMES_SKILL_DIR}`：

```bash
# 需要修改的位置（共 3 处）：

# 第 1 处：Step 1 前置配置
cd ~/.hermes/skills/media/bilibili-reader && python -m src --login
↓ 改为
cd ${HERMES_SKILL_DIR} && python -m src --login

# 第 2 处：Step 2 fetch_data
cd ~/.hermes/skills/media/bilibili-reader && python scripts/fetch_data.py <收藏夹名称> [latest|random|<bvid>]
↓ 改为
cd ${HERMES_SKILL_DIR} && python scripts/fetch_data.py <收藏夹名称> [latest|random|<bvid>]

# 第 3 处：Step 3 render_pdf
cd ~/.hermes/skills/media/bilibili-reader && python scripts/render_pdf.py /tmp/summary.json
↓ 改为
cd ${HERMES_SKILL_DIR} && python scripts/render_pdf.py /tmp/summary.json
```

### 6.3 Pitfalls 中的路径

```bash
# 第 4 处：Pitfalls execute_code
cd ~/.hermes/skills/media/bilibili-reader && .venv/bin/python your_script.py
↓ 改为
cd ${HERMES_SKILL_DIR} && .venv/bin/python your_script.py

# 第 5 处：Pitfalls 沙箱 DNS
cd skill_dir && .venv/bin/python -c "from src.bilibili_api import BilibiliAPI; ..."
↓ 改为
cd ${HERMES_SKILL_DIR} && .venv/bin/python -c "from src.bilibili_api import BilibiliAPI; ..."
```

### 6.4 版本号更新

发布前确认 `SKILL.md` 中的版本号与代码一致：

```yaml
version: 2.0.0  # 与代码库版本保持同步
```

---

## 七、推荐的发布顺序

建议按以下顺序发布，最大化曝光：

```
1. HermesHub（GitHub PR）     — 最权威，用户最信任
   ↓
2. ClawHub（clawhub CLI）      — OpenClaw 用户直接可用
   ↓
3. GitHub + README.md         — 其他 Agent 用户自取
```

---

## 八、常见问题

### Q: HermesHub 和 ClawHub 需要付费吗？

**免费**：两者都免费发布社区 skill。
**付费**：HermesHub 支持设置付费（x402 微支付协议，95% 分成给作者），ClawHub 支持类似机制。如果你希望保持免费，直接发布即可。

### Q: 发布后如何更新版本？

- **HermesHub**：提交新的 commit/PR 到 `hermeshub` 仓库
- **ClawHub**：运行 `clawhub skill publish bilibili-reader --version 2.1.0`

### Q: 如果审核被拒绝怎么办？

HermesHub 的安全扫描是自动化的，如果触发误报（你的 skill 是安全的但被标记），可以在 PR 中留言说明，或联系管理员。如果内容不符合平台规范，会收到具体的拒绝原因。

### Q: 是否需要翻译 SKILL.md 为英文？

不需要。HermesHub 和 ClawHub 都支持多语言 README。你的 `SKILL.md` 是中英双语结构（`tldr_cn` / `tldr_en` 等），这正是它们的推荐做法。

### Q: 我的 SKILL.md 里有 500+ 行，会影响性能吗？

agentskills.io 规范建议 SKILL.md 控制在 500 行 / 5000 tokens 以内。超过的部分应移到 `references/` 目录，使用时按需加载。

你的 SKILL.md 目前约 534 行，已接近上限。内容多的原因是 **Pitfalls** 和 **新增功能模块** 两节较长。建议：

```
SKILL.md          ← 保留核心流程（When to Use / Procedure / Pitfalls 精简版）
references/
  ├── bilibili-api-notes.md    ← API 细节和降级方案（从 SKILL.md 移出）
  ├── genre-prompts.md         ← 10 种体裁的完整提示词
  └── advanced-features.md     ← 新增功能模块的详细说明
```

这样 agent 在需要时再加载详细文档，不会每次都消耗大量 tokens。
