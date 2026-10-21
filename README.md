![AI-Friendly](https://img.shields.io/badge/AI--Friendly-Zone-green?style=flat-square)

# Repo2MD

**Repo2MD** is a CLI tool for developers that compiles the entire source code of your repository (either local or from GitHub) into a single, structured Markdown file.

The tool is specifically designed to prepare context for working with **LLMs** (ChatGPT, Claude, Gemini), allowing models to "see" your entire project as a whole.

## Features

* **Interactive**: Select files and folders via an interactive terminal checkbox prompt.
* **Smart Filtering**: Respects your `.gitignore` and automatically ignores binaries, locks, and system directories (`.git`, `node_modules`, `target`, `.venv`, etc.).
* **Safe Code Fences**: Accurately embeds Markdown and nested backticks (` ``` `) without breaking the resulting formatting.
* **Git Integration**: Clone, extract, and clean up temporary repositories automatically by URL.

## Installation

### Arch Linux

```bash
git clone https://github.com/Sapo534/Repo2MD.git
cd Repo2MD
updpkgsums
makepkg -si
```

### Universal Installation (via pip)

```bash
pip install questionary pathspec
# Run directly:
python repo2md.py
```

## Usage

Simply run `repo2md` in your terminal and follow the prompts:

1. Provide the folder path or repository URL.
2. Select files using the Spacebar.
3. Get your ready-to-use `.md` file for LLMs.

## License

Distributed under the MIT License.
