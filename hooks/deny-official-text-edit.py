"""Deny official Write/StrReplace/Edit, except image file saves.

The hook matcher already limits this script to those three tools.
Do not allow when stdin is empty or unreadable; that path was letting
the official tools through.

Image saves are allowed only for Write targets whose path ends in an
image extension. StrReplace and Edit stay denied.
Cursor sends hook input as UTF-8 with a BOM, so the payload is decoded
as utf-8-sig before JSON parsing.
"""

import json
import os
import sys

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".ico",
    ".avif",
}

PATH_KEYS = (
    "path",
    "file_path",
    "filePath",
    "target_file",
    "filename",
    "uri",
)


def emit(payload):
    sys.stdout.buffer.write(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")


def deny():
    emit(
        {
            "permission": "deny",
            "user_message": "官方写入会把中文存成 GBK，已改走 utf8-files。",
            "agent_message": (
                "Official Write, StrReplace, and Edit are blocked on this machine "
                "because they save Chinese as GBK. Use MCP server utf8-files instead: "
                "read_utf8(path), write_utf8(path, contents), "
                "edit_utf8(path, old_string, new_string, replace_all). "
                "Paths must be absolute. "
                "Load the schema with GetDynamicTools namespace user-utf8-files before calling. "
                "Write is allowed when the target path ends with an image extension "
                "(png, jpg, jpeg, gif, webp, bmp, ico, avif)."
            ),
        }
    )


def allow():
    emit({"permission": "allow"})


def collect_paths(value, found):
    if isinstance(value, dict):
        for key, item in value.items():
            if key in PATH_KEYS and isinstance(item, str):
                found.append(item)
            else:
                collect_paths(item, found)
    elif isinstance(value, list):
        for item in value:
            collect_paths(item, found)


def is_image_path(path):
    cleaned = path.split("?", 1)[0].split("#", 1)[0].rstrip("\\/")
    return os.path.splitext(cleaned)[1].lower() in IMAGE_EXTENSIONS


def load_payload(raw):
    if not raw.strip():
        return None
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    return data


def main():
    data = load_payload(sys.stdin.buffer.read())
    if data is None:
        deny()
        return

    tool_name = str(data.get("tool_name") or data.get("tool") or "")
    if tool_name in ("StrReplace", "Edit"):
        deny()
        return

    paths = []
    collect_paths(data.get("tool_input") or data.get("input") or {}, paths)
    if tool_name in ("", "Write") and any(is_image_path(path) for path in paths):
        allow()
        return
    deny()


if __name__ == "__main__":
    main()
