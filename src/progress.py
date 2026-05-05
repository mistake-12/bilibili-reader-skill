"""收藏夹考古 — 进度可视化"""

from dataclasses import dataclass, field
from .memory import Memory


@dataclass
class ProgressStats:
    total_processed: int = 0
    total_in_folder: int = 0
    percentage: float = 0.0
    genres: dict[str, int] = field(default_factory=dict)  # {genre_display: count}
    streak_days: int = 0
    top_genres: list[tuple[str, int]] = field(default_factory=list)


def calculate_progress(memory: Memory, total_in_folder: int = 0) -> ProgressStats:
    """计算进度统计"""
    processed = memory.get_all_processed()
    total = len(processed)

    # 统计体裁分布
    genres: dict[str, int] = {}
    for v in processed:
        g = v.genre or "📚 未知"
        genres[g] = genres.get(g, 0) + 1

    # 按数量排序
    top_genres = sorted(genres.items(), key=lambda x: x[1], reverse=True)

    # 计算百分比
    percentage = 0.0
    if total_in_folder > 0:
        percentage = (total / total_in_folder) * 100

    return ProgressStats(
        total_processed=total,
        total_in_folder=total_in_folder,
        percentage=percentage,
        genres=genres,
        top_genres=top_genres,
    )


def render_progress(stats: ProgressStats, folder_name: str = "") -> str:
    """渲染命令行进度展示"""
    lines = []
    lines.append("")
    lines.append("=" * 50)
    lines.append("  🗺️  收藏夹考古进度")
    if folder_name:
        lines.append(f"  📁 收藏夹: {folder_name}")
    lines.append("=" * 50)

    # 进度条
    if stats.total_in_folder > 0:
        bar_width = 30
        filled = int(bar_width * stats.percentage / 100)
        empty = bar_width - filled
        bar = "█" * filled + "░" * empty
        lines.append(f"\n  {bar}  {stats.percentage:.0f}%")
        lines.append(f"  已消化 {stats.total_processed}/{stats.total_in_folder} 个视频")
    else:
        lines.append(f"\n  已消化 {stats.total_processed} 个视频")

    # 体裁分布
    if stats.top_genres:
        lines.append("\n  📊 知识图谱:")
        max_count = stats.top_genres[0][1] if stats.top_genres else 1
        for genre, count in stats.top_genres:
            bar_len = int(15 * count / max_count) if max_count > 0 else 1
            bar = "█" * bar_len
            lines.append(f"    {genre:<16} {bar} {count}")

    # 成就系统
    achievements = _check_achievements(stats)
    if achievements:
        lines.append("\n  🏆 成就:")
        for ach in achievements:
            lines.append(f"    {ach}")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)


def render_mini_progress(stats: ProgressStats) -> str:
    """渲染迷你进度条（用于PDF底部等空间有限的地方）"""
    if stats.total_in_folder > 0:
        bar_width = 20
        filled = int(bar_width * stats.percentage / 100)
        empty = bar_width - filled
        bar = "█" * filled + "░" * empty
        return f"收藏夹考古: {bar} {stats.percentage:.0f}% ({stats.total_processed}/{stats.total_in_folder})"
    return f"收藏夹考古: 已消化 {stats.total_processed} 个视频"


def _check_achievements(stats: ProgressStats) -> list[str]:
    """检查解锁的成就"""
    achievements = []
    total = stats.total_processed

    # 数量成就
    milestones = [
        (1, "🌱 初次发掘 — 消化了第一个视频"),
        (5, "🔍 考古新手 — 消化 5 个视频"),
        (10, "⛏️ 考古学徒 — 消化 10 个视频"),
        (25, "🗺️ 地图绘制者 — 消化 25 个视频"),
        (50, "🏛️ 知识守护者 — 消化 50 个视频"),
        (100, "👑 收藏夹征服者 — 消化 100 个视频"),
    ]
    for threshold, desc in milestones:
        if total >= threshold:
            achievements.append(desc)

    # 体裁成就
    genre_achievements = {
        "💻": ("🔧 技术工匠", "技术教程类消化 5+ 个"),
        "🎓": ("📖 学霸", "学科教育类消化 5+ 个"),
        "🗣️": ("🌍 语言达人", "语言学习类消化 5+ 个"),
        "🔬": ("🧪 深度思考者", "深度解析类消化 5+ 个"),
        "🧠": ("💡 方法论大师", "方法论类消化 5+ 个"),
        "💼": ("👔 职场达人", "职场技能类消化 5+ 个"),
        "🎨": ("🎨 创意工匠", "艺术创造类消化 5+ 个"),
        "📖": ("📚 知识管理师", "书籍拆解类消化 5+ 个"),
        "🛠️": ("🔧 生活达人", "生活技能类消化 5+ 个"),
    }
    for genre, count in stats.genres.items():
        for prefix, (name, req) in genre_achievements.items():
            if prefix in genre and count >= 5:
                achievements.append(f"{name} — {req}")

    # 多样性成就
    if len(stats.genres) >= 5:
        achievements.append("🌈 博览群书 — 覆盖 5+ 种体裁")
    if len(stats.genres) >= 8:
        achievements.append("🎯 全能选手 — 覆盖 8+ 种体裁")

    return achievements


def print_progress(memory: Memory, folder_name: str = "", total_in_folder: int = 0):
    """直接打印进度"""
    stats = calculate_progress(memory, total_in_folder)
    print(render_progress(stats, folder_name))
