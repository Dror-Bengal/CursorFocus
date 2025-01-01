import os
import json
from typing import Dict, Any
import re
import math

class RulesAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path

    def analyze_project_for_rules(self) -> Dict[str, Any]:
        """Analyze the project and return project information for rules generation."""
        project_info = {
            'name': self._detect_project_name(),
            'version': '1.0.0',
            'language': self._detect_main_language(),
            'framework': self._detect_framework(),
            'type': self._detect_project_type()
        }
        return project_info

    def _detect_project_name(self) -> str:
        """Detect the project name from package files or directory name."""
        # Try package.json
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    if data.get('name'):
                        return data['name']
            except:
                pass

        # Try setup.py
        setup_py_path = os.path.join(self.project_path, 'setup.py')
        if os.path.exists(setup_py_path):
            try:
                with open(setup_py_path, 'r') as f:
                    content = f.read()
                    if 'name=' in content:
                        # Simple extraction, could be improved
                        name = content.split('name=')[1].split(',')[0].strip("'\"")
                        if name:
                            return name
            except:
                pass

        # Default to directory name
        return os.path.basename(os.path.abspath(self.project_path))

    def _detect_main_language(self) -> str:
        """Detect the main programming language used in the project."""
        extensions = {}
        
        # Enhanced ignore paths with common build/cache directories
        ignore_paths = {
            'node_modules', 'venv', '.git', 'dist', 'build', '__pycache__', 
            '.idea', '.vscode', 'vendor', 'target', 'bin', 'obj', 'out',
            'coverage', '.next', '.nuxt', '.cache', 'tmp', 'temp'
        }
        
        # Track total file size per extension for better weighting
        extension_sizes = {}
        
        for root, _, files in os.walk(self.project_path):
            if any(ignore in root.split(os.sep) for ignore in ignore_paths):
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1
                    try:
                        file_size = os.path.getsize(os.path.join(root, file))
                        extension_sizes[ext] = extension_sizes.get(ext, 0) + file_size
                    except OSError:
                        continue

        # Enhanced language mapping with metadata
        language_map = {
            # Python ecosystem
            '.py': {'lang': 'python', 'weight': 1.0, 'type': 'source'},
            '.pyw': {'lang': 'python', 'weight': 0.8, 'type': 'source'},
            '.pyx': {'lang': 'python', 'weight': 0.7, 'type': 'source'},
            '.pxd': {'lang': 'python', 'weight': 0.6, 'type': 'header'},
            '.pyi': {'lang': 'python', 'weight': 0.5, 'type': 'interface'},
            
            # JavaScript/TypeScript ecosystem
            '.js': {'lang': 'javascript', 'weight': 1.0, 'type': 'source'},
            '.jsx': {'lang': 'javascript', 'weight': 1.0, 'type': 'source'},
            '.mjs': {'lang': 'javascript', 'weight': 0.9, 'type': 'module'},
            '.ts': {'lang': 'typescript', 'weight': 1.0, 'type': 'source'},
            '.tsx': {'lang': 'typescript', 'weight': 1.0, 'type': 'source'},
            
            # PHP ecosystem
            '.php': {'lang': 'php', 'weight': 1.0, 'type': 'source'},
            '.phtml': {'lang': 'php', 'weight': 0.8, 'type': 'template'},
            '.php5': {'lang': 'php', 'weight': 0.9, 'type': 'source'},
            '.phps': {'lang': 'php', 'weight': 0.7, 'type': 'source'},
            '.php4': {'lang': 'php', 'weight': 0.6, 'type': 'source'},
            '.php3': {'lang': 'php', 'weight': 0.5, 'type': 'source'},
            
            # Other languages...
            '.rb': {'lang': 'ruby', 'weight': 1.0, 'type': 'source'},
            '.java': {'lang': 'java', 'weight': 1.0, 'type': 'source'},
            '.go': {'lang': 'go', 'weight': 1.0, 'type': 'source'},
            '.cs': {'lang': 'csharp', 'weight': 1.0, 'type': 'source'},
        }

        # Calculate weighted scores considering file size and type
        language_scores = {}
        
        for ext, count in extensions.items():
            if ext in language_map:
                lang_info = language_map[ext]
                lang = lang_info['lang']
                weight = lang_info['weight']
                
                # Calculate score based on count, size and weight
                base_score = count * weight
                size_factor = math.log(extension_sizes.get(ext, 0) + 1) / 10
                score = base_score + size_factor
                
                language_scores[lang] = language_scores.get(lang, 0) + score

        # Enhanced project indicators with framework detection
        indicators = {
            'php': [
                ('composer.json', 3, True),      # Required file
                ('composer.lock', 2, False),     # Optional file
                ('artisan', 2, False),           # Laravel
                ('.php-version', 1, False),
                ('wp-config.php', 2, False),     # WordPress
                ('index.php', 1, False)
            ],
            'javascript': [
                ('package.json', 3, True),
                ('package-lock.json', 2, False),
                ('node_modules', 2, False),
                ('.nvmrc', 1, False),
                ('.eslintrc', 1, False),
                ('webpack.config.js', 2, False)
            ],
        }

        # Check for required indicators and adjust scores
        for lang, files in indicators.items():
            required_files_present = True
            score = 0
            
            for file_name, weight, required in files:
                file_path = os.path.join(self.project_path, file_name)
                if os.path.exists(file_path):
                    score += weight * 2
                elif required:
                    required_files_present = False
                    
            if required_files_present and score > 0:
                language_scores[lang] = language_scores.get(lang, 0) + score

        # Enhanced content analysis with more patterns and weighting
        content_patterns = {
            'php': [
                (r'<\?php', 2),                    # PHP opening tag
                (r'namespace\s+[\w\\]+', 1.5),     # Namespace declaration
                (r'use\s+[\w\\]+', 1),             # Use statement
                (r'class\s+\w+', 1.5),             # Class definition
                (r'function\s+\w+', 1)             # Function definition
            ],
            'python': [
                (r'import\s+[\w.]+', 1),
                (r'from\s+[\w.]+\s+import', 1),
                (r'def\s+\w+\s*\(', 1.5),
                (r'class\s+\w+[:\(]', 1.5)
            ],
            # ... other languages ...
        }

        # Improved content analysis with caching
        analyzed_contents = {}
        
        for lang, patterns in content_patterns.items():
            score = 0
            files_checked = 0
            
            for root, _, files in os.walk(self.project_path):
                if files_checked >= 5:
                    break
                    
                for file in files:
                    if file.endswith(tuple(ext for ext, info in language_map.items() 
                                   if info['lang'] == lang)):
                        file_path = os.path.join(root, file)
                        
                        # Use cached content if available
                        if file_path not in analyzed_contents:
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    analyzed_contents[file_path] = f.read()
                            except (UnicodeDecodeError, IOError):
                                continue
                        
                        content = analyzed_contents[file_path]
                        for pattern, weight in patterns:
                            if re.search(pattern, content):
                                score += weight
                        
                        files_checked += 1

            if score > 0:
                language_scores[lang] = language_scores.get(lang, 0) + score

        # Final language determination with confidence score
        if language_scores:
            items = sorted(language_scores.items(), key=lambda x: x[1], reverse=True)
            main_language = items[0][0]
            
            # Calculate confidence
            total_score = sum(score for _, score in items)
            confidence = (items[0][1] / total_score) if total_score > 0 else 0
            
            # Return unknown if confidence is too low
            if confidence < 0.4:
                return 'unknown'
            
            return main_language
        
        return 'unknown'

    def _detect_framework(self) -> str:
        """Detect the framework used in the project."""
        # Check for Bun via bunfig.toml or bun.toml
        bun_config_paths = [
            os.path.join(self.project_path, 'bunfig.toml'),
            os.path.join(self.project_path, 'bun.toml')
        ]
        if any(os.path.exists(path) for path in bun_config_paths) or \
           os.path.exists(os.path.join(self.project_path, 'bun.lockb')):
            return 'bun'

        # Check package.json for JS/TS frameworks
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    # Add Bun detection
                    if 'bun' in deps or os.path.exists(os.path.join(self.project_path, 'bun.lockb')):
                        return 'bun'
                        
                    if 'react' in deps:
                        return 'react'
                    if 'vue' in deps:
                        return 'vue'
                    if '@angular/core' in deps:
                        return 'angular'
                    if 'next' in deps:
                        return 'next.js'
                    if 'express' in deps:
                        return 'express'
            except:
                pass

        # Check requirements.txt for Python frameworks
        requirements_path = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r') as f:
                    content = f.read().lower()
                    if 'django' in content:
                        return 'django'
                    if 'flask' in content:
                        return 'flask'
                    if 'fastapi' in content:
                        return 'fastapi'
            except:
                pass

        return 'none'

    def _detect_project_type(self) -> str:
        """Detect the type of project (web, mobile, library, etc.)."""
        package_json_path = os.path.join(self.project_path, 'package.json')
        
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    # Check for mobile frameworks
                    if 'react-native' in deps or '@ionic/core' in deps:
                        return 'mobile application'
                    
                    # Check for desktop frameworks
                    if 'electron' in deps:
                        return 'desktop application'
                    
                    # Check if it's a library
                    if data.get('name', '').startswith('@') or '-lib' in data.get('name', ''):
                        return 'library'
            except:
                pass

        # Look for common web project indicators
        web_indicators = ['index.html', 'public/index.html', 'src/index.html']
        for indicator in web_indicators:
            if os.path.exists(os.path.join(self.project_path, indicator)):
                return 'web application'

        return 'application' 