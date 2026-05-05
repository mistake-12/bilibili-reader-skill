<div align="center">

<img src="https://raw.githubusercontent.com/mistake-12/bilibili-reader-skill/main/assets/logo.svg" width="120" alt="bilibili-reader-skill">

# bilibili-reader-skill

### B站收藏夹视频智能总结

**收藏了不看？让 AI 帮你读。**

自动从 B站收藏夹选取视频，读取字幕、评论、弹幕，生成中英双语结构化学习笔记。

[![AgentSkills](https://img.shields.io/badge/AgentSkills.io-Compatible-blue?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHBhdGggZD0iTTEyIDJMMyA3djEwbDkgNSA5LTVIN0wxMiAyeiIgZmlsbD0iI2ZmZiIvPjwvc3ZnPg==)](https://agentskills.io)
[![Hermes Agent](https://img.shields.io/badge/Hermes_Agent-Supported-green?style=for-the-badge)](https://github.com/NousResearch/hermes-agent)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Supported-orange?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PHRleHQgeD0iNCIgeT0iMTgiIGZvbnQtc2l6ZT0iMTgiPvCfjLU8L3RleHQ+PC9zdmc+)](https://github.com/openclaw/openclaw)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

</div>

---

<div align="center">

<table>
<tr>
<td align="center" width="33%">

### ⚡ 智能体裁路由
自动判断 10 种视频类型，用最合适的提示词生成总结

</td>
<td align="center" width="33%">

### 🗺️ 收藏夹考古
可视化进度追踪 + 成就系统，让"消化收藏"变成游戏

</td>
<td align="center" width="33%">

### 📬 多平台推送
生成 PDF 后自动推送到微信 / 飞书 / Telegram / Discord

</td>
</tr>
<tr>
<td align="center">

### 🔐 扫码登录
浏览器弹窗扫码，无需手动复制 Cookie

</td>
<td align="center">

### 🌏 中英双语
每份总结同时生成中文和英文版本，对照阅读

</td>
<td align="center">

### 🧠 知识积累
记忆系统存储完整总结，支持关键词搜索和体裁过滤

</td>
</tr>
</table>

</div>

---

## 快速开始（30 秒）

> 你只需要告诉你的 Agent 一句话，它会自动完成安装和配置。

### 方式一：通过 Agent 安装（推荐）

**Hermes Agent 用户：**

在终端或聊天窗口中对 Hermes 说：

```
帮我去 https://github.com/mistake-12/bilibili-reader-skill 安装这个 bilibili-reader skill
```

**OpenClaw 用户：**

```
openclaw skills install mistake-12/bilibili-reader-skill
```

Agent 安装完成后，直接用自然语言调用：

```
帮我从B站收藏夹随机总结一个视频
```

Agent 会自动引导你完成 B站登录配置（扫码或手动填 Cookie），然后开始工作。

---

### 方式二：手动安装

如果你想直接在命令行使用（不通过 Agent）：

```bash
# 1. 克隆并安装
git clone https://github.com/mistake-12/bilibili-reader-skill.git
cd bilibili-reader-skill
pip install -r requirements.txt

# 2. 配置 B站账号（会打开浏览器扫码，按提示操作即可）
python -m src --login

# 3. 运行
python -m src
```

`--login` 会启动一个交互式向导：先让你扫码登录 B站获取 Cookie，再选择推送到哪个聊天平台。配置保存在项目根目录的 `.env` 文件中。

---

## 使用示例

### 通过 Agent（最自然的方式）

安装好 skill 后，直接用自然语言和 Agent 对话：

```
你：帮我从收藏夹总结一个视频
Agent：正在获取收藏夹列表...
       随机选中: Python装饰器完全指南 (BV1xx411c7mD)
       正在下载字幕... 获取到 342 条字幕
       正在生成总结...
       PDF已生成: output/20260506_120000_BV1xx411c7mD_Python装饰器完全指南.pdf
       [DELIVERY] 请将以下内容推送到微信...
```

```
你：搜索我之前总结过的关于 Python 的视频
Agent：在已总结记录中找到 3 个匹配:
         [💻 技术教程与实操] Python装饰器完全指南
           TLDR: 装饰器本质是高阶函数的语法糖
         [💻 技术教程与实操] Python异步编程入门
           TLDR: asyncio的核心是事件循环+协程
         ...
```

### 通过命令行

```bash
# 总结收藏夹里最新收藏的视频
python scripts/run_noninteractive.py 代码 latest

# 随机选一个未处理的视频
python scripts/run_noninteractive.py 代码 random

# 搜索已总结的记录
python scripts/run_noninteractive.py 代码 search python

# 查看考古进度
python -m src --progress

# 修改推送平台配置
python -m src --config
```

---

## 工作流程

```
收藏夹选取 → 视频详情 → 字幕 / 评论 / 弹幕
     ↓
  字幕分段概括（长视频自动分段 + 重叠区）
     ↓
  意图路由：判断视频体裁（10 种类型）
     ↓
  体裁专用提示词 → LLM 生成结构化总结
     ↓
  PDF 渲染 + 考古进度更新 + 平台推送
```

---

## 10 种体裁路由

系统自动判断视频类型，使用对应的专用提示词：

| 体裁 | 特征 | 专用字段 |
|:-----|:-----|:---------|
| 💻 技术教程 | 编程/工具/配置 | 工具清单 · 代码片段 · 避坑指南 · 验证步骤 |
| 🎓 学科教育 | 考试/公开课 | 考点 · 考试形式 · 应试技巧 |
| 🗣️ 语言学习 | 外语/语法 | 结构化词汇表 · 语法点 · 发音要点 |
| 🔬 深度解析 | 科普/商业/政经 | 论点-论据链 · 数据来源 · 批判性思考 |
| 🧠 方法论 | 学习/时间管理 | 可执行框架 · 练习模板 · 执行洞察 |
| 💼 职场技能 | 求职/副业 | 话术模板 · 场景SOP · 深层逻辑 |
| 🎨 艺术创造 | 绘画/摄影/音乐 | 技法要点 · 参考作品 · 审美规律 |
| 📖 书籍拆解 | 速读/拆书 | 关键引述 · 核心论点 · 价值评估 |
| 🛠️ 生活技能 | 维修/烹饪 | 材料清单 · 操作步骤 · 验收标准 |
| 📚 通用知识 | 兜底 | 深入浅出 · 相关话题 · 反直觉结论 |

每种体裁还有 4 个通用学习字段：**前置知识** · **难度评级** · **后续行动** · **常见误解**

---

## 收藏夹考古

每次运行后自动展示进度：

```
==================================================
  🗺️  收藏夹考古进度
  📁 收藏夹: 代码
==================================================

  ████████████░░░░░░░░  40%
  已消化 12/30 个视频

  📊 知识图谱:
    💻 技术教程与实操   ███████████████ 8
    🧠 方法论与自我提升 ████████ 4
    📚 通用知识         ████ 2

  🏆 成就:
    🌱 初次发掘 — 消化了第一个视频
    🔍 考古新手 — 消化 5 个视频
    ⛏️ 考古学徒 — 消化 10 个视频
    🔧 技术工匠 — 技术教程类消化 5+ 个
==================================================
```

| 数量 | 成就 | 数量 | 成就 |
|:-----|:-----|:-----|:-----|
| 1 | 🌱 初次发掘 | 50 | 🏛️ 知识守护者 |
| 5 | 🔍 考古新手 | 100 | 👑 收藏夹征服者 |
| 10 | ⛏️ 考古学徒 | 5+ 体裁 | 🌈 博览群书 |
| 25 | 🗺️ 地图绘制者 | 8+ 体裁 | 🎯 全能选手 |

---

## 配置

Agent 安装后会自动引导配置。如需手动修改，编辑项目根目录的 `.env` 文件：

```env
# B站Cookie（Agent 安装时自动获取）
BILIBILI_SESSDATA=xxx
BILIBILI_BILI_JCT=xxx
BILIBILI_BUVID3=xxx

# 推送平台（可选，不设则不推送）
DELIVERY_PLATFORM=wechat  # wechat / feishu / telegram / discord / slack / whatsapp / none
```

也可以运行配置向导重新设置：

```bash
python -m src --config
```

---

## 项目结构

```
bilibili-reader-skill/
├── src/
│   ├── auth.py            # 扫码登录
│   ├── bilibili_api.py    # B站API封装
│   ├── config.py          # 配置管理
│   ├── intent_router.py   # 10种体裁提示词
│   ├── main.py            # 交互式主入口
│   ├── memory.py          # 长期记忆系统
│   ├── pdf_generator.py   # PDF生成
│   ├── progress.py        # 考古进度可视化
│   ├── setup.py           # 配置向导
│   └── summarizer.py      # LLM总结核心
├── scripts/
│   └── run_noninteractive.py  # 非交互入口
├── templates/
│   └── summary.html       # PDF模板
├── SKILL.md               # AgentSkills 入口文件
├── .env.example           # 配置模板
└── requirements.txt
```

---

## Agent 兼容性

<div align="center">

| Agent | 安装方式 |
|:------|:---------|
| [Hermes Agent](https://github.com/NousResearch/hermes-agent) | 对 Hermes 说：`安装 https://github.com/mistake-12/bilibili-reader-skill` |
| [OpenClaw](https://github.com/openclaw/openclaw) | `openclaw skills install mistake-12/bilibili-reader-skill` |
| [Claude Code](https://claude.ai/code) | `git clone` 到 `~/.claude/skills/` 目录 |
| 其他 Agent | 遵循 [AgentSkills.io](https://agentskills.io) 标准，直接放入 skills 目录 |

</div>

---

<div align="center">

**收藏了不看？让它变成知识。**

[![GitHub stars](https://img.shields.io/github/stars/mistake-12/bilibili-reader-skill?style=social)](https://github.com/mistake-12/bilibili-reader-skill/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/mistake-12/bilibili-reader-skill?style=social)](https://github.com/mistake-12/bilibili-reader-skill/issues)

Made with ❤️ for B站重度用户

</div>
