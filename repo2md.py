#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Repo2MD: Packs a repository into a single Markdown file.
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

# Default settings
# Expanded list of supported file extensions
DEFAULT_EXTENSIONS = {
    '.rs', '.py', '.toml', '.md', '.js', '.ts', '.c', '.cpp', 
    '.h', '.hpp', '.go', '.java', '.slint', '.json', '.yaml', 
    '.yml', '.txt', '.lock', '.sh'
}

# Directories that will always be ignored
IGNORE_DIRS = {'.git', 'target', 'node_modules', '__pycache__', '.venv', 'dist', 'build'}

class Repo2MD:
    def __init__(self, source_path, output_file="repo_content.md"):
        self.source_path = Path(source_path).resolve()
        self.output_file = output_file
        self.files_to_process = []

    def is_binary(self, file_path):
        """Check if a file is binary."""
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
                
                # Condition: extension is whitelisted OR file is text-based with no extension
                if (ext in DEFAULT_EXTENSIONS or ext == '') and not self.is_binary(full_path):
                    rel_path = full_path.relative_to(self.source_path)
                    relevant_files.append(str(rel_path))
        return sorted(relevant_files)

    def generate_tree(self, selected_files):
        """Generates a text-based project tree structure from selected files."""
        tree = []
        # Simple tree mock-up
        tree.append("```")
        tree.append(f"Project Root: {self.source_path.name}")
        
        # Dictionaries could be used for building a prettier tree, but for LLMs 
        # a list of paths is sufficient if the tree is too complex.
        # Here we just list out the structure.
        for path in selected_files:
            tree.append(f"├── {path}")
        tree.append("```")
        return "\n".join(tree)

    def process(self):
        # 1. Collect all suitable files
        all_files = self.get_all_files()
        
        if not all_files:
            print("No matching files found.")
            return

        # 2. Interactive selection
        selected_files = questionary.checkbox(
            "Select files/directories to include in the final file:",
            choices=[questionary.Choice(f, checked=True) for f in all_files]
        ).ask()

        if not selected_files:
            print("Nothing selected.")
            return

        # 3. Content generation
        print(f"Compiling data into {self.output_file}...")
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as out:
                out.write(f"# Repository Structure: {self.source_path.name}\n\n")
                out.write("## Directory Tree\n")
                out.write(self.generate_tree(selected_files))
                out.write("\n\n---\n\n")

                for rel_path in selected_files:
                    full_path = self.source_path / rel_path
                    ext = full_path.suffix.lstrip('.')
                    # Mapping for code syntax highlighting (simplified)
                    lang = ext if ext else "text"
                    
                    out.write(f"### File: {rel_path}\n")
                    out.write(f"```{lang}\n")
                    try:
                        with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"Error reading file: {e}")
                    out.write("\n```\n\n")
            
            print(f"Done! File saved to: {Path(self.output_file).resolve()}")
            
        except Exception as e:
            print(f"Error writing file: {e}")

def clone_git_repo(repo_url):
    """Clones the repository into a temporary directory."""
    temp_dir = tempfile.mkdtemp()
    print(f"Cloning repository {repo_url} into a temporary folder...")
    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', repo_url, temp_dir],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE
        )
        return temp_dir
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_dir)
        print(f"Git Error: {e.stderr.decode()}")
        return None

def main():
    print("--- Repo2MD: Repository to LLM-ready Markdown ---")
    
    target = questionary.text("Enter path to a local folder or a GitHub/GitLab URL:").ask()
    
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
                print(f"Path '{work_path}' does not exist.")
                return

        output_name = questionary.text("Enter output filename:", default="repo_content.md").ask()
        
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
