#!/usr/bin/env python3
"""Produce a lightweight fallback project inventory as JSON."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


IGNORED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".agents",
    ".codex",
    ".claude",
    ".gemini",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "vendor",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".next",
    "target",
}

SOURCE_LANGUAGES = {
    ".py": "Python",
    ".js": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".php": "PHP",
    ".rb": "Ruby",
    ".cs": "C#",
    ".fs": "F#",
    ".vb": "Visual Basic",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".scala": "Scala",
    ".swift": "Swift",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".hrl": "Erlang",
    ".clj": "Clojure",
    ".cljs": "ClojureScript",
    ".cpp": "C++",
    ".cc": "C++",
    ".cxx": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".lua": "Lua",
    ".r": "R",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".vue": "Vue",
    ".svelte": "Svelte",
}

MANIFESTS = {
    "requirements.txt": "pip",
    "pyproject.toml": "Python project",
    "Pipfile": "Pipenv",
    "package.json": "npm-compatible",
    "pom.xml": "Maven",
    "build.gradle": "Gradle",
    "build.gradle.kts": "Gradle",
    "go.mod": "Go modules",
    "Cargo.toml": "Cargo",
    "composer.json": "Composer",
    "Gemfile": "Bundler",
    "global.json": ".NET SDK",
    "Package.swift": "Swift Package Manager",
    "pubspec.yaml": "Dart/Flutter pub",
    "mix.exs": "Mix",
    "rebar.config": "Rebar",
    "project.clj": "Leiningen",
    "deps.edn": "Clojure CLI",
    "CMakeLists.txt": "CMake",
    "meson.build": "Meson",
    "Makefile": "Make",
    "WORKSPACE": "Bazel",
    "MODULE.bazel": "Bazel",
}

MANIFEST_SUFFIXES = {
    ".csproj": ".NET project",
    ".fsproj": ".NET/F# project",
    ".vbproj": ".NET/Visual Basic project",
    ".sln": ".NET solution",
    ".xcodeproj": "Xcode project",
}

FRAMEWORK_SIGNALS = {
    "Flask": ("flask", "Flask(", "Blueprint("),
    "Django": ("django", "manage.py", "urlpatterns"),
    "FastAPI": ("fastapi", "FastAPI(", "APIRouter("),
    "Express": ("express", "express()", "express.Router"),
    "NestJS": ("@nestjs/", "@Controller(", "@Module("),
    "Spring": ("spring-boot", "@RestController", "@SpringBootApplication"),
    "Rails": ("rails", "Rails.application.routes"),
    "Laravel": ("laravel/framework", "Illuminate\\"),
    "ASP.NET Core": ("Microsoft.AspNetCore", "WebApplication.CreateBuilder"),
    "Flutter": ("flutter:", "runApp("),
    "Phoenix": ("phoenix", "use Phoenix."),
    "Actix Web": ("actix-web", "HttpServer::new"),
    "Axum": ("axum", "Router::new"),
    "Gin": ("github.com/gin-gonic/gin", "gin.Default("),
    "Echo": ("github.com/labstack/echo", "echo.New("),
    "Vue": ("\"vue\"", "createApp("),
    "React": ("\"react\"", "createRoot("),
    "Svelte": ("\"svelte\"", ".svelte"),
}

DATABASE_SIGNALS = {
    "SQLite": ("sqlite3", "sqlite://", ".db"),
    "PostgreSQL": ("postgresql", "postgres://", "psycopg"),
    "MySQL": ("mysql", "pymysql"),
    "MongoDB": ("mongodb", "mongoose", "pymongo"),
    "SQLAlchemy": ("sqlalchemy", "SQLAlchemy("),
    "Redis": ("redis", "ioredis"),
    "DynamoDB": ("dynamodb", "DynamoDb"),
    "Object/File Storage": ("s3", "blobstorage", "open("),
    "Message Queue/Event Bus": ("kafka", "rabbitmq", "amqp", "nats", "sqs"),
}

INTERFACE_SIGNALS = {
    "HTTP/API": ("route(", ".get(", ".post(", "@app.", "@router.", "@RestController", "HttpServer"),
    "GUI/UI": ("render(", "createRoot(", "runApp(", "UIViewController", "window."),
    "CLI": ("argparse", "click.command", "commander", "cobra.Command", "clap::", "System.CommandLine"),
    "Events/Messages": ("consumer", "subscribe(", "publish(", "kafka", "rabbitmq", "eventhandler"),
    "Scheduled/Batch": ("cron", "schedule(", "celery", "backgroundservice", "job"),
    "Library API": ("module.exports", "export ", "public class", "pub fn ", "__all__"),
}

ENTRY_POINT_NAMES = {
    "app.py",
    "main.py",
    "server.py",
    "manage.py",
    "wsgi.py",
    "asgi.py",
    "app.js",
    "server.js",
    "index.js",
    "main.js",
    "main.ts",
    "index.ts",
    "main.go",
    "main.rs",
    "program.cs",
    "main.java",
    "application.java",
    "main.swift",
}

SOURCE_LIKE_EXTENSIONS = {
    ".html",
    ".css",
    ".scss",
    ".sql",
    ".graphql",
    ".proto",
    ".tf",
    ".yaml",
    ".yml",
    ".xml",
}


def iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def detect_signals(files: list[Path], signal_map: dict[str, tuple[str, ...]]):
    haystack_parts = []
    for path in files:
        if path.stat().st_size <= 1_000_000:
            haystack_parts.append(path.name)
            haystack_parts.append(read_text(path))
    haystack = "\n".join(haystack_parts).lower()
    return [
        name
        for name, signals in signal_map.items()
        if any(signal.lower() in haystack for signal in signals)
    ]


def manifest_manager(path: Path) -> str | None:
    if path.name in MANIFESTS:
        return MANIFESTS[path.name]
    return MANIFEST_SUFFIXES.get(path.suffix.lower())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    files = list(iter_files(root))
    source_files = [path for path in files if path.suffix.lower() in SOURCE_LANGUAGES]
    manifest_files = [path for path in files if manifest_manager(path)]
    language_counts = Counter(SOURCE_LANGUAGES[path.suffix.lower()] for path in source_files)
    manifests = [
        {"path": str(path.relative_to(root)), "manager": manifest_manager(path)}
        for path in manifest_files
    ]
    signal_files = source_files + manifest_files

    likely_entry_points = [
        str(path.relative_to(root))
        for path in source_files
        if path.name.lower() in ENTRY_POINT_NAMES
    ]
    all_extensions = Counter(path.suffix.lower() or "<no-extension>" for path in files)
    unrecognized_extensions = {
        extension: count
        for extension, count in all_extensions.most_common()
        if extension not in SOURCE_LANGUAGES
    }
    unknown_source_candidates = [
        str(path.relative_to(root))
        for path in files
        if path.suffix.lower() in SOURCE_LIKE_EXTENSIONS
        and path.suffix.lower() not in SOURCE_LANGUAGES
    ]
    top_level_entries = sorted(path.name for path in root.iterdir())

    result = {
        "project": root.name,
        "root": str(root),
        "recognized_source_file_count": len(source_files),
        "source_extensions": dict(Counter(path.suffix.lower() for path in source_files)),
        "all_file_extensions": dict(all_extensions.most_common()),
        "unrecognized_extensions_to_investigate": unrecognized_extensions,
        "unclassified_source_candidates": unknown_source_candidates,
        "languages": dict(language_counts.most_common()),
        "manifests": manifests,
        "known_framework_candidates": detect_signals(signal_files, FRAMEWORK_SIGNALS),
        "state_and_persistence_candidates": detect_signals(signal_files, DATABASE_SIGNALS),
        "interface_candidates": detect_signals(signal_files, INTERFACE_SIGNALS),
        "likely_entry_points": likely_entry_points,
        "top_level_entries": top_level_entries,
        "tests": [
            str(path.relative_to(root))
            for path in source_files
            if "test" in path.name.lower() or "tests" in path.relative_to(root).parts
        ],
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
