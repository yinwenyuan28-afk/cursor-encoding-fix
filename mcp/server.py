"""stdio MCP server: read, write, and edit text files as UTF-8.

Official Cursor Write/StrReplace on Chinese Windows store non-ASCII text as GBK.
This server always writes UTF-8 without a BOM. stdout is reserved for JSON-RPC.
"""

import json
import os
import sys
from pathlib import Path

MAX_CHARS = 1500000
VERSION = "1.1.0"


def emit(obj):
    sys.stdout.buffer.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))
    sys.stdout.buffer.write(b"\n")
    sys.stdout.buffer.flush()


def resolve_path(path_arg):
    if not isinstance(path_arg, str) or not path_arg.strip():
        raise ValueError("path must be a non-empty string")
    path = Path(path_arg)
    if not path.is_absolute():
        raise ValueError(
            "path must be absolute (got relative %r); MCP cwd is not the workspace"
            % path_arg
        )
    return path


def decode_file(path):
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw[3:].decode("utf-8"), "utf-8-bom"
    if raw.startswith(b"\xff\xfe"):
        text = raw.decode("utf-16-le")
        if text.startswith("\ufeff"):
            text = text[1:]
        return text, "utf-16-le"
    if raw.startswith(b"\xfe\xff"):
        text = raw.decode("utf-16-be")
        if text.startswith("\ufeff"):
            text = text[1:]
        return text, "utf-16-be"
    try:
        return raw.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("gbk"), "gbk"
    except UnicodeDecodeError as exc:
        raise ValueError(
            "file is neither UTF-8, UTF-16 (BOM), nor GBK: %s" % exc
        )


def check_size(text, what):
    if len(text) > MAX_CHARS:
        raise ValueError(
            "%s is larger than %s characters" % (what, MAX_CHARS)
        )


def write_utf8(path, text):
    check_size(text, "contents")
    parent = path.parent
    if parent and str(parent) not in ("", "."):
        parent.mkdir(parents=True, exist_ok=True)
    data = text.encode("utf-8")
    tmp = path.with_name(path.name + ".utf8tmp")
    try:
        tmp.write_bytes(data)
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
    return len(data)


def note_prefix(encoding):
    if encoding == "gbk":
        return (
            "NOTE: on-disk encoding was gbk "
            "(UTF-8 decode failed; verify the body is correct). "
            "The body below is decoded text.\n"
        )
    return (
        "NOTE: on-disk encoding was %s. The body below is decoded text.\n"
        % encoding
    )


def tool_read(args):
    path = resolve_path(args["path"])
    if not path.is_file():
        raise ValueError("file not found: %s" % path)
    text, encoding = decode_file(path)
    check_size(text, "file")
    if encoding == "utf-8":
        return text
    return note_prefix(encoding) + text


def tool_write(args):
    path = resolve_path(args["path"])
    contents = args["contents"]
    if not isinstance(contents, str):
        raise ValueError("contents must be a string")
    nbytes = write_utf8(path, contents)
    return "wrote %s bytes=%s encoding=utf-8" % (path, nbytes)


def tool_edit(args):
    path = resolve_path(args["path"])
    old = args["old_string"]
    new = args["new_string"]
    replace_all = bool(args.get("replace_all", False))
    if not isinstance(old, str) or not isinstance(new, str):
        raise ValueError("old_string and new_string must be strings")
    if old == "":
        raise ValueError("old_string is empty")
    if old == new:
        raise ValueError("old_string and new_string are the same")
    if not path.is_file():
        raise ValueError("file not found: %s" % path)
    text, encoding = decode_file(path)
    check_size(text, "file")
    count = text.count(old)
    if count == 0:
        raise ValueError("old_string not found")
    if count > 1 and not replace_all:
        raise ValueError(
            "old_string matched %s times; pass replace_all=true to replace all"
            % count
        )
    updated = text.replace(old, new) if replace_all else text.replace(old, new, 1)
    check_size(updated, "contents after edit")
    nbytes = write_utf8(path, updated)
    replaced = count if replace_all else 1
    return (
        "updated %s replacements=%s bytes=%s encoding=utf-8 converted_from=%s"
        % (path, replaced, nbytes, encoding)
    )


TOOLS = {
    "read_utf8": {
        "description": (
            "Read a text file and return Unicode text. Decodes UTF-8, UTF-8 BOM, "
            "UTF-16 LE/BE (BOM), or GBK. Path must be absolute. Does not change the file."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute file path",
                }
            },
            "required": ["path"],
            "additionalProperties": False,
        },
        "fn": tool_read,
    },
    "write_utf8": {
        "description": (
            "Create or overwrite a text file as UTF-8 without BOM. "
            "Path must be absolute. Creates missing parent directories. "
            "Use this instead of the official Write tool."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute file path",
                },
                "contents": {
                    "type": "string",
                    "description": "Full file text",
                },
            },
            "required": ["path", "contents"],
            "additionalProperties": False,
        },
        "fn": tool_write,
    },
    "edit_utf8": {
        "description": (
            "Replace an exact substring and save as UTF-8 without BOM. "
            "Path must be absolute. GBK/UTF-16 sources are converted to UTF-8. "
            "Use instead of official StrReplace/Edit."
        ),
        "schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute file path",
                },
                "old_string": {
                    "type": "string",
                    "description": (
                        "Exact text to replace. Must occur once unless replace_all is true."
                    ),
                },
                "new_string": {"type": "string"},
                "replace_all": {
                    "type": "boolean",
                    "description": "Replace every non-overlapping match. Default false.",
                },
            },
            "required": ["path", "old_string", "new_string"],
            "additionalProperties": False,
        },
        "fn": tool_edit,
    },
}


def tool_list():
    return {
        "tools": [
            {
                "name": name,
                "description": spec["description"],
                "inputSchema": spec["schema"],
            }
            for name, spec in TOOLS.items()
        ]
    }


def tool_call(params):
    name = params.get("name")
    args = params.get("arguments") or {}
    if isinstance(args, str):
        args = json.loads(args)
    spec = TOOLS.get(name)
    if spec is None:
        raise ValueError("unknown tool: %s" % name)
    text = spec["fn"](args)
    return {"content": [{"type": "text", "text": text}], "isError": False}


def handle(msg):
    method = msg.get("method")
    params = msg.get("params") or {}
    if method == "initialize":
        version = params.get("protocolVersion") or "2024-11-05"
        return {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "cursor-encoding-fix", "version": VERSION},
        }
    if method == "tools/list":
        return tool_list()
    if method == "tools/call":
        try:
            return tool_call(params)
        except Exception as exc:
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    if method == "ping":
        return {}
    raise ValueError("method not found: %s" % method)


def main():
    stdin = sys.stdin.buffer
    while True:
        line = stdin.readline()
        if not line:
            return
        stripped = line.strip()
        if not stripped:
            continue
        try:
            msg = json.loads(stripped.decode("utf-8"))
        except Exception as exc:
            sys.stderr.write("bad message: %s\n" % exc)
            continue
        if "id" not in msg:
            continue
        try:
            result = handle(msg)
            emit({"jsonrpc": "2.0", "id": msg["id"], "result": result})
        except Exception as exc:
            emit(
                {
                    "jsonrpc": "2.0",
                    "id": msg["id"],
                    "error": {"code": -32601, "message": str(exc)},
                }
            )


if __name__ == "__main__":
    main()
