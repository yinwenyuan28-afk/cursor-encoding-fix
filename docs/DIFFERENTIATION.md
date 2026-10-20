# 定位与差异

## 问题

Cursor Agent 在简体中文 Windows 上使用官方 `Write` / `StrReplace` 时，非 ASCII 内容可能被静默存成 **GBK**（论坛另有 UTF-16 LE 报告）。`files.encoding`、系统 ACP UTF-8 实验选项往往无效。

## 本仓库做法

1. MCP 强制写出无 BOM UTF-8。
2. Hook 拦截官方文本写入（图片除外）。
3. Skill 约束 Agent 走 MCP。
4. 读侧可识别 GBK/UTF-16，编辑后迁移到 UTF-8（不是写回 GBK）。

## 非目标

- 不维护「磁盘永远保持 GBK」的遗留工作流（参见 mcp-fileencoding、codepage-bridge-mcp）。
- 不做大而全的通用 filesystem MCP。
