#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repo2MD: Сборщик репозитория в один Markdown-файл.
License: MIT License
Copyright (c) 2026
"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
import questionary
import sys

# Настройки по умолчанию
# Расширенный список поддерживаемых расширений
DEFAULT_EXTENSIONS = {
    '.rs', '.py', '.toml', '.md', '.js', '.ts', '.c', '.cpp', 
    '.h', '.hpp', '.go', '.java', '.slint', '.json', '.yaml', 
    '.yml', '.txt', '.lock', '.sh'
}

# Папки, которые мы точно игнорируем
IGNORE_DIRS = {'.git', 'target', 'node_modules', '__pycache__', '.venv', 'dist', 'build'}

class Repo2MD:
    def __init__(self, source_path, output_file="repo_content.md"):
        self.source_path = Path(source_path).resolve()
        self.output_file = output_file
        self.files_to_process = []

    def is_binary(self, file_path):
        """Проверка, является ли файл бинарным."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except Exception:
            return True

    def get_all_files(self):
        relevant_files = []
        for root, dirs, files in os.walk(self.source_path):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                full_path = Path(root) / file
                ext = full_path.suffix.lower()
                
                # Условие: расширение в белом списке ИЛИ файл текстовый без расширения
                if (ext in DEFAULT_EXTENSIONS or ext == '') and not self.is_binary(full_path):
                    rel_path = full_path.relative_to(self.source_path)
                    relevant_files.append(str(rel_path))
        return sorted(relevant_files)

    def generate_tree(self, selected_files):
        """Создает текстовое дерево структуры проекта из выбранных файлов."""
        tree = []
        # Простая имитация дерева
        tree.append("```")
        tree.append(f"Project Root: {self.source_path.name}")
        
        # Для построения красивого дерева можно использовать словари, но для LLM 
        # достаточно списка путей, если дерево слишком сложное.
        # Здесь мы просто перечислим структуру.
        for path in selected_files:
            tree.append(f"├── {path}")
        tree.append("```")
        return "\n".join(tree)

    def process(self):
        # 1. Сбор всех подходящих файлов
        all_files = self.get_all_files()
        
        if not all_files:
            print("Подходящие файлы не найдены.")
            return

        # 2. Интерактивный выбор
        selected_files = questionary.checkbox(
            "Выберите файлы/директории для включения в финальный файл:",
            choices=[questionary.Choice(f, checked=True) for f in all_files]
        ).ask()

        if not selected_files:
            print("Ничего не выбрано.")
            return

        # 3. Генерация контента
        print(f"Сборка данных в {self.output_file}...")
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as out:
                out.write(f"# Repository Structure: {self.source_path.name}\n\n")
                out.write("## Directory Tree\n")
                out.write(self.generate_tree(selected_files))
                out.write("\n\n---\n\n")

                for rel_path in selected_files:
                    full_path = self.source_path / rel_path
                    ext = full_path.suffix.lstrip('.')
                    # Маппинг для подсветки (упрощенный)
                    lang = ext if ext else "text"
                    
                    out.write(f"### File: {rel_path}\n")
                    out.write(f"```{lang}\n")
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"Error reading file: {e}")
                    out.write("\n```\n\n")
            
            print(f"Готово! Файл сохранен: {Path(self.output_file).resolve()}")
            
        except Exception as e:
            print(f"Ошибка при записи файла: {e}")

def clone_git_repo(repo_url):
    """Клонирует репозиторий во временную папку."""
    temp_dir = tempfile.mkdtemp()
    print(f"Клонирование репозитория {repo_url} во временную папку...")
    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, temp_dir],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        return temp_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir)
        print(f"Ошибка Git: {e.stderr.decode()}")
        return None

def main():
    print("--- Repo2MD: Repository to LLM-ready Markdown ---")
    
    target = questionary.text("Введите путь к локальной папке или URL GitHub/GitLab:").ask()
    
    if not target:
        return

    is_remote = target.startswith(('http://', 'https://', 'git@'))
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
                print(f"Путь {work_path} не существует.")
                return

        output_name = questionary.text("Введите имя выходного файла:", default="repo_content.md").ask()
        
        processor = Repo2MD(work_path, output_name)
        processor.process()

    finally:
        if temp_path and os.path.exists(temp_path):
            print("Очистка временных файлов...")
            shutil.rmtree(temp_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход из программы.")
        sys.exit(0)
