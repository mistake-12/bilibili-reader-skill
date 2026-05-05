"""主入口 — 串联所有模块，执行完整的视频总结流程"""

import random
import sys
from pathlib import Path

from .config import Config
from .bilibili_api import BilibiliAPI, FavoriteFolder
from .summarizer import generate_summary
from .pdf_generator import generate_pdf
from .memory import Memory
from .progress import print_progress, calculate_progress, render_mini_progress


def select_folder(folders: list[FavoriteFolder]) -> FavoriteFolder:
    """选择收藏夹（多个时询问用户）"""
    if len(folders) == 1:
        print(f"只有一个收藏夹: {folders[0].title} ({folders[0].media_count}个视频)")
        return folders[0]

    print("\n你的收藏夹列表:")
    for i, f in enumerate(folders, 1):
        print(f"  {i}. {f.title} ({f.media_count}个视频)")

    while True:
        try:
            choice = input("\n请选择收藏夹编号 (输入数字): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(folders):
                return folders[idx]
            print(f"请输入 1-{len(folders)} 之间的数字")
        except ValueError:
            print("请输入有效的数字")
        except (EOFError, KeyboardInterrupt):
            print("\n已取消")
            sys.exit(0)


def pick_random_unprocessed_video(api: BilibiliAPI, folder: FavoriteFolder, memory: Memory):
    """从未处理的视频中随机选一个"""
    # 获取收藏夹内容（多页）
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

    if not all_videos:
        raise Exception(f"收藏夹 '{folder.title}' 中没有视频")

    # 过滤已处理的
    unprocessed = [v for v in all_videos if not memory.is_processed(v.bvid)]

    if not unprocessed:
        raise Exception(f"收藏夹 '{folder.title}' 中的视频都已处理过")

    video = random.choice(unprocessed)
    print(f"\n随机选中: {video.title} (BV: {video.bvid})")
    print(f"  UP主: {video.owner}")
    print(f"  剩余未处理: {len(unprocessed)}/{len(all_videos)}")
    return video


def run(llm_caller=None):
    """执行完整的视频总结流程

    Args:
        llm_caller: LLM调用函数，接收prompt返回response_text
                   如果为None，使用简单总结模式
    """
    # 1. 验证配置
    missing = Config.validate()
    if missing:
        print(f"错误: 缺少配置项: {', '.join(missing)}")
        print("请在 .env 文件中配置B站Cookie")
        print("参考 .env.example")
        return None

    Config.ensure_dirs()

    # 2. 初始化模块
    api = BilibiliAPI(
        sessdata=Config.BILIBILI_SESSDATA,
        bili_jct=Config.BILIBILI_BILI_JCT,
        buvid3=Config.BILIBILI_BUVID3,
    )
    memory = Memory(Config.DATA_DIR / "processed.json")

    print("=" * 50)
    print("B站收藏夹视频智能总结")
    print("=" * 50)
    print(f"已处理视频: {memory.get_processed_count()} 个")

    # 3. 获取收藏夹
    print("\n正在获取收藏夹列表...")
    try:
        folders = api.get_favorites_list()
    except Exception as e:
        print(f"获取收藏夹失败: {e}")
        print("请检查Cookie是否正确且未过期")
        return None

    if not folders:
        print("没有找到收藏夹")
        return None

    # 4. 选择收藏夹
    folder = select_folder(folders)
    print(f"\n已选择: {folder.title}")

    # 5. 随机选视频
    print("\n正在随机选取视频...")
    try:
        video = pick_random_unprocessed_video(api, folder, memory)
    except Exception as e:
        print(f"选取视频失败: {e}")
        return None

    # 6. 获取视频详细信息
    print("\n正在获取视频详情...")
    try:
        video_detail = api.get_video_detail(video.bvid)
    except Exception as e:
        print(f"获取视频详情失败: {e}")
        return None

    # 7. 获取字幕
    subtitles = []
    if video_detail.subtitle_url:
        print("正在下载字幕...")
        try:
            subtitles = api.get_subtitles(video_detail.subtitle_url)
            print(f"  获取到 {len(subtitles)} 条字幕")
        except Exception as e:
            print(f"  字幕获取失败: {e}")
    else:
        print("  该视频没有字幕")

    # 8. 获取高赞评论
    print("正在获取高赞评论...")
    try:
        comments = api.get_top_comments(video_detail.aid, limit=Config.MAX_COMMENTS)
        print(f"  获取到 {len(comments)} 条评论")
    except Exception as e:
        print(f"  评论获取失败: {e}")
        comments = []

    # 9. 获取弹幕
    print("正在获取弹幕...")
    try:
        danmakus = api.get_danmakus(video_detail.cid, limit=Config.MAX_DANMAKUS)
        print(f"  获取到 {len(danmakus)} 条弹幕")
    except Exception as e:
        print(f"  弹幕获取失败: {e}")
        danmakus = []

    # 10. 生成总结
    print("\n正在生成总结...")
    summary = generate_summary(
        video=video_detail,
        subtitles=subtitles,
        comments=comments,
        danmakus=danmakus,
        llm_caller=llm_caller,
    )

    # 11. 记录已处理
    memory.mark_processed(video.bvid, video.title, summary=summary)
    print(f"已记录为已处理视频")

    # 12. 生成PDF
    print("正在生成PDF...")
    progress_stats = calculate_progress(memory, total_in_folder=folder.media_count)
    progress_text = render_mini_progress(progress_stats)
    pdf_path = generate_pdf(summary, Config.OUTPUT_DIR, bvid=video.bvid, progress_text=progress_text)
    print(f"\nPDF已生成: {pdf_path}")

    stats = memory.get_stats()
    print(f"累计处理: {stats['total_processed']} 个视频")

    # 13. 展示考古进度
    print_progress(memory, folder_name=folder.title, total_in_folder=folder.media_count)

    # 14. 推送指令（agent读取后自动推送到对应平台）
    _print_delivery_instruction(pdf_path, summary.title_cn)

    return pdf_path


def _print_delivery_instruction(pdf_path: Path, title: str):
    """输出推送指令，供 agent 解析后投递到对应平台"""
    platform = Config.DELIVERY_PLATFORM.lower()
    if platform == "none" or not platform:
        return

    platform_names = {
        "wechat": "微信",
        "feishu": "飞书",
        "telegram": "Telegram",
        "discord": "Discord",
        "slack": "Slack",
        "whatsapp": "WhatsApp",
    }
    platform_cn = platform_names.get(platform, platform)

    print(f"\n{'='*50}")
    print(f"[DELIVERY] 请将以下内容推送到{platform_cn}:")
    print(f"[DELIVERY] 文件: {pdf_path}")
    print(f"[DELIVERY] 消息: B站视频总结已生成 —— {title}")
    print(f"[DELIVERY] 格式: 发送PDF文件 + 一句话TLDR摘要")
    print(f"{'='*50}")


if __name__ == "__main__":
    run()
