---
name: utf8-files
description: >-
  Write and edit text files on this Windows machine. Use instead of the official
  Write, StrReplace, and Edit tools whenever creating or modifying a file,
  including Chinese, plans, markdown, and source comments. Official tools save
  non-ASCII text as GBK. Also use read_utf8 before editing a file that may
  contain Chinese, because the official Read tool decodes UTF-8 as GBK.
---

# UTF-8 文件工具（cursor-encoding-fix）

本机官方 Write、StrReplace、Edit 会把中文存成 GBK。改用 MCP 服务 `utf8-files`
（本仓库 `mcp/server.py`）。

1. 先用 GetDynamicTools 查 `user-utf8-files`（或配置名 `utf8-files`）的参数，再调用。
2. **路径必须是绝对路径**（例如 `C:\\dev\\...`）。相对路径会被拒绝，避免写到 MCP 进程 cwd（常见为用户主目录）。
3. 读含中文的文件用 `read_utf8`。返回若以 `NOTE:` 开头，第一行是编码说明，正文从第二行开始。
4. 新建或覆盖用 `write_utf8(path, contents)`。缺失的父目录会自动创建；写出无 BOM 的 UTF-8。
5. 改已有文件用 `edit_utf8(path, old_string, new_string, replace_all)`。`old_string` 必须与文件里的原文一致（含 CRLF/LF）。多处相同时要么加长区分，要么传 `replace_all=true`（非重叠替换）。
6. 读支持 UTF-8 / UTF-8 BOM / UTF-16 LE·BE（带 BOM）/ GBK；写和编辑后一律落盘为无 BOM 的 UTF-8。
7. 单文件正文上限约 150 万字符（读、写、编辑一致）。
8. 不要再调用官方 Write、StrReplace、Edit。钩子会拒绝它们（图片 Write 除外）。
