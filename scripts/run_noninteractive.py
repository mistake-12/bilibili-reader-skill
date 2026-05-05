#!/usr/bin/env python3
"""非交互式视频总结脚本 — 绕过 main.py 的 input() 问题

用法: cd ~/.hermes/skills/media/bilibili-reader && .venv/bin/python scripts/run_noninteractive.py <收藏夹名称> [latest|random|search <keyword>|<bvid>]

参数:
  收藏夹名称     目标收藏夹标题（精确匹配）
  latest         最新收藏的未处理视频（收藏时间最近，默认）
  random         随机选一个未处理视频
  search <keyword> 搜索已总结记录和未处理视频
  <bvid>         指定 BV 号

示例:
  .venv/bin/python scripts/run_noninteractive.py 代码 latest
  .venv/bin/python scripts/run_noninteractive.py 代码 random
  .venv/bin/python scripts/run_noninteractive.py 代码 search python
  .venv/bin/python scripts/run_noninteractive.py 代码 BV1ZPttzhEDV
"""

import sys, json, random
from pathlib import Path
from datetime import datetime

# 确保能导入 skill 模块
skill_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skill_dir))

from src.config import Config
from src.bilibili_api import BilibiliAPI
from src.summarizer import generate_summary
from src.pdf_generator import generate_pdf
from src.memory import Memory
from src.progress import print_progress, calculate_progress, render_mini_progress


def main():
    if len(sys.argv) < 2:
        print("用法: python run_noninteractive.py <收藏夹名称> [random|<bvid>]")
        sys.exit(1)

    folder_name = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "latest"

    # 验证配置
    missing = Config.validate()
    if missing:
        print(f"错误: 缺少配置项: {', '.join(missing)}")
        sys.exit(1)

    Config.ensure_dirs()
    api = BilibiliAPI(Config.BILIBILI_SESSDATA, Config.BILIBILI_BILI_JCT, Config.BILIBILI_BUVID3)
    memory = Memory(Config.DATA_DIR / "processed.json")

    print("=" * 50)
    print("B站收藏夹视频智能总结 (非交互模式)")
    print("=" * 50)

    # 获取收藏夹
    folders = api.get_favorites_list()
    folder = None
    for f in folders:
        if f.title == folder_name:
            folder = f
            break

    if not folder:
        print(f"错误: 找不到收藏夹 '{folder_name}'")
        print(f"可用收藏夹: {', '.join(f.title for f in folders)}")
        sys.exit(1)

    print(f"收藏夹: {folder.title} ({folder.media_count}个视频)")

    # 获取视频列表
    all_videos = []
    page = 1
    while True:
        videos = api.get_videos_from_folder(folder.id, page=page, page_size=20)
        if not videos:
            break
        all_videos.extend(videos)
        if len(videos) < 20:
            break
        page += 1

    # 选择视频
    if mode == "latest":
        # 最新收藏：取收藏时间最近的未处理视频（列表第一个）
        unprocessed = [v for v in all_videos if not memory.is_processed(v.bvid)]
        if not unprocessed:
            print("所有视频都已处理过")
            sys.exit(0)
        video_brief = unprocessed[0]
        print(f"最新收藏: {video_brief.title} ({video_brief.bvid})")
    elif mode == "random":
        unprocessed = [v for v in all_videos if not memory.is_processed(v.bvid)]
        if not unprocessed:
            print("所有视频都已处理过")
            sys.exit(0)
        video_brief = random.choice(unprocessed)
        print(f"随机选中: {video_brief.title} ({video_brief.bvid})")
    elif mode == "search":
        keyword = " ".join(sys.argv[3:]) if len(sys.argv) > 3 else ""
        if not keyword:
            print("错误: search 模式需要提供搜索关键词")
            print("用法: python run_noninteractive.py <收藏夹名称> search <keyword>")
            sys.exit(1)

        # 搜索已总结记录
        memory_results = memory.search_by_keyword(keyword)
        if memory_results:
            print(f"\n在已总结记录中找到 {len(memory_results)} 个匹配:")
            for v in memory_results:
                print(f"  [{v.genre}] {v.title} ({v.bvid})")
                if v.tldr_cn:
                    print(f"    TLDR: {v.tldr_cn}")
                if v.key_points_cn:
                    print(f"    要点: {', '.join(v.key_points_cn[:3])}")
        else:
            print(f"\n已总结记录中没有匹配 '{keyword}' 的视频")

        # 搜索收藏夹未处理视频
        folder_matches = [v for v in all_videos
                          if not memory.is_processed(v.bvid)
                          and keyword.lower() in v.title.lower()]
        if folder_matches:
            print(f"\n在收藏夹未处理视频中找到 {len(folder_matches)} 个匹配:")
            for v in folder_matches[:10]:
                print(f"  {v.title} ({v.bvid}) - UP主: {v.owner}")
        else:
            print(f"\n收藏夹未处理视频中没有标题匹配 '{keyword}' 的视频")

        sys.exit(0)
    else:
        video_brief = next((v for v in all_videos if v.bvid == mode), None)
        if not video_brief:
            print(f"错误: 收藏夹中找不到 {mode}")
            sys.exit(1)
        print(f"指定视频: {video_brief.title} ({video_brief.bvid})")

    # 获取详情
    print("\n获取视频详情...")
    video = api.get_video_detail(video_brief.bvid)

    # 字幕
    subtitles = []
    if video.subtitle_url:
        print("下载字幕...")
        try:
            subtitles = api.get_subtitles(video.subtitle_url)
            print(f"  获取到 {len(subtitles)} 条字幕")
        except Exception as e:
            print(f"  字幕获取失败: {e}")
    else:
        print("  该视频没有字幕（将基于简介和评论生成总结）")

    # 评论
    print("获取高赞评论...")
    try:
        comments = api.get_top_comments(video.aid, limit=Config.MAX_COMMENTS)
        print(f"  获取到 {len(comments)} 条评论")
    except Exception as e:
        print(f"  评论获取失败: {e}")
        comments = []

    # 弹幕
    print("获取弹幕...")
    try:
        danmakus = api.get_danmakus(video.cid, limit=Config.MAX_DANMAKUS)
        print(f"  获取到 {len(danmakus)} 条弹幕")
    except Exception as e:
        print(f"  弹幕获取失败: {e}")
        danmakus = []

    # 生成总结
    print("\n生成总结...")
    summary = generate_summary(
        video=video,
        subtitles=subtitles,
        comments=comments,
        danmakus=danmakus,
        llm_caller=None,  # 使用简单总结模式；传入 LLM 函数可生成更好的总结
    )

    # 记录
    memory.mark_processed(video.bvid, video.title, summary=summary)
    print("已记录为已处理视频")

    # 生成PDF
    print("生成PDF...")
    progress_stats = calculate_progress(memory, total_in_folder=folder.media_count)
    progress_text = render_mini_progress(progress_stats)
    pdf_path = generate_pdf(summary, Config.OUTPUT_DIR, bvid=video.bvid, progress_text=progress_text)
    print(f"\nPDF已生成: {pdf_path}")
    print(f"文件大小: {pdf_path.stat().st_size / 1024:.1f} KB")

    # 考古进度
    print_progress(memory, folder_name=folder.title, total_in_folder=folder.media_count)


if __name__ == "__main__":
    main()
