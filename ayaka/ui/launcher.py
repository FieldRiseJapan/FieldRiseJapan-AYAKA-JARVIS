import argparse

from .monitors import discover_layout


def build_parser():
    parser = argparse.ArgumentParser(description="AYAKA JARVIS v0.2 three-monitor UI")
    parser.add_argument("--print-layout", action="store_true", help="Print detected monitor roles and exit")
    return parser


def main(args=None):
    parsed = args or build_parser().parse_args()
    layout = discover_layout()
    if parsed.print_layout:
        for role, monitor in (("LEFT", layout.left), ("CENTER", layout.center), ("RIGHT", layout.right)):
            print(f"{role}: {monitor.name} {monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        return 0
    from .app import JarvisUiApp
    JarvisUiApp(layout=layout).run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
