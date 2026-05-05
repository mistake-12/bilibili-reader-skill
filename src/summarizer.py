"""LLM总结模块 — 意图路由 + 体裁专用提示词 + 分段摘要"""

import json
from dataclasses import dataclass, field
from .bilibili_api import VideoInfo, Comment, Danmaku
from .intent_router import (
    VideoGenre, GENRE_DISPLAY,
    classify_genre, get_prompt_for_genre,
)


@dataclass
class VideoSummary:
    """视频总结数据结构（升级版）"""
    # 基本信息
    title_cn: str
    title_en: str
    owner: str
    duration_str: str
    view_count: int
    like_count: int
    # 体裁
    genre: str = ""
    # 核心内容
    tldr_cn: str = ""
    tldr_en: str = ""
    summary_cn: str = ""
    summary_en: str = ""
    key_points_cn: list[str] = field(default_factory=list)
    key_points_en: list[str] = field(default_factory=list)
    # 技术教程专用字段
    tool_stack: list[dict] = field(default_factory=list)     # [{name, purpose, barrier}]
    code_snippets: list[dict] = field(default_factory=list)  # [{lang, code, context}]
    pitfalls_cn: list[str] = field(default_factory=list)
    pitfalls_en: list[str] = field(default_factory=list)
    # 洞察
    insights_cn: str = ""
    insights_en: str = ""
    # 评论
    top_comments: list[dict] = field(default_factory=list)
    # 推荐
    recommendation_cn: str = ""
    recommendation_en: str = ""
    # 通用学习导向字段
    prerequisites_cn: str = ""
    prerequisites_en: str = ""
    difficulty_cn: str = ""
    difficulty_en: str = ""
    next_steps_cn: str = ""
    next_steps_en: str = ""
    key_misconceptions_cn: str = ""
    key_misconceptions_en: str = ""
    # 体裁专用字段
    expected_outcome_cn: str = ""      # 技术教程：验证步骤
    expected_outcome_en: str = ""
    exam_format_cn: str = ""           # 学科教育：考试出题形式
    exam_format_en: str = ""
    vocabulary_list: list = field(default_factory=list)  # 语言学习 [{word, meaning, example}]
    data_sources_cn: str = ""          # 深度解析：引用数据来源
    data_sources_en: str = ""
    practice_template_cn: str = ""     # 方法论：填空式练习模板
    practice_template_en: str = ""
    scripts_templates: list = field(default_factory=list) # 职场 [{scenario, script}]
    reference_works_cn: str = ""       # 创意：参考作品
    reference_works_en: str = ""
    key_quotes: list = field(default_factory=list)        # 书籍 [{quote, context}]
    materials_list: list = field(default_factory=list)    # 生活 [{item, purpose, cost_estimate}]
    related_topics_cn: str = ""        # 通用：相关话题
    related_topics_en: str = ""


def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_count(count: int) -> str:
    if count >= 10000:
        return f"{count / 10000:.1f}万"
    return str(count)


# ──────────────────────────────────────────────
# 字幕分段 + 重叠 + 概括
# ──────────────────────────────────────────────

CHUNK_DURATION = 600       # 每段10分钟
OVERLAP_DURATION = 60      # 重叠区60秒


def chunk_subtitles(subtitles: list[dict], chunk_sec: int = CHUNK_DURATION, overlap_sec: int = OVERLAP_DURATION) -> list[list[dict]]:
    """将字幕按时间切片，相邻切片之间留重叠区防止断句"""
    if not subtitles:
        return []
    subs = sorted(subtitles, key=lambda s: s.get("from", 0))
    total_dur = subs[-1].get("from", 0) + 5
    if total_dur <= 0:
        return [subs]
    chunks = []
    start = 0
    while start < total_dur:
        end = start + chunk_sec
        chunk = [s for s in subs if s.get("from", 0) >= start and s.get("from", 0) < end]
        if chunk:
            chunks.append(chunk)
        start += chunk_sec - overlap_sec
    return chunks


def summarize_subtitle_chunk(chunk: list[dict], llm_caller, chunk_idx: int, total_chunks: int) -> str:
    text = "\n".join(s.get("content", "") for s in chunk)
    prompt = f"""请用中文概括以下B站视频字幕片段的核心内容（这是第{chunk_idx+1}/{total_chunks}段）。
要求：提炼关键信息，保留技术术语、操作步骤、关键结论，控制在200-400字。

字幕内容：
{text}"""
    return llm_caller(prompt)


def summarize_subtitles_with_chunking(subtitles: list[dict], duration_sec: int, llm_caller=None) -> str:
    """根据视频时长选择字幕处理策略"""
    if not subtitles:
        return ""
    if not llm_caller:
        return "\n".join(s.get("content", "") for s in subtitles[:200])

    if duration_sec < 1800:
        # < 30分钟：一次性概括
        text = "\n".join(s.get("content", "") for s in subtitles)
        prompt = f"""请用中文概括以下B站视频字幕的核心内容。
要求：提炼关键信息，保留技术术语、操作步骤、关键结论，控制在300-500字。

字幕内容：
{text}"""
        return llm_caller(prompt)

    # >= 30分钟：分段 + 重叠
    chunks = chunk_subtitles(subtitles)
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        summary = summarize_subtitle_chunk(chunk, llm_caller, i, len(chunks))
        chunk_summaries.append(summary)
    return "\n\n".join(f"【第{i+1}段】{s}" for i, s in enumerate(chunk_summaries))


# ──────────────────────────────────────────────
# 主流程
# ──────────────────────────────────────────────

def generate_summary(
    video: VideoInfo,
    subtitles: list[dict],
    comments: list[Comment],
    danmakus: list[Danmaku],
    llm_caller=None,
) -> VideoSummary:
    """生成视频总结（意图路由 + 体裁专用提示词）"""

    # 超长视频警告
    if video.duration > 3600:
        print(f"⚠ 警告: 视频时长 {format_duration(video.duration)}，处理时间可能较长")

    # 1. 概括字幕
    print("  概括字幕内容...")
    subtitle_summary = summarize_subtitles_with_chunking(subtitles, video.duration, llm_caller)

    # 2. 意图路由 — 判断体裁
    genre = VideoGenre.GENERIC
    if llm_caller:
        subtitle_sample = "\n".join(s.get("content", "") for s in subtitles[:200])
        print("  判断视频体裁...")
        genre = classify_genre(video.title, video.desc, subtitle_sample, llm_caller)
        print(f"  体裁: {GENRE_DISPLAY.get(genre, genre)}")
    else:
        genre = VideoGenre.GENERIC

    # 3. 构建 prompt
    comment_text = ""
    if comments:
        comment_text = "\n".join(
            f"- [{c.like}赞] {c.uname}: {c.content[:200]}" for c in comments
        )
    danmaku_text = ""
    if danmakus:
        danmaku_text = "\n".join(d.content for d in danmakus[:30])

    prompt_template = get_prompt_for_genre(genre)
    prompt = prompt_template.format(
        title=video.title,
        desc=video.desc[:500],
        duration=format_duration(video.duration),
        owner=video.owner,
        subtitle_summary=subtitle_summary or "（无字幕）",
        comments=comment_text or "（无评论）",
        danmakus=danmaku_text or "（无弹幕）",
    )

    # 4. 调用 LLM
    if llm_caller:
        print("  生成结构化总结...")
        response = llm_caller(prompt)
        summary = _parse_response(response)
    else:
        summary = VideoSummary(
            title_cn=video.title,
            title_en=video.title,
            tldr_cn=f"视频《{video.title}》由{video.owner}发布",
            tldr_en=f"Video '{video.title}' by {video.owner}",
            summary_cn=f"时长{format_duration(video.duration)}，播放量{format_count(video.view)}。{video.desc[:200]}",
            summary_en=f"Duration {format_duration(video.duration)}, {format_count(video.view)} views. {video.desc[:200]}",
        )

    # 5. 填充基本信息
    summary.owner = video.owner
    summary.duration_str = format_duration(video.duration)
    summary.view_count = video.view
    summary.like_count = video.like
    summary.genre = GENRE_DISPLAY.get(genre, "📚 通用知识")

    return summary


def _parse_response(response_text: str) -> VideoSummary:
    """解析LLM返回的JSON"""
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()

    data = json.loads(text)

    return VideoSummary(
        title_cn=data.get("title_cn", ""),
        title_en=data.get("title_en", ""),
        tldr_cn=data.get("tldr_cn", ""),
        tldr_en=data.get("tldr_en", ""),
        summary_cn=data.get("summary_cn", ""),
        summary_en=data.get("summary_en", ""),
        key_points_cn=data.get("key_points_cn", []),
        key_points_en=data.get("key_points_en", []),
        tool_stack=data.get("tool_stack", []),
        code_snippets=data.get("code_snippets", []),
        pitfalls_cn=data.get("pitfalls_cn", []),
        pitfalls_en=data.get("pitfalls_en", []),
        insights_cn=data.get("insights_cn", ""),
        insights_en=data.get("insights_en", ""),
        top_comments=data.get("top_comments", []),
        recommendation_cn=data.get("recommendation_cn", ""),
        recommendation_en=data.get("recommendation_en", ""),
        # 通用学习导向字段
        prerequisites_cn=data.get("prerequisites_cn", ""),
        prerequisites_en=data.get("prerequisites_en", ""),
        difficulty_cn=data.get("difficulty_cn", ""),
        difficulty_en=data.get("difficulty_en", ""),
        next_steps_cn=data.get("next_steps_cn", ""),
        next_steps_en=data.get("next_steps_en", ""),
        key_misconceptions_cn=data.get("key_misconceptions_cn", ""),
        key_misconceptions_en=data.get("key_misconceptions_en", ""),
        # 体裁专用字段
        expected_outcome_cn=data.get("expected_outcome_cn", ""),
        expected_outcome_en=data.get("expected_outcome_en", ""),
        exam_format_cn=data.get("exam_format_cn", ""),
        exam_format_en=data.get("exam_format_en", ""),
        vocabulary_list=data.get("vocabulary_list", []),
        data_sources_cn=data.get("data_sources_cn", ""),
        data_sources_en=data.get("data_sources_en", ""),
        practice_template_cn=data.get("practice_template_cn", ""),
        practice_template_en=data.get("practice_template_en", ""),
        scripts_templates=data.get("scripts_templates", []),
        reference_works_cn=data.get("reference_works_cn", ""),
        reference_works_en=data.get("reference_works_en", ""),
        key_quotes=data.get("key_quotes", []),
        materials_list=data.get("materials_list", []),
        related_topics_cn=data.get("related_topics_cn", ""),
        related_topics_en=data.get("related_topics_en", ""),
    )
