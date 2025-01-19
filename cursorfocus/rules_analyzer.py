import os
import json
from typing import Dict, Any

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
        
        for root, _, files in os.walk(self.project_path):
            if 'node_modules' in root or 'venv' in root or '.git' in root:
                continue
                
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

        # Map extensions to languages
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.rb': 'ruby',
            '.php': 'php',
            '.go': 'go'
        }

        # Find the most common language
        max_count = 0
        main_language = 'javascript'  # default
        
        for ext, count in extensions.items():
            if ext in language_map and count > max_count:
                max_count = count
                main_language = language_map[ext]

        return main_language

    def _detect_framework(self) -> str:
        """Detect the framework used in the project."""
        # Check package.json for JS/TS frameworks
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
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