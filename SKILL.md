---
name: bilibili-reader
description: "B站收藏夹视频智能总结：随机选取收藏视频，阅读字幕/评论/弹幕，生成中英双语总结PDF"
version: 1.0.0
author: mistake-12
license: MIT
prerequisites:
  env_vars:
    - name: BILIBILI_SESSDATA
      prompt: "请输入B站SESSDATA Cookie"
      help: "浏览器F12 → Application → Cookies → bilibili.com → SESSDATA"
      required_for: "B站API认证"
    - name: BILIBILI_BILI_JCT
      prompt: "请输入B站bili_jct Cookie"
      help: "浏览器F12 → Application → Cookies → bilibili.com → bili_jct"
      required_for: "B站API认证"
    - name: BILIBILI_BUVID3
      prompt: "请输入B站buvid3 Cookie"
      help: "浏览器F12 → Application → Cookies → bilibili.com → buvid3"
      required_for: "B站API认证"
  commands:
    - pip install -r requirements.txt
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

## Quick Reference

| 命令 | 说明 |
|------|------|
| `python -m src` | 运行一次完整的视频总结流程（交互式，需输入选择） |
| `python -m src.main` | 同上 |
| `python scripts/run_noninteractive.py <收藏夹名> latest` | 最新收藏的未处理视频（默认） |
| `python scripts/run_noninteractive.py <收藏夹名> random` | 随机选一个未处理视频 |
| `python scripts/run_noninteractive.py <收藏夹名> <bvid>` | 指定BV号 |
| `hermes --toolsets skills -q "用bilibili-reader总结一个视频"` | 通过hermes调用 |

## Procedure

> **API 细节和降级方案**：参见 `references/bilibili-api-notes.md`

### Step 1: 前置配置

首次使用需要配置B站Cookie：

1. 浏览器登录 bilibili.com
2. 按 F12 打开开发者工具
3. 进入 Application → Cookies → bilibili.com
4. 复制以下三个值：
   - `SESSDATA`
   - `bili_jct`
   - `buvid3`
5. 在项目根目录创建 `.env` 文件：
```bash
cp .env.example .env
# 编辑 .env 填入上面三个值
```

6. 安装依赖：
```bash
pip install -r requirements.txt
```

### Step 2: 运行总结

```bash
python -m src
```

### Step 3: 工作流程

程序会自动执行以下步骤：

1. **验证配置** — 检查Cookie是否已配置
2. **获取收藏夹** — 调用B站API获取用户所有收藏夹
3. **选择收藏夹** — 如有多个收藏夹，提示用户选择
4. **选择视频** — 支持三种模式：
   - `latest`（默认）：取收藏时间最近的未处理视频（收藏夹第一个）
   - `random`：从未处理的视频中随机选取
   - `<bvid>`：指定BV号
5. **获取数据** — 并行获取视频详情、字幕、高赞评论、弹幕
6. **字幕概括** — 根据时长选择策略（<30min一次性概括，>=30min分段+重叠）
7. **意图路由** — 用LLM判断视频属于哪种体裁，选择专用提示词
8. **生成总结** — 调用LLM生成结构化总结（含TLDR、要点、洞察）
9. **输出PDF** — 渲染HTML模板并转为PDF（中英分离排版）
10. **记录记忆** — 将视频bvid写入 `data/processed.json`

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

### Step 4: 查看结果

PDF文件输出在 `output/` 目录，文件名格式：
```
20260504_120000_BV1xx411c7mD_视频标题.pdf
```

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
