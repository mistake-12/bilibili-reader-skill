# bilibili-reader 功能需求与优先级定义

> 本文档针对项目现有缺陷提出系统性解决方案，并按优先级排序。
>
> 生成日期：2026-05-06
>
> 文档状态：初稿，供评审讨论

---

## 一、问题与解决方案对照表

| # | 问题分类 | 问题描述 | 解决方案 | 优先级 |
|---|---------|---------|---------|--------|
| 1 | 代码设计 | 意图路由依赖LLM判断，脆弱且主观 | 引入多维度特征提取 + 置信度评分机制 | P1 |
| 2 | 代码设计 | 字幕分段无语义感知，可能截断完整段落 | 语义分段（句子边界检测 + 段落聚类） | P2 |
| 3 | 代码设计 | 无LLM模式下总结几乎无价值 | 接入轻量级本地模型（gemma-2b / Qwen-0.5B）或提供更好的规则降级 | P1 |
| 4 | 代码设计 | PDF模板字段过多，样式与内容耦合 | 重构为组件化PDF模板，引入结构化渲染层 | P2 |
| 5 | 代码设计 | 记忆系统搜索仅字符串匹配，无向量检索 | 引入轻量向量数据库（ChromaDB）实现语义搜索 | P1 |
| 6 | 代码设计 | Cookie认证脆弱，过期无感知 | 添加Cookie健康检查 + 自动刷新机制 + 过期告警 | P1 |
| 7 | 代码设计 | 成就系统仅为打印，无状态存储与展示 | 持久化成就状态 + Web/终端徽章展示页面 | P3 |
| 8 | 需求出发 | 静态PDF非最优交付形式 | 从"PDF工厂"转型为"可查询知识库" | P0 |
| 9 | 需求出发 | 无用户反馈闭环，无法评估总结质量 | 引入用户评分/追问机制，形成优化飞轮 | P1 |
| 10 | 需求出发 | 体裁专用提示词人力维护成本高 | 统一提示词基座 + 体裁增强层（体裁作为元标签而非独立模板） | P2 |
| 11 | 需求出发 | 随机选视频不符合学习规律 | 增加"学习路径推荐"功能，基于体裁多样性和知识缺口分析 | P0 |
| 12 | 需求出发 | 无真正的学习效果验证 | 增加"理解度测验"模块，基于总结内容生成测验题 | P0 |
| 13 | 需求出发 | 缺乏数据收集，无产品迭代依据 | 埋点收集使用数据（处理量、完播率、搜索行为等） | P2 |

---

## 二、需求详情

### P0 — 核心价值重构（必须做，否则产品方向错误）

#### P0-1：从"PDF工厂"到"可查询知识库"

**问题**：当前输出物是静态 PDF，无法搜索、无法更新、无法追问。

**解决方案**：

```
output/
├── pdf/                    # 保留PDF导出（可选）
├── knowledge_base.json      # 结构化知识库（主输出）
└── index.json              # 全文索引
```

知识库结构：

```json
{
  "videos": [
    {
      "bvid": "BVxxx",
      "title_cn": "...",
      "title_en": "...",
      "genre": "💻 技术教程",
      "summary_cn": "...",
      "summary_en": "...",
      "key_points_cn": ["...", "..."],
      "key_points_en": ["...", "..."],
      "entities": ["Python", "FastAPI", "异步编程"],  // 实体标签
      "topics": ["后端开发", "Web框架"],
      "created_at": "2026-05-06T12:00:00Z",
      "quality_score": 4.5,         // 用户评分
      "user_notes": [],              // 用户追问/笔记
      "related_bvids": ["BVyyy"]     // 知识关联
    }
  ]
}
```

**核心能力**：
- 语义搜索：`"Python异步编程"` → 返回所有相关视频总结
- 知识图谱：按 topic/genre 构建视频间关联关系
- 追问交互：基于总结，用户可以追问细节（对接 LLM，引用已有总结作为上下文）
- 增量更新：如果视频内容有更新，可以重新生成总结并 diff

**预期收益**：从一次性消耗品变为长期可复用资产，直接解决"收藏了不看"的核心矛盾——用户不需要重新看视频，直接在知识库里检索即可。

---

#### P0-2：学习路径推荐（替代随机选视频）

**问题**：随机选视频没有考虑知识体系的完整性和学习规律。

**解决方案**：

```
收藏夹 → 视频分析 → 知识图谱构建 → 缺口分析 → 学习路径推荐
```

**实现逻辑**：

1. **视频打标**：自动提取每个视频的 topic、tech_stack、难度等级
2. **图谱构建**：基于 topic 共现关系构建有向图（如：学"Python基础"后才能学"FastAPI"）
3. **缺口分析**：对比用户已掌握 topics vs 收藏topics，识别知识空白
4. **路径生成**：按照"前置知识 → 入门 → 进阶"排序推荐下一个视频

**用户交互**：

```
你当前的知识体系：
  ✅ Python基础 (已消化 3 个视频)
  ✅ FastAPI入门 (已消化 1 个视频)
  🔲 异步编程进阶 (收藏 5 个视频)
  🔲 分布式系统 (收藏 2 个视频)

推荐下一个：BV1xxx — FastAPI异步深度指南
推荐理由：基于你的学习进度，这是最适合下一步的视频
```

**预期收益**：将"消化收藏"从随机行为变为有目的的学习计划，提升用户实际收获。

---

#### P0-3：理解度测验模块

**问题**：生成总结后无法验证用户是否真正理解了内容。

**解决方案**：

在知识库每条记录后追加：

```json
{
  "bvid": "BVxxx",
  "quizzes": [
    {
      "question_cn": "FastAPI 中依赖注入的目的是什么？",
      "options_cn": ["A. 提高运行速度", "B. 解耦代码，提高可测试性", "C. 减少代码行数", "D. 自动生成文档"],
      "answer": "B",
      "source": "key_points_cn[2]",
      "difficulty": "medium"
    }
  ]
}
```

**生成策略**：
- 每条 `key_point` 自动生成 1-2 道测验题
- 题目类型：选择题（简单生成）、简答题（高级功能）
- 答案来源标注：`"source": "key_points_cn[2]"` 方便用户回溯

**用户交互**：

```
看完总结后，系统提示：
"来测试一下你的理解？完成测验解锁完整成就"
用户答题 → 反馈正确率 → 错题自动关联到原视频位置
```

**预期收益**：将"看完总结"从被动接受变为主动输出，认知科学证明主动检索能显著提升记忆效果（检索练习效应）。

---

## P1 — 产品体验关键改进（严重影响当前使用体验）

#### P1-1：知识库语义搜索

**当前问题**：`memory.py` 的搜索只是简单的字符串包含匹配。

**解决方案**：引入 ChromaDB（轻量、Python原生、支持本地存储）

```python
# 概念示意
from chromadb import Client
client = Client()
collection = client.create_collection("bilibili_summaries")

# 每次生成总结时，向量化存储
collection.add(
    documents=[summary.summary_cn, summary.key_points_cn],
    metadatas=[{"bvid": video.bvid, "genre": summary.genre}],
    ids=[video.bvid]
)

# 语义搜索
results = collection.query(
    query_texts=["Python异步编程的原理"],
    n_results=5
)
```

**实施步骤**：
1. pip install chromadb
2. 初始化时加载已有 processed.json 到向量库
3. 搜索时同时执行关键词匹配 + 语义向量搜索，取并集/加权排序
4. 兼容原有 JSON 文件，ChromaDB 作为缓存层

**预期收益**：用户搜索"装饰器"能找到包含"decorator"、"@wrapper"等同义概念的视频总结。

---

#### P1-2：Cookie健康检查与自动刷新

**当前问题**：Cookie 过期程序直接报废，用户无感知。

**解决方案**：

```python
class CookieManager:
    def __init__(self, env_path: Path):
        self.env_path = env_path
        self.cookies = self._load()
        self.expiry_check()

    def expiry_check(self):
        """定期检查Cookie有效性"""
        try:
            api = BilibiliAPI(**self.cookies)
            api.get_user_mid()  # 触发验证
        except BilibiliAPIError as e:
            if "cookie" in str(e).lower():
                self._notify_and_refresh()

    def _notify_and_refresh(self):
        """通知用户并引导刷新Cookie"""
        print("⚠️ B站登录状态已过期")
        print("请重新扫码登录: python -m src --login")
        # 可选：自动打开登录流程
```

**增强**：记录 Cookie 获取时间，快过期（如7天）前主动提醒。

---

#### P1-3：用户反馈与质量飞轮

**当前问题**：总结质量无评估，无法优化。

**解决方案**：

**短期（无需模型增强）**：

```python
@dataclass
class SummaryFeedback:
    bvid: str
    helpful: bool          # 👍/👎 快速反馈
    rating: int            # 1-5 星
    missing_topic: str     # "缺少对xx的讲解"
    user_note: str         # 用户补充的笔记
```

每次生成 PDF 后，追加一个问题：

```
这份总结对你有帮助吗？
👍 有用 / 👎 一般
⭐⭐⭐⭐⭐ (1-5星评分)
补充：__________________
```

数据存入 `data/feedback.json`，按体裁聚合评分，高于平均分的体裁模板标记为"高质量参考"。

**长期**：用用户反馈数据微调体裁提示词，形成优化飞轮。

---

#### P1-4：多维度意图路由

**当前问题**：路由仅依赖 LLM 返回数字，脆弱且无法表达置信度。

**解决方案**：混合路由策略

```python
def classify_genre_hybrid(
    title: str,
    desc: str,
    subtitle_sample: str,
    llm_caller=None
) -> tuple[VideoGenre, float]:
    """
    返回：(体裁, 置信度)
    置信度 > 0.8 用关键词规则，< 0.8 再调用 LLM
    """
    # Step 1: 关键词规则（快速、确定性）
    genre, confidence = _rule_based_classify(title, desc, subtitle_sample)
    if confidence > 0.8:
        return genre, confidence

    # Step 2: 低置信度时调用 LLM
    if llm_caller:
        llm_genre = _llm_classify(title, desc, subtitle_sample, llm_caller)
        return llm_genre, 0.7  # LLM 置信度保守估计 0.7

    # Step 3: fallback
    return VideoGenre.GENERIC, 0.5


def _rule_based_classify(title, desc, subtitle) -> tuple[VideoGenre, float]:
    """基于关键词的规则分类"""
    GENRE_KEYWORDS = {
        VideoGenre.TECH_TUTORIAL: [
            "python", "javascript", "java", "react", "vue", "docker",
            "git", "linux", "sql", "api", "部署", "安装", "配置",
            "教程", "入门", "实战", "代码", "编程"
        ],
        VideoGenre.ACADEMIC: [
            "考研", "四六级", "公考", "高考", "公开课", "大学",
            "考试", "知识点", "公式", "定理", "证明"
        ],
        # ... 其他体裁
    }

    scores = {}
    text = f"{title} {desc} {subtitle[:500]}".lower()
    for genre, keywords in GENRE_KEYWORDS.items():
        scores[genre] = sum(1 for kw in keywords if kw in text)

    if not scores:
        return VideoGenre.GENERIC, 0.3

    top_genre = max(scores, key=scores.get)
    max_score = scores[top_genre]
    # 归一化置信度：至少匹配3个关键词才认为置信
    confidence = min(1.0, max_score / 5.0)
    return top_genre, confidence
```

**优势**：高频场景（明显的技术教程、明显的外语学习）用规则快速判断，减少 LLM 调用次数和延迟；边界情况才走 LLM。

---

## P2 — 优化改进（提升质量，但不影响核心体验）

#### P2-1：语义字幕分段

**当前问题**：按时间均分可能截断语义完整段落。

**解决方案**：

```python
def chunk_subtitles_semantic(
    subtitles: list[dict],
    max_chunk_duration: int = 600,
    min_chunk_duration: int = 180,
    overlap: int = 60
) -> list[list[dict]]:
    """
    语义感知的字幕分段：
    1. 在句子边界（大段停顿 > 3秒）分段
    2. 每段时长限制在 min~max 之间
    3. 相邻段落保留 overlap 秒重叠
    """
    if not subtitles:
        return []

    subs = sorted(subtitles, key=lambda s: s.get("from", 0))

    # 识别句子边界（时间戳间隙 > 3秒）
    segments = []
    current_segment = []

    for i, sub in enumerate(subs):
        current_segment.append(sub)
        if i < len(subs) - 1:
            gap = subs[i+1].get("from", 0) - sub.get("from", 0)
            # 超过3秒停顿 → 检查是否需要分段
            if gap > 3:
                segment_duration = current_segment[-1].get("from", 0) - current_segment[0].get("from", 0)
                if segment_duration >= min_chunk_duration:
                    segments.append(current_segment)
                    current_segment = []

    # 处理剩余内容
    if current_segment:
        segments.append(current_segment)

    # 如果段落太少，合并短段落
    segments = _merge_short_segments(segments, min_duration=min_chunk_duration)

    # 如果段落仍然太少，按时间均匀分段
    if len(segments) < 2:
        return _time_based_chunk(subs, max_chunk_duration, overlap)

    return segments
```

**关键改进**：
- 在语义自然断点（大停顿）分段，而非强制均分
- 保留最小段时长限制，避免过短段落
- 极端情况 fallback 到时间均分

---

#### P2-2：组件化 PDF 模板

**当前问题**：模板接收 30+ 变量，难以维护。

**解决方案**：引入结构化渲染层

```
templates/
├── base.html              # 基础框架（页眉、页脚、字体）
├── components/
│   ├── header.html        # 标题区
│   ├── summary_block.html # 摘要区（通用）
│   ├── key_points.html   # 要点区（通用）
│   ├── tech_stack.html   # 技术栈（体裁专用）
│   ├── vocabulary.html   # 词汇表（语言学习）
│   └── quiz.html          # 测验区（P0-3 新增）
└── summary.html           # 主模板，组合各组件
```

主模板变为：

```html
{% extends "base.html" %}

{% block content %}
  {% include "components/header.html" %}
  {% include "components/summary_block.html" %}
  {% include "components/key_points.html" %}

  <!-- 体裁专用区块，按需渲染 -->
  {% if genre.startswith("💻") %}
    {% include "components/tech_stack.html" %}
  {% elif genre.startswith("🗣️") %}
    {% include "components/vocabulary.html" %}
  {% endif %}

  {% include "components/quiz.html" %}
  {% include "components/footer.html" %}
{% endblock %}
```

---

#### P2-3：体裁提示词统一化

**当前问题**：10套独立模板，维护成本高，且字段利用率低。

**解决方案**：统一基座 + 动态增强

```python
# 单一通用提示词基座
BASE_PROMPT = """# Role: 视频内容分析师

# Input Data:
[视频标题]: {title}
[视频类型]: {genre}
[视频简介]: {desc}
[视频字幕]: {subtitle_summary}
[热门评论]: {comments}

# Output: 生成包含以下字段的JSON
{{
  "title_cn": "...",
  "tldr_cn": "...",
  "summary_cn": "...",
  "key_points_cn": [...],
  "prerequisites_cn": "...",
  "difficulty_cn": "...",
  "next_steps_cn": "...",
  "insights_cn": "...",
  "genre_specific": {{
    // 根据 genre 动态填充不同字段
    // 技术教程: {{tool_stack, code_snippets, pitfalls, expected_outcome}}
    // 语言学习: {{vocabulary_list, grammar_points}}
    // 书籍拆解: {{key_quotes, author_intent}}
    // ...
  }}
}}
"""

# 体裁增强指令（追加到基座后面）
GENRE_SUPPLEMENTS = {
    VideoGenre.TECH_TUTORIAL: """额外强调：
    - 提取所有代码片段和命令，保留原始格式
    - 列出工具清单及使用门槛
    - 补充常见错误和避坑提示""",
    VideoGenre.LANGUAGE: """额外强调：
    - 提取高频词汇和短语
    - 标注语法结构和例句
    - 给出跟读练习建议""",
    # ...
}
```

**优势**：一份基座 prompt + 体裁补充指令，减少模板数量，降低维护成本。

---

#### P2-4：数据埋点与产品指标

**当前问题**：无使用数据，无法迭代优化。

**解决方案**：轻量埋点（不上报到外部服务）

```python
@dataclass
class UsageEvent:
    event_type: str          # video_processed / search / quiz_attempted / ...
    timestamp: str
    metadata: dict

class Telemetry:
    """本地轻量埋点，数据保存在 data/telemetry.jsonl"""

    def track(self, event_type: str, **metadata):
        event = UsageEvent(
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        self._append(event)

    def get_summary(self) -> dict:
        """生成产品指标摘要"""
        return {
            "total_processed": self._count("video_processed"),
            "avg_quality_score": self._avg("quality_rating"),
            "top_genres": self._top_genres(),
            "search_queries": self._top_searches(),
            "quiz_completion_rate": self._rate("quiz_attempted"),
        }
```

---

## P3 — 锦上添花（体验加分，但非必需）

#### P3-1：持久化成就系统

**当前状态**：成就仅打印到终端，重启后丢失。

**解决方案**：

```python
@dataclass
class Achievement:
    id: str
    name: str
    description: str
    unlocked_at: str | None = None

ACHIEVEMENTS = [
    Achievement("first_dig", "🌱 初次发掘", "消化了第一个视频"),
    Achievement("archaeologist_5", "🔍 考古新手", "消化 5 个视频"),
    Achievement("tech_master", "🔧 技术工匠", "技术教程类消化 5+ 个"),
    # ...
]

# data/achievements.json
{
  "unlocked": ["first_dig", "archaeologist_5"],
  "current_progress": {
    "archaeologist_10": 7,  # 进度 7/10
    "tech_master": 3         # 进度 3/5
  }
}
```

**展示**：提供独立命令 `python -m src --achievements`，展示徽章页面。

---

## 三、优先级实施路线图

```
Phase 1（1-2周）：止血 + 基础体验
├─ P1-2 Cookie健康检查
├─ P1-3 用户反馈机制
└─ P1-4 多维度意图路由
    └─ 减少30% LLM调用次数

Phase 2（2-4周）：核心价值升级
├─ P0-1 知识库持久化 + 搜索升级（P1-1 ChromaDB）
└─ P0-2 学习路径推荐
    └─ 从"随机"变为"按需"

Phase 3（4-8周）：深度学习闭环
├─ P0-3 理解度测验模块
├─ P2-1 语义字幕分段
└─ P1-1（ChromaDB接入完成）

Phase 4（持续迭代）：
├─ P2-2 组件化PDF模板
├─ P2-3 统一提示词基座
├─ P2-4 数据埋点
└─ P3-1 持久化成就系统
```

---

## 四、放弃清单（明确不做）

以下是我认为不值得投入的方向，列出原因以免未来走弯路：

| 放弃项 | 原因 |
|--------|------|
| 体裁专用PDF模板 | 维护10套模板收益递减，组件化足够 |
| 自动刷新Cookie | B站不支持主动刷新，只能引导用户重新登录 |
| 视频内容Embedding做推荐 | 数据量太小（几百个视频），推荐效果不如规则引擎 |
| 导出到Notion/Obsidian | 增加外部依赖，且用户不一定用这些工具 |
| 微信/飞书原生推送集成 | 维护成本高，用户实际使用率低（PDF通知就够了） |
| 自动体裁提示词优化 | 需要大量用户反馈数据积累，短期内不现实 |
| 视频截图/封面自动提取 | 干扰PDF阅读体验，PDF应该纯文本化 |
