"""允许通过 python -m src 运行"""

import sys


def main():
    # 透传所有参数给 main.run()（包含 --search, --stats 等）
    if "--login" in sys.argv:
        from .setup import run_setup
        run_setup(skip_cookies=False)
    elif "--config" in sys.argv:
        from .setup import run_setup
        run_setup(skip_cookies=True)
    elif "--progress" in sys.argv:
        from .config import Config
        from .memory import Memory
        from .progress import print_progress
        memory = Memory(Config.DATA_DIR / "processed.json")
        print_progress(memory)
    else:
        from .main import run
        import argparse
        parser = argparse.ArgumentParser(description="B站收藏夹视频智能总结")
        parser.add_argument("--search", "-s", metavar="QUERY", dest="search_query")
        parser.add_argument("--stats", action="store_true")
        args = parser.parse_known_args()[0]
        run(args=args)
