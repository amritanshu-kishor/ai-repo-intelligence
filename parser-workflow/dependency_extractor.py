"""
Real dependency extraction from uploaded repositories.
Discovers files, parses imports/requires/inheritance, resolves to repo paths.
"""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from logger import get_logger

logger = get_logger()

SOURCE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".c": "c",
    ".h": "c",
    ".hpp": "cpp",
    ".go": "go",
    ".rs": "rust",
    ".rb": "ruby",
    ".php": "php",
    ".cs": "csharp",
    ".kt": "kotlin",
    ".swift": "swift",
}

CONFIG_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "go.mod",
    "Cargo.toml",
    "Gemfile",
}

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build",
    "target", ".github", ".vscode", ".idea", "coverage", ".next", "out",
    "bin", "obj", ".gradle", "vendor", "__tests__",
}

MAX_FILES = 500


def parse_repository(repo_path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """
    Scan repository, extract imports, resolve dependencies.

    Returns:
        parsed_files, dependencies (resolved edges), parse_stats
    """
    repo_path = repo_path.resolve()
    files = _discover_files(repo_path)
    module_index = _build_module_index(repo_path, files)
    external_from_configs = _parse_config_dependencies(repo_path)

    parsed_files: list[dict[str, Any]] = []
    raw_dependencies: list[dict[str, Any]] = []
    parse_failures: list[str] = []
    total_imports = 0

    for file_path, rel_path, language in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            parse_failures.append(f"{rel_path}: read error - {e}")
            continue

        loc = len(content.splitlines())
        imports, classes, functions, inheritance = _extract_from_file(
            content, language, rel_path
        )
        total_imports += len(imports)

        parsed_files.append({
            "file": rel_path,
            "language": language,
            "imports": imports,
            "dependencies": imports,
            "classes": classes,
            "functions": functions,
            "inheritance": inheritance,
            "loc": loc,
        })

        for imp in imports:
            raw_dependencies.append({
                "from": rel_path,
                "to": imp.get("target", imp.get("module", "")),
                "type": imp.get("type", "imports"),
                "raw": imp.get("raw", ""),
                "line": imp.get("line"),
            })

        for inh in inheritance:
            raw_dependencies.append({
                "from": rel_path,
                "to": inh.get("base", ""),
                "type": "inherits",
                "raw": inh.get("raw", ""),
            })

    resolved_dependencies, external_packages = _resolve_dependencies(
        raw_dependencies, module_index, external_from_configs
    )

    stats = {
        "files_scanned": len(parsed_files),
        "imports_found": total_imports,
        "raw_dependency_count": len(raw_dependencies),
        "resolved_edges": len(resolved_dependencies),
        "external_packages": len(external_packages),
        "module_index_size": len(module_index),
        "parse_failures": len(parse_failures),
        "parse_failure_samples": parse_failures[:10],
        "config_files_found": list(external_from_configs.keys()),
    }

    _log_validation(stats, resolved_dependencies)

    return parsed_files, resolved_dependencies, {**stats, "external_packages_list": external_packages}


def _discover_files(repo_path: Path) -> list[tuple[Path, str, str]]:
    """Return list of (absolute_path, relative_path, language)."""
    discovered: list[tuple[Path, str, str]] = []

    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(skip in path.parts for skip in SKIP_DIRS):
            continue

        rel = path.relative_to(repo_path).as_posix()
        name_lower = path.name.lower()

        if path.suffix in SOURCE_EXTENSIONS:
            if _is_test_file(path.name):
                continue
            discovered.append((path, rel, SOURCE_EXTENSIONS[path.suffix]))
            if len(discovered) >= MAX_FILES:
                logger.info(f"Reached file scan limit ({MAX_FILES})")
                break
        elif path.name in CONFIG_FILES:
            discovered.append((path, rel, "config"))

    logger.info(f"Discovered {len(discovered)} files under {repo_path}")
    return discovered


def _is_test_file(name: str) -> bool:
    n = name.lower()
    return (
        n.startswith("test_")
        or n.endswith("_test.py")
        or n.endswith(".test.js")
        or n.endswith(".test.ts")
        or n.endswith(".spec.js")
        or n.endswith(".spec.ts")
        or n.startswith("spec.")
    )


def _build_module_index(repo_path: Path, files: list[tuple[Path, str, str]]) -> dict[str, str]:
    """
    Map module identifiers to repository file paths.
    Keys: dotted module, path segments, filename stems, index paths.
    """
    index: dict[str, str] = {}

    for _abs, rel, language in files:
        if language == "config":
            continue

        path_obj = Path(rel)
        stem = path_obj.stem
        parts = path_obj.parts

        index[rel] = rel
        index[stem] = rel

        if language == "python":
            module_parts = list(parts[:-1]) + [stem]
            if stem == "__init__":
                module_parts = list(parts[:-1])
            dotted = ".".join(p for p in module_parts if p)
            if dotted:
                index[dotted] = rel
                for i in range(len(module_parts)):
                    partial = ".".join(module_parts[: i + 1])
                    index.setdefault(partial, rel)

        posix_no_ext = str(path_obj.with_suffix(""))
        index[posix_no_ext] = rel
        index[posix_no_ext.replace("/", ".")] = rel

        if path_obj.parent != Path("."):
            parent_key = str(path_obj.parent / stem)
            index[parent_key] = rel
            index[parent_key.replace("/", ".")] = rel

    return index


def _parse_config_dependencies(repo_path: Path) -> dict[str, list[str]]:
    """Extract external package names from config files."""
    externals: dict[str, list[str]] = {}

    pkg_json = _find_config(repo_path, "package.json")
    if pkg_json and pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(encoding="utf-8"))
            deps = list(data.get("dependencies", {}).keys())
            deps += list(data.get("devDependencies", {}).keys())
            externals["package.json"] = deps
        except (json.JSONDecodeError, OSError) as e:
            logger.debug(f"package.json parse error: {e}")

    req_txt = _find_config(repo_path, "requirements.txt")
    if req_txt and req_txt.exists():
        try:
            lines = req_txt.read_text(encoding="utf-8", errors="ignore").splitlines()
            pkgs = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                name = re.split(r"[>=<!\[;@]", line)[0].strip()
                if name:
                    pkgs.append(name.lower().replace("_", "-"))
            externals["requirements.txt"] = pkgs
        except OSError as e:
            logger.debug(f"requirements.txt parse error: {e}")

    pom = _find_config(repo_path, "pom.xml")
    if pom and pom.exists():
        try:
            text = pom.read_text(encoding="utf-8", errors="ignore")
            artifacts = re.findall(r"<artifactId>([^<]+)</artifactId>", text)
            externals["pom.xml"] = artifacts[:50]
        except OSError:
            pass

    go_mod = _find_config(repo_path, "go.mod")
    if go_mod and go_mod.exists():
        try:
            lines = go_mod.read_text(encoding="utf-8", errors="ignore").splitlines()
            mods = [ln.split()[0] for ln in lines if ln.strip().startswith("require ") or (
                ln.strip() and not ln.startswith("module") and not ln.startswith("go ")
                and not ln.startswith("require (") and not ln.startswith(")")
            )]
            externals["go.mod"] = mods[:50]
        except OSError:
            pass

    return externals


def _find_config(repo_path: Path, name: str) -> Path | None:
    direct = repo_path / name
    if direct.exists():
        return direct
    for p in repo_path.rglob(name):
        if p.is_file() and "node_modules" not in p.parts:
            return p
    return None


def _extract_from_file(
    content: str,
    language: str,
    rel_path: str,
) -> tuple[list[dict[str, Any]], list[dict], list[dict], list[dict]]:
    if language == "python":
        return _extract_python(content)
    if language in ("javascript", "typescript"):
        return _extract_js_ts(content)
    if language == "java":
        return _extract_java(content)
    if language == "go":
        return _extract_go(content)
    if language in ("cpp", "c"):
        return _extract_cpp(content)
    return [], [], [], []


def _extract_python(content: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    imports: list[dict[str, Any]] = []
    classes: list[dict] = []
    functions: list[dict] = []
    inheritance: list[dict] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return _extract_python_regex(content)

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                imports.append({
                    "module": mod,
                    "target": alias.name,
                    "type": "imports",
                    "raw": f"import {alias.name}",
                    "line": getattr(node, "lineno", None),
                })
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mod = node.module.split(".")[0]
                imports.append({
                    "module": mod,
                    "target": node.module,
                    "type": "imports",
                    "raw": f"from {node.module}",
                    "line": getattr(node, "lineno", None),
                })
                for alias in node.names:
                    imports.append({
                        "module": f"{node.module}.{alias.name}",
                        "target": f"{node.module}.{alias.name}",
                        "type": "imports",
                        "raw": f"from {node.module} import {alias.name}",
                        "line": getattr(node, "lineno", None),
                    })
        elif isinstance(node, ast.ClassDef):
            bases = []
            for base in node.bases:
                base_name = _ast_name(base)
                if base_name:
                    bases.append(base_name)
                    inheritance.append({
                        "class": node.name,
                        "base": base_name,
                        "raw": f"class {node.name}({base_name})",
                    })
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            classes.append({"name": node.name, "bases": bases, "methods": methods})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not any(node in p.body for p in ast.walk(tree) if isinstance(p, ast.ClassDef)):
                functions.append({"name": node.name})

    return imports, classes, functions, inheritance


def _extract_python_regex(content: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    imports: list[dict[str, Any]] = []
    for i, line in enumerate(content.splitlines()[:400], 1):
        line = line.strip()
        if line.startswith("import "):
            mod = line.replace("import ", "").split(" as ")[0].split(",")[0].strip().split(".")[0]
            imports.append({"module": mod, "target": mod, "type": "imports", "raw": line, "line": i})
        elif line.startswith("from "):
            parts = line.split()
            if len(parts) >= 2:
                mod = parts[1].split(".")[0]
                imports.append({"module": mod, "target": parts[1], "type": "imports", "raw": line, "line": i})
    return imports, [], [], []


def _ast_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        val = _ast_name(node.value)
        return f"{val}.{node.attr}" if val else node.attr
    return None


def _extract_js_ts(content: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    imports: list[dict[str, Any]] = []
    classes: list[dict] = []
    functions: list[dict] = []
    inheritance: list[dict] = []

    patterns = [
        (r"import\s+(?:[\w*{}\s,]+\s+from\s+)?['\"]([^'\"]+)['\"]", "imports"),
        (r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)", "requires"),
        (r"export\s+(?:default\s+)?(?:class|function)\s+(\w+)", "exports"),
    ]

    for i, line in enumerate(content.splitlines()[:400], 1):
        for pattern, edge_type in patterns:
            for match in re.finditer(pattern, line):
                target = match.group(1)
                imports.append({
                    "module": target,
                    "target": target,
                    "type": edge_type,
                    "raw": line.strip()[:120],
                    "line": i,
                })

        class_match = re.search(r"class\s+(\w+)(?:\s+extends\s+(\w+))?", line)
        if class_match:
            name = class_match.group(1)
            base = class_match.group(2)
            classes.append({"name": name, "bases": [base] if base else [], "methods": []})
            if base:
                inheritance.append({"class": name, "base": base, "raw": line.strip()[:80]})

        fn_match = re.search(r"(?:export\s+)?(?:async\s+)?function\s+(\w+)", line)
        if fn_match:
            functions.append({"name": fn_match.group(1)})

    return imports, classes, functions, inheritance


def _extract_java(content: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    imports: list[dict[str, Any]] = []
    classes: list[dict] = []
    inheritance: list[dict] = []

    for i, line in enumerate(content.splitlines()[:400], 1):
        line = line.strip()
        if line.startswith("import ") and not line.startswith("import static"):
            pkg = line.replace("import ", "").replace(";", "").strip()
            if pkg.endswith(".*"):
                pkg = pkg[:-2]
            imports.append({
                "module": pkg.split(".")[-1],
                "target": pkg,
                "type": "imports",
                "raw": line,
                "line": i,
            })
        extends_match = re.search(r"class\s+(\w+)\s+extends\s+(\w+)", line)
        if extends_match:
            inheritance.append({
                "class": extends_match.group(1),
                "base": extends_match.group(2),
                "raw": line,
            })
            classes.append({"name": extends_match.group(1), "bases": [extends_match.group(2)], "methods": []})

    return imports, classes, [], inheritance


def _extract_go(content: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    imports: list[dict[str, Any]] = []
    in_import = False

    for i, line in enumerate(content.splitlines()[:400], 1):
        stripped = line.strip()
        if stripped.startswith("import ("):
            in_import = True
            continue
        if in_import:
            if stripped == ")":
                in_import = False
                continue
            m = re.search(r'"([^"]+)"', stripped)
            if m:
                pkg = m.group(1).split("/")[-1]
                imports.append({
                    "module": pkg,
                    "target": m.group(1),
                    "type": "imports",
                    "raw": stripped,
                    "line": i,
                })
        elif stripped.startswith("import "):
            m = re.search(r'"([^"]+)"', stripped)
            if m:
                pkg = m.group(1).split("/")[-1]
                imports.append({
                    "module": pkg,
                    "target": m.group(1),
                    "type": "imports",
                    "raw": stripped,
                    "line": i,
                })

    return imports, [], [], []


def _extract_cpp(content: str) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    imports: list[dict[str, Any]] = []
    for i, line in enumerate(content.splitlines()[:400], 1):
        m = re.match(r'#include\s*[<"]([^>"]+)[>"]', line.strip())
        if m:
            target = m.group(1)
            imports.append({
                "module": Path(target).stem,
                "target": target,
                "type": "includes",
                "raw": line.strip(),
                "line": i,
            })
    return imports, [], [], []


def _resolve_dependencies(
    raw: list[dict[str, Any]],
    module_index: dict[str, str],
    config_externals: dict[str, list[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Resolve import targets to file paths or external module nodes."""
    resolved: list[dict[str, Any]] = []
    external_set: set[str] = set()

    for pkg_list in config_externals.values():
        for p in pkg_list:
            external_set.add(p.lower())

    for dep in raw:
        source = dep["from"]
        target_raw = dep.get("to", "")
        edge_type = dep.get("type", "imports")

        if not target_raw:
            continue

        resolved_target = _resolve_target(target_raw, source, module_index)

        if resolved_target:
            resolved.append({
                "from": source,
                "to": resolved_target,
                "type": edge_type,
                "resolved": True,
                "raw_target": target_raw,
            })
        else:
            ext_id = f"ext:{target_raw.split('.')[0]}"
            external_set.add(target_raw.split(".")[0].lower())
            resolved.append({
                "from": source,
                "to": ext_id,
                "type": edge_type,
                "resolved": False,
                "external": True,
                "raw_target": target_raw,
            })

    external_packages = [{"name": n, "type": "external"} for n in sorted(external_set) if n]
    return resolved, external_packages


def _resolve_target(target: str, source_file: str, module_index: dict[str, str]) -> str | None:
    """Resolve import string to a file path in the repository."""
    target = target.strip().strip("'\"")
    if not target or target.startswith("ext:"):
        return None

    if target in module_index:
        return module_index[target]

    # Relative JS/TS imports
    if target.startswith("."):
        source_dir = Path(source_file).parent
        candidates = [
            (source_dir / target).as_posix(),
            (source_dir / f"{target}.js").as_posix(),
            (source_dir / f"{target}.ts").as_posix(),
            (source_dir / f"{target}.tsx").as_posix(),
            (source_dir / f"{target}.jsx").as_posix(),
            (source_dir / target / "index.js").as_posix(),
            (source_dir / target / "index.ts").as_posix(),
        ]
        for c in candidates:
            c_norm = c.lstrip("./")
            if c in module_index:
                return module_index[c]
            if c_norm in module_index:
                return module_index[c_norm]

    stem = Path(target).stem
    if stem in module_index:
        return module_index[stem]

    dotted = target.replace("/", ".")
    if dotted in module_index:
        return module_index[dotted]

    parts = target.split(".")
    for i in range(len(parts), 0, -1):
        partial = ".".join(parts[:i])
        if partial in module_index:
            return module_index[partial]

    no_ext = target.replace(".", "/")
    if no_ext in module_index:
        return module_index[no_ext]

    return None


def _log_validation(stats: dict[str, Any], dependencies: list[dict[str, Any]]) -> None:
    internal = sum(1 for d in dependencies if d.get("resolved"))
    external = sum(1 for d in dependencies if d.get("external"))
    logger.info("=" * 50)
    logger.info("DEPENDENCY EXTRACTION VALIDATION")
    logger.info(f"  Files scanned:      {stats.get('files_scanned', 0)}")
    logger.info(f"  Imports found:      {stats.get('imports_found', 0)}")
    logger.info(f"  Resolved edges:     {stats.get('resolved_edges', 0)} ({internal} internal, {external} external)")
    logger.info(f"  Module index size:  {stats.get('module_index_size', 0)}")
    logger.info(f"  External packages:  {stats.get('external_packages', 0)}")
    logger.info(f"  Parse failures:     {stats.get('parse_failures', 0)}")
    logger.info("=" * 50)
