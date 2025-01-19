import os
import json

def load_config():
    """Load configuration from config.json."""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config.json')
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                return json.load(f)
        
        return get_default_config()
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def get_default_config():
    """Get default configuration."""
    return {
        'project_path': '',
        'update_interval': 60,
        'max_depth': 3,
        'ignored_directories': [
            '__pycache__',
            'node_modules',
            'venv',
            '.git',
            '.idea',
            '.vscode',
            'dist',
            'build',
            'coverage'
        ],
        'ignored_files': [
            '.DS_Store',
            'Thumbs.db',
            '*.pyc',
            '*.pyo',
            'package-lock.json',
            'yarn.lock'
        ],
        'file_length_thresholds': {
            'warning': 1.0,
            'critical': 1.5,
            'severe': 2.0
        },
        'enable_ai_review': True,  # Enable AI-powered code review by default
        'ai_review_options': {
            'include_technical': True,  # Include technical analysis
            'include_simplified': True,  # Include simplified analysis
            'analyze_complexity': True,  # Analyze code complexity
            'check_duplicates': True,    # Check for duplicate code
            'check_unused': True,        # Check for unused imports/code
            'check_structure': True,     # Check code structure
            'use_gemini': True,         # Use Google Gemini for enhanced review
            'gemini_api_key': os.getenv('GEMINI_API_KEY', ''),  # Get API key from environment
            'review_sections': {
                'code_quality': True,    # Overall code quality assessment
                'strengths': True,       # Key strengths
                'improvements': True,    # Areas for improvement
                'security': True,        # Security considerations
                'performance': True,     # Performance optimization
                'best_practices': True,  # Best practices recommendations
                'priority_actions': True # Priority action items
            }
        }
    }

# Load configuration once at module level
_config = load_config()

# Binary file extensions that should be ignored
BINARY_EXTENSIONS = set(_config.get('binary_extensions', []))

# Documentation and text files that shouldn't be analyzed for functions
NON_CODE_EXTENSIONS = {
    '.md', '.txt', '.log', '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg',
    '.conf', '.config', '.markdown', '.rst', '.rdoc', '.csv', '.tsv'
}

# Extensions that should be analyzed for code
CODE_EXTENSIONS = {
    '.js', '.jsx', '.ts', '.tsx', '.py', '.java', '.cpp', '.c', '.h', 
    '.hpp', '.cs', '.go', '.rb', '.php'
}

# Regex patterns for function detection
FUNCTION_PATTERNS = {
    # Standard function declarations
    'standard': r'(?:^|\s+)(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function)',
    
    # Arrow functions with better handling of complex types
    'arrow': r'(?:^|\s+)(?:const|let|var)\s+(\w+)\s*(?:<[^>]*>)?\s*=\s*(?:async\s*)?(?:\([^{]*?\)|[^=])\s*=>\s*(?:{|[^{;\n]+)',
    
    # Object methods with optional type parameters
    'method': r'\b(\w+)\s*(?:<[^>]*>)?\s*:\s*(?:async\s*)?(?:function|\([^{]*?\)\s*(?::\s*[^{]*?)?\s*=>)',
    
    # Class methods with access modifiers and decorators
    'class_method': r'(?:^|\s+)(?:@\w+\s+)*(?:public|private|protected|readonly|static|async)?\s*(?:async\s+)?(\w+)\s*(?:<[^>]*>)?\s*\([^{]*?\)\s*(?::\s*[^{]*?)?\s*{',
    
    # Object property functions with type annotations
    'object_property': r'(\w+)\s*(?:<[^>]*>)?\s*:\s*(?:\([^{]*?\)|[^=])\s*=>\s*(?:{|[^{;\n]+)',
    
    # React functional components with comprehensive type handling
    'react_component': r'(?:export\s+)?(?:const|function)\s+(\w+)(?:\s*:\s*(?:React\.)?(?:FC|FunctionComponent)(?:<[^>]*>)?|\s*=\s*(?:\([^{]*?\))?\s*(?::\s*(?:React\.)?(?:FC|FunctionComponent|JSX\.Element|React\.ReactNode)(?:<[^>]*>)?)?)\s*(?:=>|{)',
    
    # TypeScript interface methods with generic types
    'interface_method': r'(\w+)\s*(?:<[^>]*>)?\s*\([^{]*?\)\s*:\s*(?:[^{;]*?);',
    
    # TypeScript type methods with complex return types
    'type_method': r'(\w+)\s*(?:<[^>]*>)?\s*:\s*(?:\([^{]*?\))\s*=>\s*[^;]+',
    
    # React hooks with type parameters
    'react_hook': r'(?:^|\s+)(?:const|let|var)\s+\[([^,\]]+)[^\]]*?\]\s*=\s*use[A-Z]\w+(?:<[^>]*>)?'
}

# Keywords that should not be treated as function names
IGNORED_KEYWORDS = {
    'if', 'switch', 'while', 'for', 'catch', 'finally', 'else', 'return',
    'break', 'continue', 'case', 'default', 'to', 'from', 'import', 'as',
    'try', 'except', 'raise', 'with', 'async', 'await', 'yield', 'assert',
    'pass', 'del', 'print', 'in', 'is', 'not', 'and', 'or', 'lambda',
    'global', 'nonlocal', 'class', 'def', 'n', 'lines', 'directly',
    'interface', 'type', 'enum', 'namespace', 'module', 'declare',
    'extends', 'implements', 'constructor', 'super', 'this', 'new',
    'typeof', 'keyof', 'readonly', 'abstract', 'static', 'get', 'set'
}

# Names of files and directories that should be ignored
IGNORED_NAMES = set(_config.get('ignored_directories', []))

FILE_LENGTH_STANDARDS = _config.get('file_length_standards', {})

def get_file_length_limit(file_path):
    """Get the recommended line limit for a given file type."""
    ext = os.path.splitext(file_path)[1].lower()
    return FILE_LENGTH_STANDARDS.get(ext, FILE_LENGTH_STANDARDS.get('default', 300)) 