"""允许通过 python -m src 运行"""

import sys


def main():
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
        run()


if __name__ == "__main__":
    main()
