#!/usr/bin/env python3
"""接收 summary JSON，渲染 PDF 并记录到记忆系统

用法:
  python scripts/render_pdf.py summary.json
  echo '{"title_cn":"..."}' | python scripts/render_pdf.py -

输入: JSON 文件路径或 - (从 stdin 读取)
输出: PDF 文件路径到 stdout
"""

import sys
import json
from pathlib import Path

skill_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skill_dir))

from src.config import Config
from src.summarizer import VideoSummary
from src.pdf_generator import generate_pdf
from src.memory import Memory
from src.progress import calculate_progress, render_mini_progress


def main():
    if len(sys.argv) < 2:
        print("用法: python render_pdf.py <summary.json>", file=sys.stderr)
        sys.exit(1)

    # 读取 JSON
    arg = sys.argv[1]
    if arg == "-":
        raw = sys.stdin.read()
    else:
        path = Path(arg)
        if not path.exists():
            print(f"错误: 文件不存在 {arg}", file=sys.stderr)
            sys.exit(1)
        raw = path.read_text(encoding="utf-8")

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 {e}", file=sys.stderr)
        sys.exit(1)

    # 构建 VideoSummary
    summary = VideoSummary(
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
        prerequisites_cn=data.get("prerequisites_cn", ""),
        prerequisites_en=data.get("prerequisites_en", ""),
        difficulty_cn=data.get("difficulty_cn", ""),
        difficulty_en=data.get("difficulty_en", ""),
        next_steps_cn=data.get("next_steps_cn", ""),
        next_steps_en=data.get("next_steps_en", ""),
        key_misconceptions_cn=data.get("key_misconceptions_cn", ""),
        key_misconceptions_en=data.get("key_misconceptions_en", ""),
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
        owner=data.get("owner", ""),
        duration_str=data.get("duration_str", ""),
        view_count=data.get("view_count", 0),
        like_count=data.get("like_count", 0),
        genre=data.get("genre", ""),
    )

    Config.ensure_dirs()

    # 记忆系统
    bvid = data.get("bvid", "")
    memory = Memory(Config.DATA_DIR / "processed.json")
    folder_name = data.get("folder_name", "")
    folder_total = data.get("folder_total", 0)

    # 生成 PDF
    progress_stats = calculate_progress(memory, total_in_folder=folder_total)
    progress_text = render_mini_progress(progress_stats)
    pdf_path = generate_pdf(summary, Config.OUTPUT_DIR, bvid=bvid, progress_text=progress_text)

    # 记录已处理
    if bvid:
        memory.mark_processed(bvid, summary.title_cn, summary=summary)

    # 输出 PDF 路径
    print(str(pdf_path))


if __name__ == "__main__":
    main()
