# bilibili-reader v2.0 开发文档

> 本文档是 bilibili-reader 项目 v2.0 的完整开发指南，包含所有需求确认、技术方案、文件清单和实施顺序。
>
> 生成日期：2026-05-06
>
> 需求确认状态：✅ 全部确认

---

## 一、需求确认汇总

以下所有需求已确认引入，进入开发阶段：

| # | 优先级 | 需求 | 决策依据 |
|---|--------|------|---------|
| v2.0 | P0 | PDF 提示词模板 v2.0（双视角结构） | 核心内容重构 |
| P1-4-m | P1 | 多分类时调用多分类内容/合并渲染 | 用户确认：视频可同时属于多个体裁 |
| P1-1 | P1 | ChromaDB 向量搜索 | 用户确认引入 |
| P1-2 | P1 | Cookie 健康检查 + 过期告警 | 用户确认引入 |
| P2-2 | P2 | 组件化 PDF 模板 | 用户确认引入 |
| P2-3 | P2 | 统一基座提示词（体裁作为元标签） | 用户确认引入 |
| P0-2 | P0 | 学习路径推荐（基于 Topic 依赖图） | 用户确认引入 |
| P0-3 | P0 | 理解度测验模块（思考题 + 选择题） | 用户确认引入 |

---

## 二、整体架构

### 2.1 目录结构

```
bilibili-reader/
├── src/
│   ├── bilibili_api.py          # B站 API（不变）
│   ├── intent_router.py          # ★ 重构：统一基座 + 多分类
│   ├── summarizer.py             # ★ 重构：v2.0 prompt + VideoSummary 扩展
│   ├── pdf_generator.py          # ★ 重构：组件化模板渲染
│   ├── memory.py                 # ★ 重构：ChromaDB 向量搜索
│   ├── cookie_manager.py          # ★ 新增：Cookie 健康检查
│   ├── quiz_generator.py         # ★ 新增：理解度测验生成
│   ├── topic_graph.py            # ★ 新增：Topic 依赖图 + 学习路径
│   ├── search_engine.py          # ★ 新增：混合搜索（向量+关键词）
│   ├── telemetry.py               # （可选）轻量埋点
│   ├── progress.py               # ★ 重构：学习路径推荐替代随机
│   └── ...
├── templates/
│   ├── base.html                  # 基础框架（页眉/页脚/字体/CSS 变量）
│   ├── _macros.html               # Jinja2 宏（可复用小组件）
│   ├── components/
│   │   ├── _header.html           # 标题区
│   │   ├── _tldr.html            # TLDR 区块
│   │   ├── _my_analysis.html      # ★ v2.0：「我的解读」主区域
│   │   │   ├── _concept_block.html # 单概念区块（def+principle+analogy+insight）
│   │   │   └── _thinking.html      # 思考题区块
│   │   ├── _video_transcript.html  # ★ v2.0：「视频完整陈述」主区域
│   │   │   └── _segment.html       # 单时间段区块
│   │   ├── _key_points.html       # 核心要点
│   │   ├── _prerequisites.html    # 前置知识
│   │   ├── _difficulty.html       # 难度评级
│   │   ├── _misconceptions.html   # 常见误解
│   │   ├── _insights.html         # 洞察区块
│   │   ├── _genre_tech.html       # 体裁专用：技术教程
│   │   ├── _genre_academic.html   # 体裁专用：学科教育
│   │   ├── _genre_language.html   # 体裁专用：语言学习
│   │   ├── _genre_deepdive.html   # 体裁专用：硬核科普
│   │   ├── _genre_methodology.html # 体裁专用：方法论
│   │   ├── _genre_career.html     # 体裁专用：职场
│   │   ├── _genre_creative.html   # 体裁专用：创意
│   │   ├── _genre_book.html       # 体裁专用：书籍
│   │   ├── _genre_life.html       # 体裁专用：生活技能
│   │   ├── _quiz.html             # ★ v2.0：测验区
│   │   ├── _comments.html          # 评论区
│   │   ├── _recommendation.html    # 推荐区
│   │   └── _footer.html           # 页脚
│   └── summary.html               # 主模板（按体裁拼接组件）
├── data/
│   ├── processed.json             # 已处理视频记录（不变）
│   ├── chroma_db/                # ★ 新增：ChromaDB 向量存储
│   │   ├── chroma.sqlite3
│   │   └── ...
│   ├── topic_graph.json           # ★ 新增：Topic 依赖图
│   ├── quiz_cache/               # ★ 新增：测验题缓存
│   └── feedback.json              # 用户反馈（可选）
├── docs/
│   ├── prompt-template-v2.md      # ★ v2.0 提示词规范（已完成）
│   ├── feature-requirements.md    # 需求文档（参考）
│   ├── product-analysis.md
│   ├── video-script.md
│   └── DEVELOPMENT.md             # ★ 本文档
└── ...
```

---

## 三、文件改动详解

### 3.1 `src/intent_router.py` — 统一基座 + 多分类

#### 改动 1：统一基座提示词

将现有的 10 套独立模板重构为**一个基座 + 体裁增强指令**：

```python
# ─── 基座提示词（v2.0 完整版，来自 prompt-template-v2.md）───
BASE_PROMPT_V2 = """# Role: 视频内容分析师 + 学习笔记专家

你是 bilibili 视频的深度学习伴侣...
[完整内容见 docs/prompt-template-v2.md 第四节的示例模板]
"""

# ─── 体裁增强指令（轻量追加，不是独立模板）───
GENRE_ENHANCEMENTS: dict[VideoGenre, str] = {
    VideoGenre.TECH_TUTORIAL: """
    【体裁增强 — 技术教程】
    重点强调以下字段的深度：
    - tool_stack：必须包含每个工具的 name、purpose、barrier
    - code_snippets：代码必须完整可运行，保留原始注释，标注使用步骤
    - expected_outcome：必须给出可验证的预期结果和验证命令
    - pitfalls：必须来自字幕/评论原文，标注来源
    """,
    VideoGenre.LANGUAGE: """
    【体裁增强 — 语言学习】
    重点强调：
    - vocabulary_list：每个词条必须包含 word、meaning、example
    - 典型错误：必须标注「中文母语者特有错误」
    """,
    # ... 其他体裁类似，每个 50-100 行
}

def build_prompt(genre: VideoGenre, **context) -> str:
    """拼接基座 + 体裁增强"""
    base = BASE_PROMPT_V2.format(**context)
    enhancement = GENRE_ENHANCEMENTS.get(genre, "")
    return base + "\n\n" + enhancement
```

#### 改动 2：多分类支持

当视频同时属于多个体裁时，合并渲染：

```python
def classify_genre_multi(
    title: str, desc: str, subtitle_sample: str, llm_caller=None
) -> list[tuple[VideoGenre, float]]:
    """
    返回：[(体裁1, 置信度1), (体裁2, 置信度2), ...]
    置信度 >= 0.7 的体裁全部纳入
    """
    genre_list = _llm_classify_multi(title, desc, subtitle_sample, llm_caller)
    # genre_list: ["1", "2", "6"] 或 ["1"] 或 ["4"]
    results = []
    for num in genre_list:
        genre = _NUM_TO_GENRE.get(num)
        confidence = 0.8  # LLM 返回数字时保守估计 0.8
        results.append((genre, confidence))

    # 置信度 >= 0.7 才纳入，否则降级为 GENERIC
    filtered = [(g, c) for g, c in results if c >= 0.7]
    return filtered if filtered else [(VideoGenre.GENERIC, 1.0)]
```

```python
def get_prompts_for_genres(
    genres: list[tuple[VideoGenre, float]]
) -> list[tuple[VideoGenre, str, float]]:
    """为多个体裁生成对应的提示词"""
    return [
        (genre, build_prompt(genre, ...), confidence)
        for genre, confidence in genres
    ]
```

#### 改动 3：Prompt 注入质量控制

在 `build_prompt` 末尾自动追加质量检查清单（从 prompt-template-v2.md 第五章复制）。

---

### 3.2 `src/summarizer.py` — VideoSummary 扩展 + v2.0 字段

#### 改动 1：VideoSummary dataclass 新增字段

```python
@dataclass
class VideoSummary:
    # ── 原有字段（保留）───
    title_cn: str = ""
    # ... 所有原有字段 ...

    # ── v2.0 新增字段 ──
    my_analysis: dict = field(default_factory=dict)  # 对应 JSON my_analysis
    video_transcript: dict = field(default_factory=dict)  # 对应 JSON video_transcript

    # 测验相关（可选，快速接入）
    quizzes: list[dict] = field(default_factory=list)
    thinking_questions: list[dict] = field(default_factory=list)
```

#### 改动 2：多分类渲染支持

当视频属于多个体裁时，生成多份总结，然后合并：

```python
def generate_summary_multi(
    video: VideoInfo,
    subtitles: list[dict],
    comments: list[Comment],
    danmakus: list[Danmaku],
    genres: list[tuple[VideoGenre, float]],
    llm_caller=None,
) -> VideoSummary:
    """
    多体裁模式：每个体裁生成一份总结，合并到主 summary
    """
    primary_genre, primary_conf = genres[0]
    main_summary = _generate_single(..., primary_genre, llm_caller)

    if len(genres) > 1:
        # 合并次级体裁的体裁专用字段
        for genre, conf in genres[1:]:
            secondary = _generate_single(..., genre, llm_caller)
            # 只合并体裁专用字段，核心字段（summary_cn 等）以主summary为准
            main_summary = _merge_genre_fields(main_summary, secondary, genre)

    return main_summary
```

#### 改动 3：summarize_subtitles_with_chunking 增强

保持现有逻辑不变，字幕分段逻辑无需调整。

---

### 3.3 `src/memory.py` — ChromaDB 向量搜索

#### 核心逻辑

```python
import chromadb
from chromadb.config import Settings
from .summarizer import VideoSummary

class SemanticMemory:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.chroma_client = chromadb.PersistentClient(
            path=str(data_dir / "chroma_db")
        )
        self.collection = self.chroma_client.get_or_create_collection(
            name="bilibili_summaries",
            metadata={"description": "B站视频总结向量库"}
        )
        self.videos = self._load_processed()

    def _vectorize(self, summary: VideoSummary, video: VideoInfo):
        """将总结向量化存入 ChromaDB"""
        doc_cn = " ".join(filter(None, [
            summary.title_cn,
            summary.tldr_cn,
            summary.summary_cn,
            *summary.key_points_cn,
            summary.insights_cn or "",
        ]))
        doc_en = " ".join(filter(None, [
            summary.title_en,
            summary.tldr_en,
            summary.summary_en,
            *summary.key_points_en,
            summary.insights_en or "",
        ]))

        self.collection.add(
            documents=[doc_cn, doc_en],
            metadatas=[
                {"bvid": video.bvid, "lang": "cn", "genre": summary.genre},
                {"bvid": video.bvid, "lang": "en", "genre": summary.genre},
            ],
            ids=[f"{video.bvid}_cn", f"{video.bvid}_en"]
        )

    def search(self, query: str, top_k: int = 5, genre_filter: str = "") -> list[dict]:
        """
        混合搜索：向量语义搜索 + 关键词匹配，取加权并集
        """
        # 1. 向量搜索
        vector_results = self.collection.query(
            query_texts=[query],
            n_results=top_k * 2,
            where={"genre": genre_filter} if genre_filter else None,
        )

        # 2. 关键词匹配
        keyword_results = [
            v for v in self.videos
            if query.lower() in v.get("title_cn", "").lower()
            or query.lower() in v.get("summary_cn", "").lower()
        ][:top_k]

        # 3. 合并排序
        merged = self._merge_and_rerank(query, vector_results, keyword_results)
        return merged[:top_k]

    def _merge_and_rerank(self, query, vector_results, keyword_results) -> list[dict]:
        """加权合并向量结果和关键词结果"""
        seen = set()
        scored = []

        # 关键词匹配给基础分 1.0
        for v in keyword_results:
            seen.add(v["bvid"])
            scored.append((v, 1.0))

        # 向量匹配按相似度给分（相似度在 0-1 之间）
        if vector_results and vector_results.get("distances"):
            for bvid, distance in zip(
                vector_results["ids"][0], vector_results["distances"][0]
            ):
                if bvid not in seen:
                    bvid_clean = bvid.replace("_cn", "").replace("_en", "")
                    # distance 越小越相似，转为 0-1 分数
                    score = max(0, 1.0 - distance)
                    seen.add(bvid_clean)
                    target = next((v for v in self.videos if v["bvid"] == bvid_clean), None)
                    if target:
                        scored.append((target, score * 0.8))  # 向量权重 0.8

        scored.sort(key=lambda x: x[1], reverse=True)
        return [v for v, _ in scored]

    def on_video_processed(self, summary: VideoSummary, video: VideoInfo):
        """视频处理完成后，自动向量化"""
        self._vectorize(summary, video)

    def reindex_all(self):
        """全量重新索引（首次安装或数据损坏时调用）"""
        self.collection.delete(where={})
        for video_data in self.videos:
            # 从 processed.json 重建向量（如果 summary 数据还在）
            pass  # 实现略
```

---

### 3.4 `src/cookie_manager.py` — Cookie 健康检查（新增文件）

```python
"""Cookie 健康检查与过期告警模块"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from .bilibili_api import BilibiliAPI, BilibiliAPIError

@dataclass
class CookieStatus:
    valid: bool
    last_check: str  # ISO 时间戳
    expires_in_days: int | None  # None 表示未知
    error_message: str | None = None

class CookieManager:
    """管理 B站 Cookie 的健康检查和过期提醒"""

    def __init__(self, env_path: Path, bilibili_api_class= BilibiliAPI):
        self.env_path = env_path
        self.api_class = bilibili_api_class
        self.cookies = self._load_cookies()
        self._last_valid = True

    def _load_cookies(self) -> dict:
        """从 .env 文件加载 Cookie"""
        cookies = {}
        if self.env_path.exists():
            for line in self.env_path.read_text().splitlines():
                if line.startswith("BILI_SESSDATA"):
                    cookies["SESSDATA"] = line.split("=", 1)[1].strip()
                elif line.startswith("BILI_BILI_JCT"):
                    cookies["bili_jct"] = line.split("=", 1)[1].strip()
        return cookies

    def check_health(self) -> CookieStatus:
        """检查 Cookie 是否有效"""
        try:
            api = self.api_class(**self.cookies)
            api.get_user_mid()  # 触发验证请求
            return CookieStatus(
                valid=True,
                last_check=datetime.now().isoformat(),
                expires_in_days=None,  # B站不提供明确过期时间
            )
        except BilibiliAPIError as e:
            error_msg = str(e)
            self._last_valid = False
            return CookieStatus(
                valid=False,
                last_check=datetime.now().isoformat(),
                expires_in_days=None,
                error_message=error_msg,
            )

    def warn_if_expiring(self) -> bool:
        """
        每次启动时调用，若 Cookie 无效应急退出
        返回 True 表示正常，False 表示有问题但可继续（仅警告）
        """
        status = self.check_health()
        if status.valid:
            return True

        print("=" * 50)
        print("⚠️  B站登录状态异常")
        print(f"错误信息：{status.error_message}")
        print("=" * 50)
        print("请重新获取 Cookie：")
        print("  1. 登录 bilibili.com")
        print("  2. 开发者工具 → Application → Cookies → bilibili.com")
        print("  3. 复制 SESSDATA 和 bili_jct 的值")
        print("  4. 更新 .env 文件中的 BILI_SESSDATA 和 BILI_BILI_JCT")
        print("=" * 50)
        return False

    def refresh(self):
        """重新从 .env 加载 Cookie（用户手动更新后调用）"""
        self.cookies = self._load_cookies()
        return self.check_health()
```

---

### 3.5 `src/quiz_generator.py` — 理解度测验（新增文件）

```python
"""理解度测验生成模块"""

from dataclasses import dataclass, field
from .summarizer import VideoSummary

@dataclass
class Quiz:
    question_cn: str
    options_cn: list[str] | None = None  # None = 简答题
    answer: str | None = None  # "A", "B", "C", "D" 或简答关键词
    source: str = ""  # 来源：key_points_cn[2] 等
    difficulty: str = "medium"  # easy / medium / hard
    type: str = "choice"  # choice / open


QUIZ_PROMPT = """基于以下视频总结，生成 {count} 道理解度测验题。

视频总结：
标题：{title}
核心要点：
{key_points}
洞察：
{insights}

要求：
1. 题目类型为选择题，每题 4 个选项，必须有且仅有一个正确答案
2. 答案必须直接来自上述总结内容，不能编造
3. 干扰项要有一定迷惑性，但不能太离谱
4. 每道题必须标注 source（来源的要点编号）

输出格式（JSON数组）：
[
  {{
    "question_cn": "题目内容",
    "options_cn": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
    "answer": "B",
    "source": "key_points_cn[2]",
    "difficulty": "medium",
    "type": "choice"
  }}
]
"""

def generate_quizzes(
    summary: VideoSummary,
    count: int = 3,
    llm_caller=None
) -> list[Quiz]:
    """生成测验题"""
    if not llm_caller:
        return []

    key_points_text = "\n".join(
        f"{i}. {p}" for i, p in enumerate(summary.key_points_cn)
    )

    prompt = QUIZ_PROMPT.format(
        title=summary.title_cn,
        key_points=key_points_text,
        insights=summary.insights_cn or "无",
        count=count,
    )

    response = llm_caller(prompt)

    import json
    try:
        data = json.loads(_extract_json(response))
        return [Quiz(**q) for q in data]
    except Exception:
        return []


def _extract_json(text: str) -> str:
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text.strip()
```

---

### 3.6 `src/topic_graph.py` — Topic 依赖图 + 学习路径（新增文件）

```python
"""Topic 依赖图与学习路径推荐"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from .summarizer import VideoSummary

@dataclass
class TopicNode:
    name: str
    depends_on: list[str] = field(default_factory=list)
    unlocks: list[str] = field(default_factory=list)
    description: str = ""

@dataclass
class TopicGraph:
    topics: dict[str, TopicNode] = field(default_factory=dict)
    video_topics: dict[str, list[str]] = field(default_factory=dict)
    # video_topics: {bvid: [topic1, topic2, ...]}

    @classmethod
    def load(cls, path: Path) -> "TopicGraph":
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls(
            topics={
                k: TopicNode(name=k, **v) for k, v in data.get("topics", {}).items()
            },
            video_topics=data.get("video_topics", {}),
        )

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "topics": {k: v.__dict__ for k, v in self.topics.items()},
            "video_topics": self.video_topics,
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def register_video(self, bvid: str, topics: list[str]):
        """注册视频的 topic"""
        self.video_topics[bvid] = topics
        for topic in topics:
            if topic not in self.topics:
                self.topics[topic] = TopicNode(name=topic)

    def infer_dependencies(self, summary: VideoSummary, bvid: str):
        """从 prerequisites 和 next_steps 推断 topic 依赖关系"""
        if summary.prerequisites_cn:
            # TODO: 调用 LLM 从 prerequisites 中提取 topic
            pass

    def get_learning_path(
        self, mastered_bvids: set[str], candidate_bvids: set[str]
    ) -> list[tuple[str, str, str]]:
        """
        返回推荐路径：[(bvid, title, reason), ...]
        """
        mastered_topics = set()
        for bvid in mastered_bvids:
            mastered_topics.update(self.video_topics.get(bvid, []))

        candidates = []
        for bvid in candidate_bvids:
            topics = self.video_topics.get(bvid, [])
            if not topics:
                continue

            # 检查前置知识是否满足
            ready = all(
                dep in mastered_topics
                for topic in topics
                for dep in self.topics.get(topic, TopicNode(topic)).depends_on
            )

            if ready:
                candidates.append((bvid, topics, "前置知识已满足"))

        # 按 topic 优先级排序（先推荐 topic 下视频数最多的）
        candidates.sort(key=lambda x: -len(x[1]))
        return [(b, "", r) for b, _, r in candidates[:5]]


TOPIC_EXTRACT_PROMPT = """从以下视频信息中提取3-5个核心topic标签。

标题：{title}
总结：{summary}
前置知识：{prerequisites}

要求：
- 使用标准化的topic名称（如"Python异步编程"、"Docker容器化"、"考研政治"）
- 只返回topic名称，每行一个，不要其他说明

返回格式（JSON数组）：
["topic1", "topic2", "topic3"]
"""

def extract_topics(
    summary: VideoSummary,
    llm_caller=None
) -> list[str]:
    """从总结中提取 topic"""
    if not llm_caller:
        return []

    prompt = TOPIC_EXTRACT_PROMPT.format(
        title=summary.title_cn,
        summary=summary.summary_cn,
        prerequisites=summary.prerequisites_cn,
    )

    response = llm_caller(prompt)
    import json
    try:
        return json.loads(_extract_json(response))
    except Exception:
        return []

def _extract_json(text: str) -> str:
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    return text.strip()
```

---

### 3.7 `src/search_engine.py` — 混合搜索（新增文件）

```python
"""混合搜索：向量 + 关键词 + 过滤器"""

from pathlib import Path
from .memory import SemanticMemory

class SearchEngine:
    def __init__(self, memory: SemanticMemory):
        self.memory = memory

    def search(
        self,
        query: str,
        top_k: int = 5,
        genre_filter: str = "",
        sort_by: str = "relevance"  # relevance | date | views
    ) -> list[dict]:
        results = self.memory.search(query, top_k=top_k * 2, genre_filter=genre_filter)

        if sort_by == "date":
            results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        elif sort_by == "views":
            results.sort(key=lambda x: x.get("view_count", 0), reverse=True)

        return results[:top_k]

    def suggest(self, partial_query: str) -> list[str]:
        """搜索建议（基于已有标题的前缀匹配）"""
        titles = [v.get("title_cn", "") for v in self.memory.videos]
        return [t for t in titles if partial_query.lower() in t.lower()][:5]
```

---

### 3.8 `src/progress.py` — 学习路径替代随机选择

#### 改动点

```python
from .topic_graph import TopicGraph

def select_next_video(
    unprocessed: list[dict],
    topic_graph: TopicGraph,
    mastered_bvids: set[str],
) -> dict | None:
    """
    基于学习路径推荐下一个视频，而非随机选择
    """
    if not unprocessed:
        return None

    # 获取路径推荐
    path = topic_graph.get_learning_path(
        mastered_bvids=mastered_bvids,
        candidate_bvids={v["bvid"] for v in unprocessed},
    )

    if path:
        # 有推荐路径，取第一个
        bvid, _, reason = path[0]
        target = next((v for v in unprocessed if v["bvid"] == bvid), None)
        if target:
            print(f"🎯 学习路径推荐：{target['title_cn']}")
            print(f"   推荐理由：{reason}")
            return target

    # 无推荐（冷启动），fallback 到随机
    print("📚 随机选择（知识图谱尚无足够数据）")
    import random
    return random.choice(unprocessed)
```

---

### 3.9 `templates/` — 组件化 PDF 模板

#### 渲染层改动（`pdf_generator.py`）

```python
def generate_pdf(summary: VideoSummary, output_dir: Path, ...) -> Path:
    # ... 现有逻辑 ...

    # ★ 渲染 v2.0 字段
    html_content = template.render(
        # ── 原有字段（保持不变）───
        title_cn=summary.title_cn,
        summary_cn=summary.summary_cn,
        # ... 所有原有字段 ...

        # ── v2.0 新增字段 ──
        my_analysis=summary.my_analysis,
        video_transcript=summary.video_transcript,
        quizzes=getattr(summary, "quizzes", []),
        thinking_questions=getattr(summary, "thinking_questions", []),
    )
    # ...
```

#### 模板文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `base.html` | ~60 | 框架、CSS 变量、字体、页眉页脚基础样式 |
| `_macros.html` | ~40 | Jinja2 宏（星级渲染、分页符、条件块） |
| `components/_header.html` | ~25 | 标题区 |
| `components/_tldr.html` | ~20 | TLDR 区块 |
| `components/_my_analysis.html` | ~30 | 「我的解读」入口，遍历 concepts |
| `components/_concept_block.html` | ~120 | 单概念完整区块（def+principle+analogy+insight） |
| `components/_thinking.html` | ~40 | 思考题区块 |
| `components/_video_transcript.html` | ~30 | 「视频完整陈述」入口，遍历 segments |
| `components/_segment.html` | ~60 | 单时间段完整区块 |
| `components/_key_points.html` | ~30 | 核心要点 |
| `components/_prerequisites.html` | ~20 | 前置知识 |
| `components/_difficulty.html` | ~20 | 难度评级 |
| `components/_misconceptions.html` | ~20 | 常见误解 |
| `components/_insights.html` | ~20 | 洞察区块 |
| `components/_quiz.html` | ~80 | 测验区（题目+选项） |
| `components/_genre_*.html` | 各~30 | 各体裁专用区块（9个） |
| `components/_comments.html` | ~30 | 评论区 |
| `components/_recommendation.html` | ~20 | 推荐区 |
| `components/_footer.html` | ~15 | 页脚 |
| `summary.html` | ~50 | 主模板，按体裁拼接组件 |
| **合计** | **~700行** | 拆分后每个文件 < 120 行 |

#### 渲染样式重点

`components/_concept_block.html` 核心布局：

```html
<!-- ★ v2.0 概念区块：definition → principle → analogy → insight -->
<div class="concept-block" style="margin-bottom: 20px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden;">

  <!-- 概念标题 -->
  <div class="concept-header" style="background: linear-gradient(135deg, #00a1d6, #0087b5); color: white; padding: 8px 15px;">
    <strong>{{ concept.name }}</strong>
    {% if concept.layer == 'concept' %}
    <span class="layer-tag">📖 概念层</span>
    {% else %}
    <span class="layer-tag">🔧 操作层</span>
    {% endif %}
  </div>

  <!-- Definition -->
  <div style="padding: 12px 15px; background: #fff;">
    <div style="font-size: 9pt; color: #888; margin-bottom: 4px;">📌 定义</div>
    {{ concept.definition }}
  </div>

  <!-- Principle（理论阐述）★ -->
  <div style="padding: 12px 15px; background: #f8f9fa; border-top: 1px dashed #ddd;">
    <div style="font-size: 9pt; color: #555; margin-bottom: 6px; font-weight: bold;">📚 理论阐述</div>
    <div style="line-height: 1.9; font-size: 10pt;">{{ concept.principle }}</div>
  </div>

  <!-- Analogy -->
  <div style="padding: 12px 15px; background: #fff8e1; border-top: 1px dashed #ddd;">
    <div style="font-size: 9pt; color: #856404; margin-bottom: 6px;">💡 生活类比</div>
    <div><strong>场景：</strong>{{ concept.analogy.scenario }}</div>
    <div style="margin-top: 6px;"><strong>映射：</strong>{{ concept.analogy.mapping }}</div>
    <div style="margin-top: 6px; color: #dc3545;"><strong>⚠️ 局限：</strong>{{ concept.analogy.limitation }}</div>
  </div>

  <!-- Insight -->
  <div style="padding: 12px 15px; background: #e8f4fd; border-top: 1px dashed #ddd;">
    <div style="font-size: 9pt; color: #00a1d6; margin-bottom: 4px;">🧠 个人洞察</div>
    {{ concept.insight }}
  </div>

</div>
```

---

## 四、实施顺序与依赖关系

```
Phase 1: 基础设施（无依赖）
├─ 4.1 `cookie_manager.py`         ← 新增，无依赖
└─ 4.2 `templates/` 组件化基础      ← 新增，无依赖

Phase 2: 核心数据流（依赖 Phase 1）
├─ 4.3 `intent_router.py` 重构     ← 依赖：统一基座 prompt（无代码依赖）
├─ 4.4 `summarizer.py` v2.0 扩展  ← 依赖：prompt-template-v2.md
└─ 4.5 `pdf_generator.py` 适配     ← 依赖：组件化模板

Phase 3: 搜索增强（无特殊依赖）
├─ 4.6 `memory.py` ChromaDB       ← 可独立引入
├─ 4.7 `search_engine.py`          ← 依赖：memory.py
└─ 4.8 `topic_graph.py`            ← 可独立引入

Phase 4: 功能增强（依赖 Phase 2+3）
├─ 4.9 `progress.py` 路径推荐      ← 依赖：topic_graph.py
├─ 4.10 `quiz_generator.py`       ← 依赖：summarizer.py
└─ 4.11 全量向量化（冷启动）        ← 依赖：memory.py

建议实施周期：
  Phase 1: 第 1 天
  Phase 2: 第 2-4 天
  Phase 3: 第 3-5 天（与 Phase 2 并行）
  Phase 4: 第 5-7 天
```

---

## 五、兼容性策略

### 5.1 VideoSummary 向后兼容

v2.0 字段初始化为空，PDF 模板中降级处理：

```python
# summarizer.py
@dataclass
class VideoSummary:
    # ... 原有字段 ...
    my_analysis: dict = field(default_factory=dict)
    video_transcript: dict = field(default_factory=dict)
    quizzes: list = field(default_factory=list)
```

```html
<!-- summary.html -->
{% if my_analysis and my_analysis.concepts %}
  {% include "_my_analysis.html" %}
{% else %}
  <!-- 降级：渲染原有 summary + key_points -->
  {% include "_key_points.html" %}
{% endif %}
```

### 5.2 ChromaDB 冷启动

首次启动时自动检测本地 ChromaDB 是否已有数据，若无则自动从 `processed.json` 全量向量化：

```python
def _ensure_indexed(self):
    indexed_ids = set(self.collection.get()["ids"])
    for video_data in self.videos:
        cn_id = f"{video_data['bvid']}_cn"
        if cn_id not in indexed_ids:
            self._vectorize_from_json(video_data)
```

### 5.3 Topic Graph 冷启动

`topic_graph.json` 初始为空，`get_learning_path` 在无数据时自动 fallback 到随机选择（见 `progress.py` 改动）。

---

## 六、测试计划

### 6.1 单元测试

```python
# tests/test_intent_router.py
def test_multi_genre():
    result = classify_genre_multi("Python异步教程", "...", "...")
    assert len(result) >= 1

def test_unified_base_prompt():
    prompt = build_prompt(VideoGenre.TECH_TUTORIAL, ...)
    assert "my_analysis" in prompt
    assert "video_transcript" in prompt
    assert len(prompt) > 2000  # 基座足够长

# tests/test_memory.py
def test_chroma_search():
    mem = SemanticMemory(data_dir)
    mem.search("异步编程")  # 应返回结果

# tests/test_topic_graph.py
def test_learning_path_fallback():
    graph = TopicGraph()
    result = graph.get_learning_path(set(), {"BV1": "BV1"})  # 空图应 fallback
    assert result == []  # 空图无推荐
```

### 6.2 集成测试

```
手动测试流程：
1. 处理一个视频 → 检查 PDF v2.0 结构是否正确渲染
2. 搜索"异步" → 检查 ChromaDB 是否返回相关视频
3. 处理多个视频 → 检查 topic_graph 是否自动构建
4. Cookie 过期 → 检查告警是否正常触发
```

---

## 七、已完成的文档

| 文档 | 位置 | 说明 |
|------|------|------|
| v2.0 提示词规范 | `docs/prompt-template-v2.md` | 完整 JSON 格式 + 字数要求 + 质量检查清单 |
| 需求确认 | `docs/feature-requirements.md` | 含用户批注的需求文档 |
| 本文档 | `docs/DEVELOPMENT.md` | 完整开发指南 |

---

## 八、版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-05-06 | 初始需求文档 |
| v2.0 | 2026-05-06 | 完整开发文档，整合所有确认需求 |
