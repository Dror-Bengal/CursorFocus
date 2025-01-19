# CursorFocus

An AI-powered code review and project analysis tool that provides intelligent, contextual descriptions of your codebase.

## Features

- 🔄 Automated Code Reviews with AI-powered insights
- 📝 Intelligent file and function documentation
- 🌳 Project structure analysis and visualization
- 📏 Code quality metrics and alerts
- 🎯 Smart project type detection
- 🔍 Duplicate code detection
- 🧩 Modular and extensible design
- 🎛️ Customizable rules and configurations
- 🔄 Real-time project monitoring

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/CursorFocus.git
```

2. Create and activate a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
cd CursorFocus
pip install -e .
```

4. Create a `.env` file from the template:
```bash
cp .env.example .env
```

5. Add your Gemini API key to the `.env` file:
```
GEMINI_API_KEY=your_api_key_here
```

## Usage

### Generate a Code Review

From your project directory:

```bash
cursorfocus-review
```

This will generate a `CodeReview.md` file in your project root with:
- Project structure analysis
- File-by-file review
- Function documentation
- Code duplication alerts
- Project metrics

### Monitor Project Changes

To start real-time project monitoring:

```bash
cursorfocus
```

This will create and update a `Focus.md` file in your project root with:
- Current project state
- Directory structure
- File analysis
- Development guidelines

## Configuration

You can customize CursorFocus by creating a `config.json` file in your project root:

```json
{
  "ignored_directories": [
    "node_modules",
    "venv",
    ".git"
  ],
  "ignored_files": [
    "*.pyc",
    ".DS_Store"
  ],
  "max_depth": 3,
  "update_interval": 60
}
```

## Requirements

- Python 3.8 or higher
- Google Gemini API key

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history. 