# CursorFocus

A lightweight tool that maintains a focused view of your project structure and environment. CursorFocus automatically tracks your project files, functions, and environment variables, updating every 60 seconds to keep you informed of changes.

## Features

- 🔄 Real-time project structure tracking
- 📝 Automatic file and function documentation
- 🌳 Hierarchical directory visualization
- 📏 File length standards and alerts
- 🎯 Project-specific information detection
- 🔍 Smart project type detection (Chrome Extension, Node.js, Python)
- 🧩 Modular and extensible design

## Setup

1. Clone or copy the CursorFocus directory to your project:
   ```bash
   git clone https://github.com/Dror-Bengal/CursorFocus.git CursorFocus
   ```

2. Install dependencies (Python 3.6+ required):
   ```bash
   cd CursorFocus
   pip install -r requirements.txt
   ```

3. Run the script:
   ```bash
   python3 focus.py
   ```

## Output

CursorFocus generates a `Focus.md` file in your project root with:

1. Project Overview
   - Project name and description
   - Key features and version
   - Project type detection

2. Project Structure
   - Directory hierarchy
   - File descriptions
   - Function listings with detailed descriptions
   - File type detection
   - File length alerts based on language standards

3. Code Analysis
   - Key function identification
   - Detailed function descriptions
   - File length standards compliance

## Configuration

Edit `config.json` to customize:

```json
{
    "project_path": "",
    "update_interval": 60,
    "max_depth": 3,
    "ignored_directories": [
        "__pycache__",
        "node_modules",
        "venv",
        ".git",
        ".idea",
        ".vscode",
        "dist",
        "build",
        "coverage"
    ],
    "ignored_files": [
        ".DS_Store",
        "Thumbs.db",
        "*.pyc",
        "*.pyo",
        "package-lock.json",
        "yarn.lock"
    ]
}
```

## File Length Standards

CursorFocus includes built-in file length standards for different file types:

- JavaScript/TypeScript:
  - Regular files: 300 lines
  - React components (.jsx/.tsx): 250 lines

- Python files: 400 lines

- Style files:
  - CSS/SCSS/LESS/SASS: 400 lines

- Template files:
  - HTML: 300 lines
  - Vue/Svelte components: 250 lines

- Configuration files:
  - JSON/YAML/TOML: 100 lines

- Documentation files:
  - Markdown/RST: 500 lines

The tool will alert you when files exceed these recommended limits.

## Project Structure

```
CursorFocus/
├── focus.py           # Main entry point
├── analyzers.py       # File and code analysis
├── config.py          # Configuration management
├── content_generator.py # Focus file generation
├── project_detector.py # Project type detection
├── config.json        # User configuration
└── requirements.txt   # Dependencies
```

## Supported Project Types

CursorFocus automatically detects and provides specialized information for:

- Chrome Extensions (manifest.json)
- Node.js Projects (package.json)
- Python Projects (setup.py, pyproject.toml)
- Generic Projects (basic structure)

## Contributing

Contributions are welcome! Please feel free to submit pull requests or create issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 