# cursor-encoding-fix

专治 **简体中文 Windows** 上 Cursor Agent 的 `Write` / `StrReplace` 把非 ASCII **静默存成 GBK** 的问题。

策略：用 MCP 工具读写文件，**一律落盘为无 BOM 的 UTF-8**；可选钩子拦截官方写入工具，避免 Agent「自觉」失败。

> 与「读 GBK、写回 GBK」的遗留编码桥（如 mcp-fileencoding）不同：本仓库面向 **现代 UTF-8 工程被 Cursor 写坏** 的场景。

## 特性

- MCP：`read_utf8` / `write_utf8` / `edit_utf8`
- 读：UTF-8、UTF-8 BOM、UTF-16 LE/BE（BOM）、GBK
- 写/改：无 BOM UTF-8；自动创建父目录；路径必须为绝对路径
- `edit_utf8` 可将 GBK / UTF-16 源文件转成 UTF-8
- Hook：拒绝官方 `Write` / `StrReplace` / `Edit`（图片 `Write` 除外）
- Skill：教 Agent 正确用法
- `scripts/doctor.py`：写探针并核对磁盘字节

## 快速安装（Cursor）

1. Clone 本仓库到本机，例如 `C:\\dev\\code\\cursor\\cursor-encoding-fix`。
2. 在 `%USERPROFILE%\\.cursor\\mcp.json` 增加（按本机 Python 路径改 `command`）：

```json
{
  "mcpServers": {
    "utf8-files": {
      "command": "python",
      "args": ["C:\\dev\\code\\cursor\\cursor-encoding-fix\\mcp\\server.py"],
      "env": {
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1"
      }
    }
  }
}
```

3. 在 `%USERPROFILE%\\.cursor\\hooks.json` 增加拦截（路径同上）：

```json
{
  "version": 1,
  "hooks": {
    "preToolUse": [
      {
        "command": "python C:\\dev\\code\\cursor\\cursor-encoding-fix\\hooks\\deny-official-text-edit.py",
        "matcher": "^(Write|StrReplace|Edit)$"
      }
    ]
  }
}
```

4. 将 `skills/utf8-files/` 拷到 `%USERPROFILE%\\.cursor\\skills\\utf8-files\\`（或做目录联接）。
5. 重载 Cursor / 重启 MCP `utf8-files`。

## 自检

```bat
python scripts\doctor.py --path C:\dev\code\\cursor\\cursor-encoding-fix\\_probe.txt
```

期望：`match_utf8_exact True`，hex 以 `e7 bc 96 e7 a0 81...` 一类 UTF-8 开头，而不是 GBK 的 `d6 d0...`。

## Agent 用法摘要

1. 只用 `read_utf8` / `write_utf8` / `edit_utf8`，路径用绝对路径。
2. `read_utf8` 若以 `NOTE:` 开头，剥掉第一行再当正文。
3. `edit_utf8` 的 `old_string` 从刚读到的正文复制（注意 CRLF/LF）。

详见 `skills/utf8-files/SKILL.md`。

## 布局

```text
mcp/server.py                 # MCP stdio 服务
hooks/deny-official-text-edit.py
skills/utf8-files/SKILL.md
scripts/doctor.py
docs/                         # 补充说明
```

## 许可

MIT
