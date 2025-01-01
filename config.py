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
    """Get default configuration settings."""
    return {
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
        ],
        "binary_extensions": [
            ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".exe", ".bin"
        ],
        "file_length_standards": {
            ".js": 300,
            ".jsx": 250,
            ".ts": 300,
            ".tsx": 250,
            ".py": 400,
            ".css": 400,
            ".scss": 400,
            ".less": 400,
            ".sass": 400,
            ".html": 300,
            ".vue": 250,
            ".svelte": 250,
            ".json": 100,
            ".yaml": 100,
            ".yml": 100,
            ".toml": 100,
            ".md": 500,
            ".rst": 500,
            "default": 300
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
    '.hpp', '.cs', '.go', '.rb', '.php', '.phtml', '.phps',
    '.cc', '.cxx', '.cp', '.c++', '.cshtml', '.csx',
    # Rust
    '.rs', '.rlib',
    # Swift
    '.swift', '.swiftmodule',
    # Kotlin
    '.kt', '.kts',
    # Dart
    '.dart',
    # Scala
    '.scala', '.sc',
    # R
    '.r', '.R', '.Rmd',
    # MATLAB
    '.m', '.mat',
    # Lua
    '.lua',
    # Perl
    '.pl', '.pm', '.t',
    # Objective-C
    '.m', '.mm'
}

# Regex patterns for function detection
FUNCTION_PATTERNS = {
    'standard': r'(?:^|\s+)(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?function)',
    'arrow': r'(?:^|\s+)(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[^=])\s*=>',
    'method': r'\b(\w+)\s*:\s*(?:async\s*)?function',
    'class_method': r'(?:^|\s+)(?:async\s+)?(\w+)\s*\([^)]*\)\s*{',
    'object_property': r'(\w+)\s*:\s*(?:\([^)]*\)|[^=])\s*=>',
    'php_function': r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?function\s+(\w+)\s*\(',
    'php_class_method': r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?function\s+(\w+)\s*\(',
    'php_closure': r'\$(\w+)\s*=\s*function\s*\(',
    # Add C++ patterns
    'cpp_function': r'(?:virtual\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?(?:\w+(?:::\w+)*\s+)?(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?(?:final\s*)?(?:=\s*0\s*)?(?=\s*\{|;)',
    'cpp_method': r'(?:virtual\s+)?(?:explicit\s+)?(?:static\s+)?(?:inline\s+)?(?:const\s+)?(?:\w+(?:::\w+)*\s+)?(\w+)::\s*(\w+)\s*\([^)]*\)\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?(?:final\s*)?(?:=\s*0\s*)?(?=\s*\{|;)',
    
    # Add C# patterns  
    'csharp_method': r'(?:public|private|protected|internal|static|virtual|override|abstract|async)*\s+(?:\w+\s+)?(\w+)\s*\([^)]*\)\s*(?:where\s+[^{]+)?(?=\s*\{|;)',
    'csharp_property': r'(?:public|private|protected|internal)\s+(?:\w+\s+)?(\w+)\s*\{[^}]*\}',
    'csharp_event': r'(?:public|private|protected|internal)\s+event\s+\w+\s+(\w+)\s*;',
    
    # Rust patterns
    'rust_function': r'fn\s+(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)\s*(?:->\s*[^{]+)?\s*\{',
    'rust_method': r'impl\s+(?:[^{]+\s+)?for\s+[^{]+\{\s*(?:pub\s+)?fn\s+(\w+)',
    
    # Swift patterns
    'swift_function': r'func\s+(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)\s*(?:->\s*[^{]+)?\s*\{',
    'swift_method': r'(?:override\s+)?func\s+(\w+)',
    
    # Kotlin patterns
    'kotlin_function': r'fun\s+(\w+)\s*(?:<[^>]+>)?\s*\([^)]*\)\s*(?::\s*[^{]+)?\s*\{',
    'kotlin_method': r'(?:override\s+)?fun\s+(\w+)',
    
    # Dart patterns
    'dart_function': r'(?:void\s+)?(\w+)\s*\([^)]*\)\s*(?:async\s*)?\{',
    'dart_method': r'(?:@override\s+)?(?:void\s+)?(\w+)\s*\([^)]*\)\s*(?:async\s*)?\{',
    
    # Scala patterns
    'scala_function': r'def\s+(\w+)\s*(?:\[[^\]]+\])?\s*(?:\([^)]*\))?\s*(?::\s*[^=]+)?\s*=',
    'scala_method': r'(?:override\s+)?def\s+(\w+)',
    
    # R patterns
    'r_function': r'(\w+)\s*<-\s*function\s*\(',
    
    # MATLAB patterns
    'matlab_function': r'function\s+(?:\[?[^]]*\]?\s*=\s*)?(\w+)\s*\(',
    
    # Lua patterns
    'lua_function': r'function\s+(\w+)\s*\(',
    'lua_method': r'function\s+\w+[:.]\s*(\w+)\s*\(',
    
    # Perl patterns
    'perl_sub': r'sub\s+(\w+)\s*\{',
    
    # Objective-C patterns
    'objc_method': r'[-+]\s*\([^)]+\)\s*(\w+)\s*[:{]'
}

# Keywords that should not be treated as function names
IGNORED_KEYWORDS = {
    'if', 'switch', 'while', 'for', 'catch', 'finally', 'else', 'return',
    'break', 'continue', 'case', 'default', 'to', 'from', 'import', 'as',
    'try', 'except', 'raise', 'with', 'async', 'await', 'yield', 'assert',
    'pass', 'del', 'print', 'in', 'is', 'not', 'and', 'or', 'lambda',
    'global', 'nonlocal', 'class', 'def', 'n', 'lines', 'directly',
    # C++ keywords
    'class', 'struct', 'union', 'enum', 'template', 'typename', 'namespace',
    'operator', 'friend', 'using', 'typedef', 'decltype', 'constexpr',
    
    # C# keywords  
    'abstract', 'async', 'await', 'checked', 'const', 'event', 'extern',
    'fixed', 'goto', 'implicit', 'interface', 'internal', 'lock', 'namespace',
    'operator', 'out', 'override', 'params', 'readonly', 'ref', 'sealed',
    'sizeof', 'stackalloc', 'this', 'unsafe', 'virtual', 'volatile', 'where'
}

# Names of files and directories that should be ignored
IGNORED_NAMES = set(_config.get('ignored_directories', []))

FILE_LENGTH_STANDARDS = _config.get('file_length_standards', {})

def get_file_length_limit(file_path):
    """Get the recommended line limit for a given file type."""
    ext = os.path.splitext(file_path)[1].lower()
    return FILE_LENGTH_STANDARDS.get(ext, FILE_LENGTH_STANDARDS.get('default', 300)) 