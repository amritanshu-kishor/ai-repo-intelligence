"""
Build per-file repository summaries from parsed file metadata.
Used by the parser summaries API (no external LLM required).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def build_file_summary(file_data: dict[str, Any]) -> dict[str, Any]:
    path = file_data.get("file", "")
    language = file_data.get("language", "unknown")
    classes = file_data.get("classes", []) or []
    functions = file_data.get("functions", []) or []
    imports = file_data.get("imports", []) or []
    loc = int(file_data.get("loc", 0) or 0)

    class_names = [c.get("name", "") for c in classes if c.get("name")]
    func_names = [f.get("name", "") for f in functions if f.get("name")]

    parts: list[str] = []
    if class_names:
        shown = ", ".join(class_names[:6])
        suffix = f" (+{len(class_names) - 6} more)" if len(class_names) > 6 else ""
        parts.append(f"defines {len(class_names)} class(es): {shown}{suffix}")
    if func_names:
        parts.append(f"{len(func_names)} function(s)")
    if imports:
        parts.append(f"{len(imports)} import(s)")
    if loc:
        parts.append(f"{loc} lines")

    role = _infer_role(path, class_names, func_names, imports)
    detail = "; ".join(parts) if parts else "parsed source file"
    summary = f"{role} — {language} — {detail}"

    symbols = class_names + [n for n in func_names if n not in class_names]
    return {
        "path": path,
        "summary": summary,
        "symbols": symbols[:30],
        "language": language,
        "loc": loc,
    }


def _infer_role(path: str, classes: list[str], functions: list[str], imports: list) -> str:
    name = path.replace("\\", "/").split("/")[-1].lower()
    if name in ("main.py", "app.py", "index.js", "index.ts", "server.py", "manage.py"):
        return "Entry point"
    if "test" in name or "/test" in path.lower():
        return "Test module"
    if name in ("config.py", "settings.py", ".env"):
        return "Configuration"
    if any(x in name for x in ("route", "controller", "handler", "view")):
        return "HTTP / API layer"
    if any(x in name for x in ("service", "usecase")):
        return "Service layer"
    if any(x in name for x in ("repo", "repository", "dao", "model", "dto")):
        return "Data layer"
    if classes and not functions:
        return "Type definitions"
    if len(imports) > 8:
        return "Integration hub"
    return "Application module"


def build_repository_summaries(
    repository_id: str,
    parsed_files: list[dict[str, Any]],
) -> dict[str, Any]:
    items = [build_file_summary(f) for f in parsed_files if f.get("file")]
    items.sort(key=lambda x: x["path"])
    return {
        "repository_id": repository_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": items,
        "file_count": len(items),
    }
