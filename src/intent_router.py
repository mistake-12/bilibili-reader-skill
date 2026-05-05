"""意图路由 — 视频体裁分类 + 专用提示词

流程：
1. 用标题+简介+前1000字字幕判断视频属于哪种体裁
2. 选择对应的专用提示词模板
3. 不匹配任何类型时使用通用 fallback
"""

from enum import Enum


class VideoGenre(str, Enum):
    TECH_TUTORIAL = "tech_tutorial" # 💻 技术教程与实操
    ACADEMIC = "academic"           # 🎓 学科与考试教育
    LANGUAGE = "language"           # 🗣️ 语言学习
    DEEP_DIVE = "deep_dive"         # 🔬 硬核科普与深度解析
    METHODOLOGY = "methodology"     # 🧠 方法论与自我提升
    CAREER = "career"               # 💼 茁场与商业技能
    CREATIVE = "creative"           # 🎨 艺术创造与设计美学
    BOOK = "book"                   # 📖 书籍拆解与文献综述
    LIFE_SKILL = "life_skill"       # 🛠️ 生活技能与日常经验
    GENERIC = "generic"             # 通用 fallback


GENRE_DISPLAY = {
    VideoGenre.TECH_TUTORIAL: "💻 技术教程与实操",
    VideoGenre.ACADEMIC: "🎓 学科与考试教育",
    VideoGenre.LANGUAGE: "🗣️ 语言学习",
    VideoGenre.DEEP_DIVE: "🔬 硬核科普与深度解析",
    VideoGenre.METHODOLOGY: "🧠 方法论与自我提升",
    VideoGenre.CAREER: "💼 茁场与商业技能",
    VideoGenre.CREATIVE: "🎨 艺术创造与设计美学",
    VideoGenre.BOOK: "📖 书籍拆解与文献综述",
    VideoGenre.LIFE_SKILL: "🛠️ 生活技能与日常经验",
    VideoGenre.GENERIC: "📚 通用知识",
}


# ──────────────────────────────────────────────
# 路由分类提示词
# ──────────────────────────────────────────────

ROUTER_PROMPT = """请判断以下B站视频属于哪种体裁，只回复对应的编号（1-10）。

体裁列表：
1. 技术教程与实操 — 软件使用/编程教学/工具配置/开发实战，有具体操作步骤、代码、命令
2. 学科与考试教育 — 考研/四六级/公考/高校公开课/K12教育，板书多、逻辑严密
3. 语言学习 — 外语听说读写、语法讲解、语料跟读、双语字幕
4. 硬核科普与深度解析 — 科技前沿/商业财经/政经地缘，信息密度大、数据图表多
5. 方法论与自我提升 — 学习方法/时间管理/个人心理学，概念抽象但落脚行为改变
6. 茁场与商业技能 — 求职辅导/茁场生存/副业搞钱，实用主义、话术多
7. 艺术创造与设计美学 — 绘画/摄影/音乐/写作，视觉听觉主导
8. 书籍拆解与文献综述 — 速读/拆书/论文解读，二次压缩、论点-论据结构
9. 生活技能与日常经验 — 家居维修/烹饪健康/生活防坑，强步骤性
10. 其他（不属于以上任何类型）

视频标题: {title}
视频简介: {desc}
字幕片段: {subtitle_sample}

只回复数字（1-10），不要解释。"""


def classify_genre(title: str, desc: str, subtitle_sample: str, llm_caller=None) -> VideoGenre:
    """用LLM判断视频体裁"""
    if not llm_caller:
        return VideoGenre.GENERIC

    prompt = ROUTER_PROMPT.format(
        title=title,
        desc=desc[:300],
        subtitle_sample=subtitle_sample[:1000],
    )

    try:
        response = llm_caller(prompt).strip()
        # 提取数字
        num = ""
        for ch in response:
            if ch.isdigit():
                num += ch
                break
        genre_map = {
            "1": VideoGenre.TECH_TUTORIAL,
            "2": VideoGenre.ACADEMIC,
            "3": VideoGenre.LANGUAGE,
            "4": VideoGenre.DEEP_DIVE,
            "5": VideoGenre.METHODOLOGY,
            "6": VideoGenre.CAREER,
            "7": VideoGenre.CREATIVE,
            "8": VideoGenre.BOOK,
            "9": VideoGenre.LIFE_SKILL,
            "10": VideoGenre.GENERIC,
        }
        return genre_map.get(num, VideoGenre.GENERIC)
    except Exception:
        return VideoGenre.GENERIC


# ──────────────────────────────────────────────
# 通用 fallback 提示词
# ──────────────────────────────────────────────

GENERIC_PROMPT = """# Role: 通用知识拆解专家
你擅长从各类视频中提取核心价值，用深入浅出的方式让读者真正理解视频内容。
你的总结不是"视频简介"，而是一份能让读者不看视频也能获得同等价值的"知识笔记"。

# 核心原则：
- 拒绝泛泛而谈，必须有具体细节
- 用类比和具体例子解释抽象概念
- 提取视频中的关键数据、案例、结论
- 如果有操作步骤，必须拆解为可执行的1-2-3

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}
[弹幕精选]: {danmakus}

请严格按照以下JSON格式输出，不要输出其他内容：
```json
{{
  "title_cn": "中文标题（可对原标题做简化或意译）",
  "title_en": "English title (translate or adapt)",
  "tldr_cn": "一句话总结：这个视频讲了什么，有什么价值（50字以内）",
  "tldr_en": "One-sentence TL;DR (under 50 words)",
  "summary_cn": "中文内容摘要，300-500字，要讲明白具体干了什么、核心结论是什么",
  "summary_en": "English summary, 200-400 words, covering what was done and key conclusions",
  "key_points_cn": ["核心要点1（具体，不要空话）", "要点2", "要点3", "要点4", "要点5"],
  "key_points_en": ["Key point 1 (specific, not generic)", "Point 2", "Point 3", "Point 4", "Point 5"],
  "prerequisites_cn": "学习本内容需要什么前置知识/基础？（具体列出）",
  "prerequisites_en": "What prerequisites/foundations are needed? (list specifically)",
  "difficulty_cn": "难度评级：入门/进阶/高级 + 一句话解释为什么",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + one sentence why",
  "next_steps_cn": "看完之后应该做什么？给出2-3个具体的后续行动建议",
  "next_steps_en": "What to do after watching? 2-3 specific follow-up actions",
  "key_misconceptions_cn": "关于这个话题最常见的误解是什么？怎么纠正？",
  "key_misconceptions_en": "Most common misconceptions about this topic? How to correct them?",
  "related_topics_cn": "2-3个读者可能感兴趣的相关话题，简述关联",
  "related_topics_en": "2-3 related topics the reader might explore, with brief connection",
  "insights_cn": "深层思考：这个内容背后的核心逻辑是什么？和读者已知知识的连接点在哪？有什么反直觉的结论？100-200字",
  "insights_en": "Deep thinking: core logic? Connection to reader's existing knowledge? Counterintuitive conclusions? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "推荐理由+适合什么人看，50-100字",
  "recommendation_en": "Who should watch this and why, 50-100 words"
}}
```"""


# ──────────────────────────────────────────────
# 9种体裁专用提示词
# ──────────────────────────────────────────────

TECH_TUTORIAL_PROMPT = """# Role: 高级技术助教 / 知识拆解专家
你是一个极其擅长从冗长的技术教程、干货视频中提取核心价值的助教。你的任务是将B站视频的字幕、简介和评论，重构成一份**结构化、可直接照做**的「实战学习笔记」。

# Constraints:
- 拒绝空话套话，拒绝写成"视频简介"
- 必须具有极强的"实操性"，读者看完这篇笔记，不看视频也能跟着操作
- 提取字幕中提到的任何命令、代码、特定提示词(Prompt)，必须原文保留并用Markdown代码块包裹
- 如果视频不是技术教程，而是纯理论知识，则重点拆解逻辑思维导图

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}
[弹幕精选]: {danmakus}

请严格按照以下JSON格式输出，不要输出其他内容：
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "一句话总结：这个视频能帮读者解决什么痛点，学会什么技能（50字内）",
  "tldr_en": "TL;DR: what pain point does this solve, what skill will you learn",
  "summary_cn": "核心概述：这个视频具体做了什么、用了什么工具、达到了什么效果（300-500字）",
  "summary_en": "Overview: what was done, what tools were used, what results were achieved (200-400 words)",
  "key_points_cn": ["步骤1：xxx（具体操作）", "步骤2：xxx", "步骤3：xxx", "关键配置：xxx", "效果对比：xxx"],
  "key_points_en": ["Step 1: xxx (specific action)", "Step 2: xxx", ...],
  "prerequisites_cn": "操作前需要准备什么？（系统环境/已安装软件/账号/前置知识）",
  "prerequisites_en": "What to prepare before starting? (OS/tools/accounts/prior knowledge)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "跟着做完之后，下一步应该学什么/做什么？2-3个建议",
  "next_steps_en": "After completing this, what next? 2-3 suggestions",
  "key_misconceptions_cn": "新手最容易踩的坑或理解错的地方",
  "key_misconceptions_en": "Most common beginner mistakes or misunderstandings",
  "expected_outcome_cn": "跟着做完后应该看到什么结果？怎么验证做对了？",
  "expected_outcome_en": "What result should you see? How to verify it worked?",
  "tool_stack": [
    {{"name": "工具名", "purpose": "核心作用", "barrier": "使用门槛（如：需翻墙/需付费/需API Key）"}}
  ],
  "code_snippets": [
    {{"lang": "bash/python/prompt", "code": "提取的具体代码或提示词原文", "context": "这段代码在什么步骤使用"}}
  ],
  "pitfalls_cn": ["避坑1：xxx（来源：字幕/评论区）", "避坑2：xxx"],
  "pitfalls_en": ["Pitfall 1: xxx (source: subtitle/comments)", ...],
  "insights_cn": "原理解析：剥离操作表象，讲明白背后的底层逻辑。为什么这套工具组合能行？运行机制是什么？100-200字",
  "insights_en": "Underlying principles: why does this toolchain work? What's the mechanism? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么水平的人？建议的实践方式？",
  "recommendation_en": "What skill level? Suggested practice approach?"
}}
```"""


ACADEMIC_PROMPT = """# Role: 学科教育助教 / 考试辅导专家
你是一个擅长将高校课程、考试辅导视频转化为系统化学习笔记的助教。
你的总结要让学生不看视频也能理清知识框架、记住核心考点。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "一句话总结这节课/这个视频覆盖了哪些考点（50字内）",
  "tldr_en": "TL;DR in one sentence",
  "summary_cn": "知识框架概述：本讲涵盖的核心知识点、逻辑链条、公式/定理（300-500字）",
  "summary_en": "Knowledge framework overview (200-400 words)",
  "key_points_cn": ["考点1：具体知识点+公式/定义", "考点2", "考点3", ...],
  "key_points_en": ["Point 1: specific knowledge + formula/definition", ...],
  "prerequisites_cn": "学习本课需要什么前置知识？（先修课程/章节/基础概念）",
  "prerequisites_en": "What prerequisite knowledge is needed? (prior courses/chapters/concepts)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "学完后应该做什么？（做题/看下一章/复习方法）",
  "next_steps_en": "What to do after learning this? (practice/next chapter/review method)",
  "key_misconceptions_cn": "关于这些知识点最常见的误解或易混淆概念",
  "key_misconceptions_en": "Most common misconceptions or easily confused concepts",
  "exam_format_cn": "这些知识点在考试中通常怎么考？（选择/填空/计算/证明，分值占比）",
  "exam_format_en": "How are these tested in exams? (format, typical weight)",
  "insights_cn": "应试技巧：这些知识点在考试中怎么出题？常见的坑在哪里？100-200字",
  "insights_en": "Exam tips: how are these tested? Common pitfalls? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么阶段的学生？建议搭配什么资料？",
  "recommendation_en": "Who should watch? What resources to pair with?"
}}
```"""


LANGUAGE_PROMPT = """# Role: 语言学习教练
你是一个擅长将语言教学视频转化为可执行学习计划的教练。
你的总结要包含具体的词汇、短语、语法点，以及练习建议。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "这节课教了什么语言技能/知识点（50字内）",
  "tldr_en": "TL;DR: what language skill/knowledge point is taught",
  "summary_cn": "教学内容概述：本课覆盖的语法点、词汇主题、发音技巧等（300-500字）",
  "summary_en": "Teaching content overview (200-400 words)",
  "key_points_cn": ["核心语法点/句型：xxx", "重点词汇/短语：xxx", "发音要点：xxx", ...],
  "key_points_en": ["Grammar pattern: xxx", "Key vocabulary: xxx", ...],
  "prerequisites_cn": "学习本课需要什么语言基础？（词汇量/语法水平/CEFR等级）",
  "prerequisites_en": "What language level is needed? (vocabulary/grammar/CEFR level)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "学完后应该怎么练习？（跟读/造句/找语伴/看原声视频）",
  "next_steps_en": "How to practice after learning? (shadowing/sentence building/language partner)",
  "key_misconceptions_cn": "中文母语者最容易犯的典型错误",
  "key_misconceptions_en": "Most common errors for Chinese speakers",
  "vocabulary_list": [
    {"word": "单词/短语", "meaning": "中文释义", "example": "例句（原文+翻译）"},
    ...
  ],
  "insights_cn": "语言习得洞察：这个语法/词汇在真实语境中怎么用？和中文思维的差异在哪？容易犯的典型错误是什么？100-200字",
  "insights_en": "Study tips: most efficient practice method? Common confusions? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么水平的学习者？建议的学习路径？",
  "recommendation_en": "What level? Suggested learning path?"
}}
```"""


DEEP_DIVE_PROMPT = """# Role: 深度内容分析师
你是一个擅长将硬核科普、商业分析、政经解读视频转化为结构化分析报告的分析师。
你的总结要帮读者理清复杂信息的逻辑链条，抓住核心论点和论据。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}
[弹幕精选]: {danmakus}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "核心结论是什么？一句话概括（50字内）",
  "tldr_en": "Core conclusion in one sentence",
  "summary_cn": "分析概述：事件/现象背景 → 核心论点 → 支撑论据 → 结论推演（300-500字）",
  "summary_en": "Analysis overview: background → thesis → evidence → conclusion (200-400 words)",
  "key_points_cn": ["论点1：xxx（论据：xxx）", "论点2：xxx（论据：xxx）", ...],
  "key_points_en": ["Thesis 1: xxx (Evidence: xxx)", ...],
  "prerequisites_cn": "理解本内容需要什么背景知识？（领域基础/时事背景/专业术语）",
  "prerequisites_en": "What background knowledge is needed? (domain basics/current events/jargon)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "看完后应该怎么做？（深入了解某个子话题/关注后续发展/验证信息源）",
  "next_steps_en": "What to do after watching? (dive deeper into subtopic/follow up/verify sources)",
  "key_misconceptions_cn": "关于这个话题最常见的误解或片面认知",
  "key_misconceptions_en": "Most common misconceptions or one-sided views on this topic",
  "data_sources_cn": "视频中引用了哪些关键数据、报告、研究或信息来源？",
  "data_sources_en": "What key data, reports, studies, or sources were cited?",
  "insights_cn": "批判性思考：UP主的逻辑有没有漏洞？有哪些被忽略的角度？信息来源是否可靠？100-200字",
  "insights_en": "Critical thinking: any logical gaps? What angles were overlooked? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合对什么话题感兴趣的人？延伸阅读建议？",
  "recommendation_en": "Who should watch? Extended reading suggestions?"
}}
```"""


METHODOLOGY_PROMPT = """# Role: 个人成长教练
你是一个擅长将方法论、自我提升视频转化为可执行行动方案的教练。
你的总结不是复述概念，而是帮读者建立一套可以立刻开始用的框架。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "这个方法/框架能解决什么问题？（50字内）",
  "tldr_en": "What problem does this solve?",
  "summary_cn": "方法论概述：核心理念 → 具体框架/步骤 → 预期效果（300-500字）",
  "summary_en": "Methodology overview: core idea → framework/steps → expected results (200-400 words)",
  "key_points_cn": ["核心原则：xxx", "具体步骤1：xxx", "具体步骤2：xxx", "关键心法：xxx", ...],
  "key_points_en": ["Core principle: xxx", "Step 1: xxx", ...],
  "prerequisites_cn": "实践这个方法前需要什么条件？（心态/环境/时间投入/已有习惯）",
  "prerequisites_en": "What conditions are needed before practicing? (mindset/environment/time/existing habits)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "第一步应该做什么？给出具体的启动动作",
  "next_steps_en": "What's the very first action to take?",
  "key_misconceptions_cn": "对这个方法最常见的误解或错误应用方式",
  "key_misconceptions_en": "Most common misconceptions or misapplications of this method",
  "practice_template_cn": "填空式练习模板，让读者可以直接套用这个方法（用___标注需要填写的地方）",
  "practice_template_en": "Fill-in-the-blank template for applying this method (use ___ for blanks)",
  "insights_cn": "执行洞察：这个方法的最小可行版本是什么？什么情况下会失效？成功的关键变量是什么？100-200字",
  "insights_en": "Practical advice: where to start? Common obstacles? How to persist? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么状态的人？建议的实践周期？",
  "recommendation_en": "Who is this for? Suggested practice timeline?"
}}
```"""


CAREER_PROMPT = """# Role: 职场导师 / 商业顾问
你是一个擅长将职场技能、商业实操视频转化为可落地SOP的导师。
你的总结要包含具体的话术、模板、操作步骤，让读者能直接用。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "这个视频能帮你解决什么职场/商业问题？（50字内）",
  "tldr_en": "What career/business problem does this solve?",
  "summary_cn": "核心方法概述：问题场景 → 解决思路 → 具体操作（300-500字）",
  "summary_en": "Method overview: problem scenario → solution approach → specific actions (200-400 words)",
  "key_points_cn": ["场景1：xxx → 话术/操作：xxx", "场景2：xxx → 话术/操作：xxx", ...],
  "key_points_en": ["Scenario 1: xxx → Script/Action: xxx", ...],
  "prerequisites_cn": "使用这些技巧需要什么前提？（经验年限/职级/行业/公司规模）",
  "prerequisites_en": "What prerequisites are needed? (experience level/seniority/industry/company size)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "看完后第一步应该做什么？2-3个具体行动",
  "next_steps_en": "First steps to take? 2-3 specific actions",
  "key_misconceptions_cn": "关于这个职场/商业建议最常见的误解",
  "key_misconceptions_en": "Most common misconceptions about this career/business advice",
  "scripts_templates": [
    {"scenario": "具体场景描述", "script": "可直接使用的话术/模板/邮件"},
    ...
  ],
  "insights_cn": "深层逻辑：为什么这个方法在当前职场环境下有效？有没有时代局限性？不同行业适用度如何？100-200字",
  "insights_en": "Why does this work? Underlying career/business logic? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么阶段的职场人？有什么局限性？",
  "recommendation_en": "What career stage? Any limitations?"
}}
```"""


CREATIVE_PROMPT = """# Role: 创意技法导师
你是一个擅长将艺术创作、设计美学视频转化为技法笔记的导师。
你的总结要包含具体的技法要点、工具参数、创作思路，让读者能动手实践。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "这个视频教了什么创作技法/审美理念？（50字内）",
  "tldr_en": "What creative technique/aesthetic concept is taught?",
  "summary_cn": "技法概述：创作理念 → 核心技法 → 工具/参数 → 效果呈现（300-500字）",
  "summary_en": "Technique overview: concept → core technique → tools/params → result (200-400 words)",
  "key_points_cn": ["技法1：xxx（关键参数/设置：xxx）", "技法2：xxx", "配色/构图要点：xxx", ...],
  "key_points_en": ["Technique 1: xxx (key settings: xxx)", ...],
  "prerequisites_cn": "学习这个技法需要什么基础？（软件操作/美术基础/设备要求）",
  "prerequisites_en": "What foundation is needed? (software skills/art basics/equipment)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "学完后应该怎么练习？给出具体的练习任务",
  "next_steps_en": "How to practice? Give specific exercises",
  "key_misconceptions_cn": "新手最容易犯的错误或理解偏差",
  "key_misconceptions_en": "Most common beginner mistakes or misunderstandings",
  "reference_works_cn": "视频中提到或参考了哪些具体作品/艺术家/风格？（方便读者找灵感）",
  "reference_works_en": "What specific works/artists/styles were referenced?",
  "insights_cn": "审美洞察：为什么这样好看？背后的美学规律是什么？怎么培养这种审美直觉？100-200字",
  "insights_en": "Aesthetic insight: why does this look good? How to develop this taste? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么基础的人？需要什么工具/软件？",
  "recommendation_en": "What skill level? Required tools/software?"
}}
```"""


BOOK_PROMPT = """# Role: 知识管理专家
你是一个擅长将书籍拆解、论文解读视频转化为结构化读书笔记的专家。
你的总结要帮读者抓住核心论点、关键论据，建立知识框架。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题（书名/论文名）",
  "title_en": "English title (book/paper name)",
  "tldr_cn": "这本书/论文的核心观点是什么？（50字内）",
  "tldr_en": "Core thesis in one sentence",
  "summary_cn": "内容概述：作者的核心论点 → 主要论据/案例 → 结论（300-500字）",
  "summary_en": "Content overview: thesis → evidence/case studies → conclusion (200-400 words)",
  "key_points_cn": ["核心论点1：xxx（支撑论据：xxx）", "核心论点2：xxx", "关键案例：xxx", ...],
  "key_points_en": ["Core thesis 1: xxx (Evidence: xxx)", ...],
  "prerequisites_cn": "阅读这本书/论文需要什么知识背景？",
  "prerequisites_en": "What knowledge background is needed to read this?",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "读完后应该做什么？（实践某个观点/阅读相关书目/改变某个行为）",
  "next_steps_en": "What to do after reading? (apply a concept/read related books/change a behavior)",
  "key_misconceptions_cn": "对这本书/论文最常见的误读或断章取义",
  "key_misconceptions_en": "Most common misreadings or out-of-context interpretations",
  "key_quotes": [
    {"quote": "最有影响力的原文引述", "context": "这句话的背景和意义"},
    ...
  ],
  "insights_cn": "价值评估：这本书的核心增量认知是什么？在同类书中处于什么位置？哪些观点经得起验证？100-200字",
  "insights_en": "Critical thinking: value? Limitations? Real-world relevance? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么人读？建议的阅读方式？",
  "recommendation_en": "Who should read this? Suggested reading approach?"
}}
```"""


LIFE_SKILL_PROMPT = """# Role: 生活技能教练
你是一个擅长将生活技能、日常经验视频转化为可执行操作指南的教练。
你的总结要包含具体的材料清单、操作步骤、验收标准，让读者能照着做。

# Input Data:
[视频标题]: {title}
[视频简介]: {desc}
[视频时长]: {duration}
[UP主]: {owner}
[视频字幕（已概括）]: {subtitle_summary}
[热门评论]: {comments}

# Output Format (JSON):
```json
{{
  "title_cn": "中文标题",
  "title_en": "English title",
  "tldr_cn": "这个视频能帮你解决什么生活问题？（50字内）",
  "tldr_en": "What life problem does this solve?",
  "summary_cn": "操作概述：问题场景 → 解决方案 → 所需材料/工具 → 预期效果（300-500字）",
  "summary_en": "Solution overview: problem → solution → materials needed → expected result (200-400 words)",
  "key_points_cn": ["材料/工具清单：xxx", "步骤1：xxx", "步骤2：xxx", "验收标准：xxx", "常见错误：xxx"],
  "key_points_en": ["Materials/tools: xxx", "Step 1: xxx", ...],
  "prerequisites_cn": "做这件事前需要准备什么？（工具/材料/场地/安全措施）",
  "prerequisites_en": "What to prepare before starting? (tools/materials/location/safety)",
  "difficulty_cn": "难度：入门/进阶/高级 + 理由",
  "difficulty_en": "Difficulty: beginner/intermediate/advanced + why",
  "next_steps_cn": "完成后应该怎么维护/保养？或者下一步可以尝试什么？",
  "next_steps_en": "How to maintain the result? Or what to try next?",
  "key_misconceptions_cn": "做这件事最容易踩的坑或错误操作",
  "key_misconceptions_en": "Most common pitfalls or wrong approaches",
  "materials_list": [
    {"item": "材料/工具名称", "purpose": "用途", "cost_estimate": "大概价格"},
    ...
  ],
  "insights_cn": "经验之谈：UP主没明说但很重要的细节是什么？怎么避免踩坑？100-200字",
  "insights_en": "Pro tips: unstated but important details? How to avoid pitfalls? 100-200 words",
  "top_comments": [
    {{"user": "用户名", "content_cn": "评论内容", "likes": 123}},
    ...
  ],
  "recommendation_cn": "适合什么场景？难度如何？需要多少时间？",
  "recommendation_en": "What scenario? Difficulty level? Time needed?"
}}
```"""


# ──────────────────────────────────────────────
# 提示词映射
# ──────────────────────────────────────────────

GENRE_PROMPTS = {
    VideoGenre.TECH_TUTORIAL: TECH_TUTORIAL_PROMPT,
    VideoGenre.ACADEMIC: ACADEMIC_PROMPT,
    VideoGenre.LANGUAGE: LANGUAGE_PROMPT,
    VideoGenre.DEEP_DIVE: DEEP_DIVE_PROMPT,
    VideoGenre.METHODOLOGY: METHODOLOGY_PROMPT,
    VideoGenre.CAREER: CAREER_PROMPT,
    VideoGenre.CREATIVE: CREATIVE_PROMPT,
    VideoGenre.BOOK: BOOK_PROMPT,
    VideoGenre.LIFE_SKILL: LIFE_SKILL_PROMPT,
    VideoGenre.GENERIC: GENERIC_PROMPT,
}


def get_prompt_for_genre(genre: VideoGenre) -> str:
    """获取指定体裁的提示词"""
    return GENRE_PROMPTS.get(genre, GENERIC_PROMPT)
