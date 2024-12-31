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
            '.go': 'go',
            '.sh': 'shell',
            '.cpp': 'cpp',
            '.hpp': 'cpp',
            '.h': 'cpp',
            '.cc': 'cpp',
            '.cs': 'csharp',
            '.csproj': 'csharp'
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

        # Check composer.json for PHP frameworks
        composer_json_path = os.path.join(self.project_path, 'composer.json')
        if os.path.exists(composer_json_path):
            try:
                with open(composer_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('require', {}), **data.get('require-dev', {})}
                    
                    if 'laravel/framework' in deps:
                        return 'laravel'
                    if 'symfony/symfony' in deps:
                        return 'symfony'
                    if 'cakephp/cakephp' in deps:
                        return 'cakephp'
            except:
                pass

        # Check Gemfile for Ruby frameworks
        gemfile_path = os.path.join(self.project_path, 'Gemfile')
        if os.path.exists(gemfile_path):
            try:
                with open(gemfile_path, 'r') as f:
                    content = f.read().lower()
                    if 'rails' in content:
                        return 'rails'
                    if 'sinatra' in content:
                        return 'sinatra'
            except:
                pass

        # Check go.mod for Go frameworks
        go_mod_path = os.path.join(self.project_path, 'go.mod')
        if os.path.exists(go_mod_path):
            try:
                with open(go_mod_path, 'r') as f:
                    content = f.read().lower()
                    if 'gin-gonic/gin' in content:
                        return 'gin'
                    if 'gorilla/mux' in content:
                        return 'gorilla'
                    if 'echo' in content:
                        return 'echo'
            except:
                pass

        # Check for C++ frameworks
        cmake_path = os.path.join(self.project_path, 'CMakeLists.txt')
        if os.path.exists(cmake_path):
            try:
                with open(cmake_path, 'r') as f:
                    content = f.read().lower()
                    if 'qt' in content:
                        return 'qt'
                    if 'boost' in content:
                        return 'boost'
                    if 'opencv' in content:
                        return 'opencv'
            except:
                pass

        # Check for C# frameworks
        csproj_files = []
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.csproj'):
                    csproj_files.append(os.path.join(root, file))

        for csproj in csproj_files:
            try:
                with open(csproj, 'r') as f:
                    content = f.read().lower()
                    if 'microsoft.aspnetcore' in content:
                        return 'aspnet_core'
                    if 'microsoft.net.sdk.web' in content:
                        return 'aspnet_core'
                    if 'xamarin' in content:
                        return 'xamarin'
                    if 'microsoft.maui' in content:
                        return 'maui'
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

    def _analyze_shell_script(self, file_path: str) -> Dict:
        """Analyze shell script specific rules."""
        results = {
            'warnings': [],
            'suggestions': []
        }
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check for shebang
            if not content.startswith('#!/'):
                results['warnings'].append('Missing shebang line')
                results['suggestions'].append('Add #!/bin/bash or appropriate shebang')
                
            # Check for executable permission
            if not os.access(file_path, os.X_OK):
                results['warnings'].append('Script is not executable')
                results['suggestions'].append('Run: chmod +x script.sh')
                
            # Check for common shell script practices
            if 'set -e' not in content:
                results['suggestions'].append('Consider adding "set -e" for error handling')
                
            if 'set -u' not in content:
                results['suggestions'].append('Consider adding "set -u" for undefined variable checking')
                
        except Exception as e:
            results['warnings'].append(f'Error analyzing shell script: {str(e)}')
            
        return results 