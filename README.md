# CursorFocus

A powerful code review and project analysis tool that helps you maintain high-quality code and documentation. CursorFocus automatically analyzes your project structure, generates intelligent code reviews, and maintains project documentation.

## Features

- 🔄 Automated Code Reviews with AI-powered insights
- 📝 Intelligent file and function documentation
- 🌳 Project structure analysis and visualization
- 📏 Code quality metrics and alerts
- 🎯 Smart project type detection
- 🔍 Duplicate code detection
- 🧩 Modular and extensible design
- 🎛️ Customizable rules and configurations

## Quick Start

1. Install CursorFocus:
   ```bash
   pip install cursorfocus
   ```

2. Set up your environment:
   ```bash
   # Copy environment template
   cp .env.example .env
   
   # Edit .env with your Gemini API key
   # Get your API key from: https://makersuite.google.com/app/apikey
   ```

3. Run CursorFocus:
   ```bash
   python -m cursorfocus
   ```

## Generated Files

CursorFocus maintains three key files:

1. **Focus.md** (Updates every 60 seconds)
   - Real-time project structure
   - File and function documentation
   - Project metrics and insights

2. **.cursorrules** (One-time generation)
   - Project-specific Cursor settings
   - Coding standards and preferences
   - Customized for your project type

3. **CodeReview.md** (On-demand generation)
   - Comprehensive code analysis
   - Quality metrics and alerts
   - Actionable improvement suggestions
   - Duplicate code detection
   - Security considerations

## Configuration

1. Environment Variables (`.env`):
   ```bash
   GEMINI_API_KEY=your_api_key_here  # Required for AI features
   PROJECT_PATH=.                     # Project root directory
   UPDATE_INTERVAL=60                 # Update interval in seconds
   ```

2. Project Configuration (`config.json`):
   ```json
   {
     "ignored_directories": ["node_modules", "dist"],
     "ignored_files": ["*.pyc", ".DS_Store"],
     "max_file_length": {
       "js": 300,
       "py": 400
     }
   }
   ```

## Usage Examples

1. Generate a code review:
   ```bash
   python -m cursorfocus review
   ```

2. Update project documentation:
   ```bash
   python -m cursorfocus focus
   ```

3. Monitor project changes:
   ```bash
   python -m cursorfocus watch
   ```

## Best Practices

1. Code Review:
   - Run after significant changes
   - Review before major commits
   - Monitor for recurring issues

2. Project Documentation:
   - Let Focus.md update automatically
   - Use as reference during development
   - Keep .cursorrules stable

3. API Usage:
   - Code reviews use API calls
   - Run reviews thoughtfully
   - Consider rate limits

## Troubleshooting

1. Missing API Key:
   ```
   Error: GEMINI_API_KEY not found
   Solution: Add your API key to .env file
   ```

2. File Permission Issues:
   ```bash
   chmod +x CursorFocus/run.sh
   ```

3. Dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Contributing

We welcome contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details. 