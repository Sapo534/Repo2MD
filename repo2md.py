#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repo2MD: Packs a repository into a single Markdown file for LLMs.
License: MIT License
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    import pathspec
    import questionary
except ImportError as e:
    missing = e.name
    print(f"❌ Error: Missing required dependency '{missing}'.")
    print("👉 Please run: pip install questionary pathspec")
    sys.exit(1)

# Папки, которые отсекаются ВСЕГДА (даже если их нет в .gitignore)
IGNORE_DIRS = {
    ".git",
    ".svn",
    ".hg",
    "node_modules",
    "target",
    "__pycache__",
    ".venv",
    "venv",
    "ENV",
    "dist",
    "build",
    ".idea",
    ".vscode",
    ".pytest_cache",
    ".mypy_cache",
}

# Файлы, которые обычно только забивают контекст LLM мусором
IGNORE_FILES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "Cargo.lock",
    "poetry.lock",
    "repo_content.md",
}


class Repo2MD:
    def __init__(self, source_path, output_file="repo_content.md"):
        self.source_path = Path(source_path).resolve()
        self.output_file = output_file
        self.gitignore_spec = None
        self._load_gitignore()

    def _load_gitignore(self):
        """Загрузка правил из .gitignore в корне проекта."""
        gitignore_path = self.source_path / ".gitignore"
        if gitignore_path.is_file():
            try:
                with open(gitignore_path, "r", encoding="utf-8") as f:
                    patterns = f.read().splitlines()
                patterns = [
                    p.strip()
                    for p in patterns
                    if p.strip() and not p.strip().startswith("#")
                ]
                if patterns:
                    self.gitignore_spec = pathspec.PathSpec.from_lines(
                        "gitwildmatch", patterns
                    )
                    print(f"Loaded {len(patterns)} pattern(s) from .gitignore")
            except Exception as e:
                print(f"Warning: Could not parse .gitignore: {e}")

    def _should_ignore(self, path: Path) -> bool:
        """Проверка пути через .gitignore (с учетом слэша для папок)."""
        if self.gitignore_spec is None:
            return False
        try:
            rel_path = path.relative_to(self.source_path)
            # В стандарте gitignore для папок обязателен слэш на конце (например, 'venv/')
            path_str = str(rel_path) + ("/" if path.is_dir() else "")
            return self.gitignore_spec.match_file(path_str)
        except ValueError:
            return False

    def is_binary(self, file_path: Path) -> bool:
        """Проверка на бинарный файл по наличию нулевых байтов."""
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(2048)
                return b"\0" in chunk
        except Exception:
            return True

    def get_all_files(self):
        relevant_files = []

        for root, dirs, files in os.walk(self.source_path):
            # 1. Сразу выкидываем хардкорные папки (.git, node_modules, .venv)
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            # 2. Фильтруем оставшиеся папки по .gitignore
            filtered_dirs = []
            for d in dirs:
                dir_path = Path(root) / d
                if not self._should_ignore(dir_path):
                    filtered_dirs.append(d)
            dirs[:] = filtered_dirs

            # 3. Сканируем файлы
            for file in files:
                if file in IGNORE_FILES:
                    continue

                full_path = Path(root) / file

                if self._should_ignore(full_path):
                    continue

                if self.is_binary(full_path):
                    continue

                rel_path = full_path.relative_to(self.source_path)
                relevant_files.append(str(rel_path))

        return sorted(relevant_files)

    def generate_tree(self, selected_files):
        """Формирование текстового дерева файлов."""
        tree = ["```", f"Project Root: {self.source_path.name}"]
        for path in selected_files:
            tree.append(f"├── {path}")
        tree.append("```")
        return "\n".join(tree)

    def _get_markdown_fence(self, content: str) -> str:
        """
        Динамический подбор ограничителя блока (Fence).
        Если внутри файла уже есть ```, оборачиваем в ```` или больше,
        чтобы не ломать разметку Markdown.
        """
        max_backticks = 0
        current = 0
        for char in content:
            if char == "`":
                current += 1
                if current > max_backticks:
                    max_backticks = current
            else:
                current = 0
        return "`" * max(3, max_backticks + 1)

    def process(self):
        all_files = self.get_all_files()

        if not all_files:
            print("No matching files found.")
            print("Try checking your .gitignore or project path.")
            return

        selected_files = questionary.checkbox(
            "Select files/directories to include in the final Markdown:",
            choices=[questionary.Choice(f, checked=True) for f in all_files],
        ).ask()

        if not selected_files:
            print("Nothing selected.")
            return

        print(f"Compiling {len(selected_files)} file(s) into {self.output_file}...")

        try:
            with open(self.output_file, "w", encoding="utf-8") as out:
                out.write(f"# Repository Structure: {self.source_path.name}\n\n")
                out.write("## Directory Tree\n")
                out.write(self.generate_tree(selected_files))
                out.write("\n\n---\n\n")

                for rel_path in selected_files:
                    full_path = self.source_path / rel_path
                    ext = full_path.suffix.lstrip(".")
                    lang = ext if ext else "text"

                    try:
                        with open(
                            full_path, "r", encoding="utf-8", errors="replace"
                        ) as f:
                            content = f.read()
                    except Exception as e:
                        content = f"Error reading file: {e}"

                    fence = self._get_markdown_fence(content)

                    out.write(f"### File: {rel_path}\n")
                    out.write(f"{fence}{lang}\n")
                    out.write(content)
                    if not content.endswith("\n"):
                        out.write("\n")
                    out.write(f"{fence}\n\n")

            print(f" Done! File saved to: {Path(self.output_file).resolve()}")

        except Exception as e:
            print(f"Error writing file: {e}")


def clone_git_repo(repo_url):
    """Клонирование удаленного репозитория во временную папку."""
    temp_dir = tempfile.mkdtemp()
    print(f"Cloning repository {repo_url} into a temporary folder...")
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        return temp_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir)
        print(f"Git Error: {e.stderr.decode()}")
        return None


def main():
    print("--- Repo2MD: Repository to LLM-ready Markdown ---")

    target = questionary.text(
        "Enter path to a local folder or a GitHub/GitLab URL:"
    ).ask()

    if not target:
        return

    is_remote = target.startswith(("http://", "https://", "git@"))
    temp_path = None

    try:
        if is_remote:
            temp_path = clone_git_repo(target)
            if not temp_path:
                return
            work_path = temp_path
        else:
            work_path = target
            if not os.path.exists(work_path):
                print(f"Path '{work_path}' does not exist.")
                return

        output_name = questionary.text(
            "Enter output filename:", default="repo_content.md"
        ).ask()
        if not output_name:
            output_name = "repo_content.md"

        processor = Repo2MD(work_path, output_name)
        processor.process()

    finally:
        if temp_path and os.path.exists(temp_path):
            print("Cleaning up temporary files...")
            shutil.rmtree(temp_path)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting program.")
        sys.exit(0)
