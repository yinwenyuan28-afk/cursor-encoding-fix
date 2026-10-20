"""Write a Chinese probe file and print on-disk encoding evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "mcp") not in sys.path:
    sys.path.insert(0, str(ROOT / "mcp"))

import server  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--path",
        default=str(Path.cwd() / "_cursor_encoding_fix_probe.txt"),
        help="Absolute path for the probe file",
    )
    args = parser.parse_args()
    path = Path(args.path)
    if not path.is_absolute():
        print("error: --path must be absolute", file=sys.stderr)
        return 2

    sample = "编码探针：岗位发布与收费\n"
    msg = server.tool_write({"path": str(path), "contents": sample})
    raw = path.read_bytes()
    print(msg)
    print("hex", raw.hex(" "))
    print("bom", raw.startswith(b"\xef\xbb\xbf"))
    try:
        text = raw.decode("utf-8")
        print("utf8_ok", repr(text))
    except UnicodeDecodeError as exc:
        print("utf8_fail", exc)
        return 1
    try:
        raw.decode("gbk")
        print("also_decodes_as_gbk", True)
    except UnicodeDecodeError:
        print("also_decodes_as_gbk", False)
    expect = sample.encode("utf-8")
    ok = raw == expect
    print("match_utf8_exact", ok)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
