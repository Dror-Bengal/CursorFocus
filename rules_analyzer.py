import os
import json
from typing import Dict, Any, Tuple


class RulesAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path

    def analyze_project_for_rules(self) -> Dict[str, Any]:
        """Analyze the project and return project information for rules."""
        language = self._detect_main_language()
        frontend_framework, backend_framework = self._detect_frameworks()

        project_info = {
            'name': self._detect_project_name(),
            'version': self._detect_version(),
            'language': language,
            'frontend_framework': frontend_framework,
            'backend_framework': backend_framework,
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
            except IOError as e:
                print(f"Error reading package.json: {e}")

        # Try setup.py
        setup_py_path = os.path.join(self.project_path, 'setup.py')
        if os.path.exists(setup_py_path):
            try:
                with open(setup_py_path, 'r') as f:
                    content = f.read()
                    if 'name=' in content:
                        # Extract name from setup.py
                        name = (
                            content.split('name=')[1]
                            .split(',')[0].strip("'\"")
                        )
                        if name:
                            return name
            except IOError as e:
                print(f"Error reading setup.py: {e}")

        # Try pyproject.toml
        pyproject_path = os.path.join(self.project_path, 'pyproject.toml')
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path, 'r') as f:
                    content = f.read()
                    if 'name =' in content:
                        # Extract name from pyproject.toml
                        name = (
                            content.split('name =')[1]
                            .split('\n')[0].strip(' "\'')
                        )
                        if name:
                            return name
            except IOError as e:
                print(f"Error reading pyproject.toml: {e}")

        # Default to directory name
        return os.path.basename(os.path.abspath(self.project_path))

    def _detect_version(self) -> str:
        """Detect project version from various config files."""
        # Try package.json
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    if data.get('version'):
                        return data['version']
            except IOError as e:
                print(f"Error reading package.json: {e}")

        # Try setup.py
        setup_py_path = os.path.join(self.project_path, 'setup.py')
        if os.path.exists(setup_py_path):
            try:
                with open(setup_py_path, 'r') as f:
                    content = f.read()
                    if 'version=' in content:
                        # Extract version from setup.py
                        version = (
                            content.split('version=')[1]
                            .split(',')[0].strip("'\"")
                        )
                        if version:
                            return version
            except IOError as e:
                print(f"Error reading setup.py: {e}")

        return '1.0.0'  # Default version

    def _detect_main_language(self) -> str:
        """Detect the main programming language used in the project."""
        extensions = {}

        ignored_dirs = [
            'node_modules', 'venv', '.git', '__pycache__',
            'build', 'dist', '.pytest_cache'
        ]

        for root, _, files in os.walk(self.project_path):
            if any(ignored in root for ignored in ignored_dirs):
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
            '.vue': 'javascript',
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

    def _detect_frameworks(self) -> Tuple[str, str]:
        """Detect both frontend and backend frameworks used in the project."""
        frontend_framework = 'none'
        backend_framework = 'none'

        # Check package.json for frontend frameworks
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {
                        **data.get('dependencies', {}),
                        **data.get('devDependencies', {})
                    }

                    # Frontend framework detection
                    if 'next' in deps:
                        frontend_framework = 'nextjs'
                    elif 'react' in deps:
                        frontend_framework = 'react'
                    elif 'vue' in deps:
                        frontend_framework = 'vue'
                    elif '@angular/core' in deps:
                        frontend_framework = 'angular'
            except IOError as e:
                print(f"Error reading package.json: {e}")

        # Check requirements.txt for backend frameworks
        requirements_path = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r') as f:
                    content = f.read().lower()
                    if 'fastapi' in content:
                        backend_framework = 'fastapi'
                    elif 'flask' in content:
                        backend_framework = 'flask'
            except IOError as e:
                print(f"Error reading requirements.txt: {e}")

        # Check pyproject.toml for backend frameworks
        pyproject_path = os.path.join(self.project_path, 'pyproject.toml')
        if os.path.exists(pyproject_path):
            try:
                with open(pyproject_path, 'r') as f:
                    content = f.read().lower()
                    if 'fastapi' in content:
                        backend_framework = 'fastapi'
                    elif 'flask' in content:
                        backend_framework = 'flask'
            except IOError as e:
                print(f"Error reading pyproject.toml: {e}")

        return frontend_framework, backend_framework

    def _detect_project_type(self) -> str:
        """Detect the type of project (web, mobile, library, etc.)."""
        package_json_path = os.path.join(self.project_path, 'package.json')

        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {
                        **data.get('dependencies', {}),
                        **data.get('devDependencies', {})
                    }

                    # Check for mobile frameworks
                    if 'react-native' in deps or '@ionic/core' in deps:
                        return 'mobile application'

                    # Check for desktop frameworks
                    if 'electron' in deps:
                        return 'desktop application'

                    # Check if it's a library
                    if (data.get('name', '').startswith('@') or
                            '-lib' in data.get('name', '')):
                        return 'library'
            except IOError as e:
                print(f"Error reading package.json: {e}")

        # Look for common web project indicators
        web_indicators = ['index.html', 'public/index.html', 'src/index.html']
        for indicator in web_indicators:
            if os.path.exists(os.path.join(self.project_path, indicator)):
                return 'web application'

        # Check for Python library indicators
        setup_py_path = os.path.join(self.project_path, 'setup.py')
        if os.path.exists(setup_py_path):
            return 'library'

        return 'application'
