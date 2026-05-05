"""B站扫码登录 — 替代手动复制Cookie"""

import json
import time
import webbrowser
import subprocess
import requests
from pathlib import Path
from typing import Optional


LOGIN_API = "https://passport.bilibili.com/x/passport-login/web"
NAV_API = "https://api.bilibili.com/x/web-interface/nav"

# 扫码状态码
STATUS_READY = 0       # 未扫描
STATUS_SCANNED = 86101  # 已扫描，未确认
STATUS_CONFIRMED = 86090  # 已确认
STATUS_EXPIRED = 86038   # 二维码过期


def generate_qrcode() -> tuple[str, str]:
    """生成二维码，返回 (qrcode_url, qrcode_key)"""
    url = f"{LOGIN_API}/qrcode/generate"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.ConnectionError, requests.Timeout):
        data = _curl_get(url)

    if data.get("code") != 0:
        raise Exception(f"生成二维码失败: {data.get('message', 'unknown')}")

    qr_data = data["data"]
    return qr_data["url"], qr_data["qrcode_key"]


def poll_qrcode_status(qrcode_key: str) -> tuple[int, dict]:
    """轮询扫码状态，返回 (status_code, response_data)"""
    url = f"{LOGIN_API}/qrcode/poll"
    params = {"qrcode_key": qrcode_key}
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except (requests.ConnectionError, requests.Timeout):
        data = _curl_get(url, params)

    code = data.get("data", {}).get("code", -1)
    return code, data.get("data", {})


def extract_cookies_from_response(resp_data: dict) -> dict[str, str]:
    """从登录成功的响应中提取Cookie"""
    cookies = {}
    # 从 set-cookie 中提取
    cookie_info = resp_data.get("cookie_info", {})
    if cookie_info:
        for c in cookie_info.get("cookies", []):
            name = c.get("name", "")
            value = c.get("value", "")
            if name in ("SESSDATA", "bili_jct", "buvid3"):
                cookies[name] = value

    # 如果 cookie_info 没有，尝试从 url 字段解析（重定向URL中可能带cookie）
    if not cookies and "url" in resp_data:
        # 有些版本的API返回的是重定向URL
        pass

    return cookies


def login_with_qrcode(save_to_env: bool = True) -> Optional[dict[str, str]]:
    """完整的扫码登录流程

    Args:
        save_to_env: 是否自动保存到 .env 文件

    Returns:
        成功返回 {"SESSDATA": "...", "bili_jct": "...", "buvid3": "..."}, 失败返回 None
    """
    print("=" * 50)
    print("B站扫码登录")
    print("=" * 50)

    # 1. 生成二维码
    print("\n正在生成二维码...")
    try:
        qr_url, qr_key = generate_qrcode()
    except Exception as e:
        print(f"生成二维码失败: {e}")
        return None

    print(f"二维码链接: {qr_url}")
    print("\n正在打开浏览器...")

    # 2. 打开浏览器
    try:
        webbrowser.open(qr_url)
        print("浏览器已打开，请用B站APP扫描二维码")
    except Exception:
        print(f"无法自动打开浏览器，请手动访问:\n{qr_url}")

    print("\n等待扫码中...")

    # 3. 轮询状态
    max_wait = 180  # 最多等3分钟
    start_time = time.time()
    last_status = None

    while time.time() - start_time < max_wait:
        try:
            status, data = poll_qrcode_status(qr_key)
        except Exception as e:
            print(f"\n轮询出错: {e}")
            time.sleep(2)
            continue

        if status != last_status:
            if status == STATUS_READY:
                print("  等待扫描...", end="\r")
            elif status == STATUS_SCANNED:
                print("  已扫描，请在手机上确认登录")
            elif status == STATUS_CONFIRMED:
                print("  已确认，正在获取Cookie...")
            elif status == STATUS_EXPIRED:
                print("\n二维码已过期，请重新运行")
                return None
            last_status = status

        if status == STATUS_CONFIRMED:
            cookies = extract_cookies_from_response(data)
            if cookies:
                print("\n登录成功!")
                print(f"  SESSDATA: {cookies.get('SESSDATA', '')[:20]}...")
                print(f"  bili_jct: {cookies.get('bili_jct', '')[:20]}...")
                print(f"  buvid3:   {cookies.get('buvid3', '')[:20]}...")

                if save_to_env:
                    _save_to_env(cookies)
                    print(f"\nCookie已保存到 .env 文件")

                return cookies
            else:
                print("\n登录成功但未获取到Cookie，可能需要手动设置")
                return None

        time.sleep(2)

    print("\n等待超时，请重新运行")
    return None


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


def _curl_get(url: str, params: dict = None) -> dict:
    """curl fallback（处理沙箱DNS问题）"""
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    result = subprocess.run(
        ["curl", "-s", "--connect-timeout", "10", url],
        capture_output=True, text=True, timeout=15,
    )
    if not result.stdout.strip():
        raise Exception(f"curl请求无响应: {url}")
    return json.loads(result.stdout)


if __name__ == "__main__":
    login_with_qrcode()
