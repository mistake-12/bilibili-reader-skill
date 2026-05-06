---
name: bilibili-reader
description: "B站收藏夹视频智能总结：随机选取收藏视频，阅读字幕/评论/弹幕，生成中英双语总结PDF"
version: 1.0.0
author: mistake-12
license: MIT
prerequisites:
  env_vars:
    - name: BILIBILI_SESSDATA
      prompt: "B站SESSDATA（运行 python -m src --login 自动获取）"
      help: "运行 python -m src --login，浏览器会自动打开B站，扫码后自动提取"
      required_for: "B站API认证"
    - name: BILIBILI_BILI_JCT
      prompt: "B站bili_jct（运行 python -m src --login 自动获取）"
      help: "运行 python -m src --login，浏览器会自动打开B站，扫码后自动提取"
      required_for: "B站API认证"
    - name: BILIBILI_BUVID3
      prompt: "B站buvid3（运行 python -m src --login 自动获取）"
      help: "运行 python -m src --login，浏览器会自动打开B站，扫码后自动提取"
      required_for: "B站API认证"
  commands:
    - pip install -r requirements.txt
    - playwright install chromium
metadata:
  hermes:
    tags:
      - bilibili
      - video
      - summary
      - pdf
      - chinese
      - bilingual
      - reading
      - favorites
    related_skills: []
  openclaw:
    requires:
      bins:
        - python3
        - pip
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
---

# bilibili-reader — B站收藏夹视频智能总结

定期从B站收藏夹中随机选取视频，自动阅读字幕、高赞评论和弹幕，生成结构清晰的中英双语总结PDF。解决"收藏了但不看"的痛点。

## When to Use

当用户说以下内容时触发此skill：
- "总结一个B站视频"
- "从收藏夹随机选个视频看看"
- "帮我看看收藏了什么"
- "今天推送一个视频总结"
- "bilibili reader"
- "扫码登录B站"
- "看看我的考古进度"
- "搜索我总结过的视频"

## Quick Reference

| 命令 | 说明 |
|------|------|
| `python -m src` | 运行一次完整的视频总结流程（交互式，需输入选择） |
| `python -m src --login` | 首次配置向导（扫码登录 + 推送平台设置） |
| `python -m src --config` | 修改配置（推送平台/推送目标，不动Cookie） |
| `python -m src --progress` | 查看收藏夹考古进度 |
| `python scripts/run_noninteractive.py <收藏夹名> latest` | 最新收藏的未处理视频（默认） |
| `python scripts/run_noninteractive.py <收藏夹名> random` | 随机选一个未处理视频 |
| `python scripts/run_noninteractive.py <收藏夹名> search <关键词>` | 搜索已总结记录和未处理视频 |
| `python scripts/run_noninteractive.py <收藏夹名> <bvid>` | 指定BV号 |
| `hermes --toolsets skills -q "用bilibili-reader总结一个视频"` | 通过hermes调用 |

## Procedure

> **API 细节和降级方案**：参见 `references/bilibili-api-notes.md`

### Step 1: 前置配置

**Agent 行为规则：** 当检测到 `.env` 中缺少 B站Cookie 时，必须执行以下命令来配置：

```bash
cd ~/.hermes/skills/media/bilibili-reader && python -m src --login
```

此命令会自动完成：
1. 打开 Chromium 浏览器，访问 bilibili.com
2. 如果未登录 → 用户用B站APP扫码登录
3. 如果已登录 → 程序自动提取 Cookie
4. Cookie 自动保存到 `.env` 文件

**首次安装还需要运行：**
```bash
pip install -r requirements.txt
playwright install chromium
```

**重要：不要引导用户手动从浏览器 F12 复制 Cookie。** 使用 `python -m src --login` 自动获取。

### Step 2: Agent 三步工作流（核心）

**Agent 行为规则：** 当用户要求总结视频时，严格按以下三步执行：

**第一步：获取视频数据**

```bash
cd ~/.hermes/skills/media/bilibili-reader && python scripts/fetch_data.py <收藏夹名称> [latest|random|<bvid>]
```

这会输出一个 JSON，包含：`bvid`、`title`、`desc`、`owner`、`duration`、`subtitles`、`comments`、`danmakus`。

**第二步：Agent 生成总结（用你自己的 LLM）**

读取第一步的 JSON 输出，根据视频标题、简介、字幕内容判断体裁（见下方 10 种体裁表），然后用对应的提示词模板生成结构化总结。

字幕处理规则：
- 字幕少于 500 条 → 直接概括
- 字幕 500-2000 条 → 分段概括（每段约 500 条），合并后再总结
- 字幕超过 2000 条 → 取前 1000 条 + 后 500 条概括

**第三步：渲染 PDF**

把第二步生成的总结 JSON 写入临时文件，然后调用渲染脚本：

```bash
cd ~/.hermes/skills/media/bilibili-reader && python scripts/render_pdf.py /tmp/summary.json
```

脚本会输出 PDF 文件路径。将路径告诉用户，并附上一句话 TLDR。

> **收藏时间排序说明**：API按收藏时间倒序返回视频，第一个即为最新收藏的视频。

### 意图路由（Intent Routing）

系统会自动判断视频体裁，使用对应的专用提示词生成总结：

| 编号 | 体裁 | 触发特征 |
|------|------|----------|
| 1 | 💻 技术教程与实操 | 软件使用/编程教学/工具配置/开发实战 |
| 2 | 🎓 学科与考试教育 | 考研/四六级/公考/高校公开课/K12 |
| 3 | 🗣️ 语言学习 | 外语听说读写/语法/语料跟读 |
| 4 | 🔬 硬核科普与深度解析 | 科技前沿/商业财经/政经地缘 |
| 5 | 🧠 方法论与自我提升 | 学习方法/时间管理/心理学 |
| 6 | 💼 茁场与商业技能 | 求职/茁场生存/副业搞钱 |
| 7 | 🎨 艺术创造与设计美学 | 绘画/摄影/音乐/写作 |
| 8 | 📖 书籍拆解与文献综述 | 速读/拆书/论文解读 |
| 9 | 🛠️ 生活技能与日常经验 | 家居维修/烹饪/生活防坑 |
| 10 | 📚 通用知识 | 不属于以上任何类型（fallback） |

每种体裁的提示词会强调不同的输出结构：
- 技术教程 → 工具清单(含门槛)、保姆级SOP、代码/提示词原文提取、避坑指南、原理解析
- 学科类 → 考点、公式、应试技巧
- 语言类 → 词汇、语法点、练习建议
- 科普类 → 论点-论据链条、批判性思考
- 方法论 → 可执行框架、行动步骤
- 茁场类 → 话术模板、场景SOP
- 创意类 → 技法要点、工具参数、审美规律
- 书籍类 → 核心论点、知识框架
- 生活类 → 材料清单、操作步骤、验收标准
- 通用 → 深入浅出讲明白内容

### 总结 JSON 输出格式

Agent 在第二步生成总结时，必须输出以下 JSON 格式（写入 `/tmp/summary.json`）：

```json
{
  "bvid": "视频BV号（从fetch_data输出中获取）",
  "title_cn": "中文标题",
  "title_en": "English title",
  "owner": "UP主名称",
  "duration_str": "时长格式化 如 23:45",
  "view_count": 12345,
  "like_count": 678,
  "genre": "体裁显示名 如 💻 技术教程与实操",
  "tldr_cn": "一句话中文总结（50字内）",
  "tldr_en": "One-sentence TL;DR (under 50 words)",
  "summary_cn": "中文摘要 300-500字，讲明白具体做了什么、核心结论",
  "summary_en": "English summary 200-400 words",
  "key_points_cn": ["要点1", "要点2", "要点3", "要点4", "要点5"],
  "key_points_en": ["Point 1", "Point 2", "Point 3", "Point 4", "Point 5"],
  "prerequisites_cn": "前置知识",
  "prerequisites_en": "Prerequisites",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty level + why",
  "next_steps_cn": "看完后应该做什么，2-3个具体行动",
  "next_steps_en": "2-3 specific follow-up actions",
  "key_misconceptions_cn": "常见误解及纠正",
  "key_misconceptions_en": "Common misconceptions",
  "insights_cn": "深层洞察 100-200字",
  "insights_en": "Deep insights 100-200 words",
  "top_comments": [{"user": "用户名", "content_cn": "评论内容", "likes": 123}],
  "recommendation_cn": "推荐理由 50-100字",
  "recommendation_en": "Recommendation 50-100 words"
}
```

**体裁专用字段（按体裁选填）：**

| 体裁 | 额外字段 |
|------|---------|
| 技术教程 | `tool_stack`: [{name, purpose, barrier}], `code_snippets`: [{lang, code, context}], `pitfalls_cn/en`, `expected_outcome_cn/en` |
| 学科教育 | `exam_format_cn/en` |
| 语言学习 | `vocabulary_list`: [{word, meaning, example}] |
| 深度解析 | `data_sources_cn/en` |
| 方法论 | `practice_template_cn/en` |
| 职场技能 | `scripts_templates`: [{scenario, script}] |
| 艺术创造 | `reference_works_cn/en` |
| 书籍拆解 | `key_quotes`: [{quote, context}] |
| 生活技能 | `materials_list`: [{item, purpose, cost_estimate}] |
| 通用知识 | `related_topics_cn/en` |

### 体裁判断规则

根据视频标题、简介、字幕前 500 条内容判断：

1. **技术教程** — 标题/内容含：编程语言名、框架名、工具名、"教程"/"入门"/"实战"/"配置"/"搭建"
2. **学科教育** — 标题/内容含：考研/四六级/公考/大学/课程/考试/知识点/公式
3. **语言学习** — 标题/内容含：英语/日语/语法/单词/口语/听力/TOEFL/IELTS
4. **深度解析** — 标题/内容含：分析/解读/深度/揭秘/原理/背后的逻辑/数据
5. **方法论** — 标题/内容含：方法/技巧/提升/效率/习惯/思维/框架/自律
6. **职场技能** — 标题/内容含：求职/面试/简历/副业/赚钱/职场/晋升/薪资
7. **艺术创造** — 标题/内容含：绘画/摄影/设计/音乐/写作/PS/Pr/Blender
8. **书籍拆解** — 标题/内容含：书名号、读书/拆书/书评/笔记/读后感
9. **生活技能** — 标题/内容含：教程/DIY/做菜/维修/收纳/清洁/健康

不匹配任何类型 → 用通用模板。

### Step 4: 查看结果

PDF文件输出在 `output/` 目录，文件名格式：
```
20260504_120000_BV1xx411c7mD_视频标题.pdf
```

### Step 5: 推送到聊天平台（可选）

在 `.env` 中配置 `DELIVERY_PLATFORM` 后，程序会输出 `[DELIVERY]` 标记的推送指令。

**Agent 行为规则：** 当你看到输出中包含 `[DELIVERY]` 标记时，请执行以下操作：

1. 读取 `[DELIVERY]` 指令中的平台、目标、文件路径和消息内容
2. 使用你内置的消息投递能力，将 PDF 文件发送到对应平台
3. 附带一句话 TLDR 摘要作为消息正文

支持的平台：`wechat`（微信）/ `feishu`（飞书）/ `telegram` / `discord` / `slack` / `whatsapp`

配置方式：
```bash
# 方式一：配置向导（推荐）
python -m src --config

# 方式二：手动编辑 .env
DELIVERY_PLATFORM=wechat
```

推送目标由 agent 默认对话决定，不需要额外配置。如果不配置或设为 `none`，则只在本地生成 PDF，不推送。

## Pitfalls

### execute_code 工具无法使用 venv 包
- **症状**：`execute_code` 内调用 weasyprint 等 venv 包时 ModuleNotFoundError
- **原因**：`execute_code` 使用系统 Python，不是 skill 的 .venv
- **解决**：用 `terminal` 工具执行，显式指定 venv Python 路径：
  ```bash
  cd ~/.hermes/skills/media/bilibili-reader && .venv/bin/python your_script.py
  ```

### 非交互环境下 main.py 不可用
- **症状**：`select_folder()` 中的 `input()` 阻塞或 EOFError
- **原因**：main.py 使用交互式 input() 选择收藏夹
- **解决**：不调用 `python -m src`，而是编写自定义脚本直接调用 BilibiliAPI：
  1. 用 `api.get_favorites_list()` 获取列表
  2. 按名称匹配目标收藏夹（如 `f.title == '代码'`）
  3. 调用 `api.get_videos_from_folder()` + `random.choice()` 选视频
  4. 调用 `summarizer.generate_summary()` + `pdf_generator.generate_pdf()`
  5. 将 venv Python 路径写在脚本开头，用 `terminal` 执行

### 没有字幕时的降级策略
- **症状**：`video.subtitle_url` 为空，总结质量受限
- **处理**：基于视频简介（`video.desc`）和评论手动构建 summary JSON，然后直接调用 `pdf_generator.generate_pdf()` 渲染 PDF。总结质量取决于简介的详细程度。

### 收藏夹API返回-400
- **症状**：`/x/v3/fav/folder/created/list-all` 返回 `{"code":-400,"message":"请求错误"}`
- **原因**：`up_mid` 参数不能为0，必须传入真实UID
- **解决**：先调用 `/x/web-interface/nav` 获取当前登录用户的 `mid`，再用该 `mid` 请求收藏夹列表：
  ```python
  r = requests.get('https://api.bilibili.com/x/web-interface/nav', cookies=cookies, headers=headers)
  mid = r.json()['data']['mid']
  # 然后用 mid 请求收藏夹
  r2 = requests.get('https://api.bilibili.com/x/v3/fav/folder/created/list-all', params={'up_mid': mid}, ...)
  ```

### protobuf导入方式
- **症状**：`import protobuf` 报 ModuleNotFoundError
- **解决**：protobuf 包的导入路径是 `from google.protobuf import ...`，不是 `import protobuf`

### Cookie过期
- **症状**：API返回 code=-101 或 "请先登录"
- **解决**：重新从浏览器获取Cookie并更新 `.env`

### 没有字幕
- **症状**：提示"该视频没有字幕"
- **处理**：程序会根据标题、简介和评论生成总结，内容会较简略
- **字幕获取策略**：代码会依次尝试两个API接口获取字幕：
  1. `/x/web-interface/view` — 获取AI生成的CC字幕
  2. `/x/player/wbi/v2` — 获取UP主上传的字幕（作为fallback）
  - 优先选择中文字幕，没有中文则取第一个可用字幕
  - 如果两个接口都没有字幕，说明该视频确实没有可用字幕

### 长视频处理策略
根据视频时长自动选择字幕处理方式，避免token溢出和内容丢失：

| 时长 | 策略 |
|------|------|
| < 30分钟 | 字幕概括后直接总结（不送完整原文） |
| 30-60分钟 | 分段+重叠区（每段10分钟，重叠60秒），每段概括后合并总结 |
| > 60分钟 | 同上，但先警告处理时间较长 |

- **重叠区作用**：防止一句话被生硬劈成两半导致上下文断裂
- **分段概括**：每段独立提炼关键信息，保留技术术语和操作步骤
- **合并总结**：所有段的概括合并后再做最终结构化总结

### 弹幕解析失败
- **症状**：弹幕数量为0
- **处理**：不影响主流程，字幕和评论仍可正常获取

### 收藏夹为空
- **症状**：提示"收藏夹中没有视频"
- **解决**：选择其他收藏夹，或先收藏一些视频

### 沙箱环境DNS不通，curl可以
- **症状**：Python requests 报 `Name or service not known` 或 `ConnectionError`，但 `curl` 同样的URL能通
- **原因**：Python 的 `socket.getaddrinfo()` DNS 解析器在沙箱中被限制，而 curl 用独立的 DNS 解析器（c-ares/libcurl）
- **解决**：`bilibili_api.py` 的 `_get()` 方法已内置 curl fallback——requests 失败时自动切换到 subprocess+curl
- **验证**：`cd skill_dir && .venv/bin/python -c "from src.bilibili_api import BilibiliAPI; ..."` 如果走 curl 路径会正常返回

### weasyprint安装问题
- **症状**：ImportError或字体渲染异常
- **解决**：
  - Windows: `pip install weasyprint` 会自动安装GTK依赖
  - 如有问题，参考 https://doc.courtbouillon.org/weasyprint/stable/first_steps.html

## Verification

验证skill正常工作：

1. **配置验证**：运行后不应提示"缺少配置项"
2. **API验证**：应能成功获取收藏夹列表
3. **数据验证**：应能获取视频详情和评论
4. **输出验证**：`output/` 目录应生成PDF文件
5. **记忆验证**：再次运行应跳过已处理的视频

测试命令：
```bash
hermes --toolsets skills -q "用bilibili-reader从收藏夹随机总结一个视频"
```
