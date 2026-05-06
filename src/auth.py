"""B站登录 — 浏览器扫码 + Cookie提取"""

import webbrowser
from pathlib import Path
from typing import Optional


def login_via_browser(save_to_env: bool = True) -> Optional[dict[str, str]]:
    """通过浏览器登录B站并提取Cookie

    打开B站登录页面，用户扫码后，粘贴浏览器控制台输出的Cookie字符串。

    Args:
        save_to_env: 是否自动保存到 .env 文件

    Returns:
        成功返回 {"SESSDATA": "...", "bili_jct": "...", "buvid3": "..."}, 失败返回 None
    """
    print("=" * 50)
    print("B站登录")
    print("=" * 50)

    # 1. 打开B站登录页
    login_url = "https://passport.bilibili.com/login"
    print(f"\n正在打开浏览器...")
    try:
        webbrowser.open(login_url)
    except Exception:
        pass

    print(f"如果浏览器没有自动打开，请手动访问:\n{login_url}")
    print()
    print("── 操作步骤 ──")
    print("1. 在浏览器中用B站APP扫码登录")
    print("2. 登录成功后，按 F12 打开开发者工具")
    print("3. 切换到「控制台」(Console) 标签")
    print("4. 粘贴以下命令并回车：")
    print()
    print('   document.cookie.split(";").filter(c=>/SESSDATA|bili_jct|buvid3/.test(c.trim().split("=")[0])).map(c=>c.trim()).join("\\n")')
    print()
    print("5. 复制输出的结果，粘贴到下面")
    print()

    # 2. 等待用户粘贴
    print("请粘贴控制台输出的 Cookie（每行一个 key=value）：")
    print("（直接回车跳过，稍后手动配置 .env）")
    print()

    lines = []
    try:
        while True:
            line = input().strip()
            if not line:
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        print("\n已取消")
        return None

    if not lines:
        print("未输入Cookie，跳过配置")
        return None

    # 3. 解析 Cookie
    cookies = {}
    for line in lines:
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            # 去掉可能的前缀空格和引号
            value = value.strip().strip('"').strip("'")
            if key in ("SESSDATA", "bili_jct", "buvid3"):
                cookies[key] = value

    if not cookies:
        print("未识别到有效的Cookie字段（需要 SESSDATA、bili_jct、buvid3）")
        return None

    missing = [k for k in ("SESSDATA", "bili_jct", "buvid3") if k not in cookies]
    if missing:
        print(f"警告: 缺少以下字段: {', '.join(missing)}")
        print("请确认控制台命令输出了这三项")

    # 4. 显示结果
    print(f"\n登录成功!")
    for k, v in cookies.items():
        print(f"  {k}: {v[:20]}...")

    if save_to_env:
        _save_to_env(cookies)
        print(f"\nCookie已保存到 .env 文件")

    return cookies


def _save_to_env(cookies: dict[str, str]):
    """将Cookie保存到 .env 文件"""
    env_path = Path(__file__).parent.parent / ".env"

    # 读取现有内容
    existing = {}
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    existing[key.strip()] = value.strip()

    # 更新Cookie
    existing["BILIBILI_SESSDATA"] = cookies.get("SESSDATA", "")
    existing["BILIBILI_BILI_JCT"] = cookies.get("bili_jct", "")
    existing["BILIBILI_BUVID3"] = cookies.get("buvid3", "")

    # 写回
    with open(env_path, "w", encoding="utf-8") as f:
        for key, value in existing.items():
            f.write(f"{key}={value}\n")


if __name__ == "__main__":
    login_via_browser()
