import os
import json
import subprocess
from typing import Dict, List, Tuple

class DependencyAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        
    def analyze(self) -> Dict:
        """Analyze dependencies efficiently."""
        return {
            'direct': self._get_direct_dependencies(),
            'transitive': self._get_transitive_dependencies(),
            'outdated': [],
            'missing_tools': self._check_missing_tools()
        }

    def _get_direct_dependencies(self) -> Dict[str, str]:
        """Get direct dependencies from requirements.txt and setup.py."""
        direct_deps = {}
        
        # Check requirements.txt
        req_file = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(req_file):
            try:
                with open(req_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            if '>=' in line:
                                name, version = line.split('>=')
                                direct_deps[f"{name.strip()}>={version.strip()}"] = 'latest'
                            elif '==' in line:
                                name, version = line.split('==')
                                direct_deps[name.strip()] = version.strip()
                            else:
                                direct_deps[line.strip()] = 'latest'
            except Exception as e:
                print(f"⚠️ Warning: Could not read requirements.txt: {str(e)}")

        # Check setup.py
        setup_file = os.path.join(self.project_path, 'setup.py')
        if os.path.exists(setup_file):
            try:
                with open(setup_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Find install_requires
                    if 'install_requires=' in content:
                        # Simplify: only get explicit dependencies
                        import re
                        deps = re.findall(r"'([^']+)'", content)
                        for dep in deps:
                            if '>=' in dep:
                                name, version = dep.split('>=')
                                direct_deps[f"{name.strip()}>={version.strip()}"] = 'latest'
                            elif '==' in dep:
                                name, version = dep.split('==')
                                direct_deps[name.strip()] = version.strip()
                            else:
                                direct_deps[dep.strip()] = 'latest'
            except Exception as e:
                print(f"⚠️ Warning: Could not read setup.py: {str(e)}")

        return direct_deps

    def _get_transitive_dependencies(self) -> Dict[str, str]:
        """Get transitive dependencies from pip freeze."""
        trans_deps = {}
        try:
            import pkg_resources
            working_set = pkg_resources.WorkingSet()
            
            # Get direct deps first
            direct = set(self._get_direct_dependencies().keys())
            
            # Check all installed packages
            for dist in working_set:
                name = dist.key
                # If not a direct dependency
                if not any(name in d for d in direct):
                    for req in dist.requires():
                        spec = str(req.specifier) if req.specifier else ''
                        if spec:
                            trans_deps[req.name] = spec
        except Exception as e:
            print(f"⚠️ Warning: Could not analyze transitive dependencies: {str(e)}")
        
        return trans_deps

    def _check_missing_tools(self) -> List[str]:
        """Check for missing analysis tools."""
        missing = []
        
        try:
            import safety
        except ImportError:
            missing.append("Safety package not installed. Install with: pip install safety")
        
        try:
            import pip
        except ImportError:
            missing.append("pip not found in environment")
            
        return missing

    def generate_report(self) -> str:
        """Generate a Markdown report for dependencies."""
        deps = self.analyze()
        
        report = [
            "# Dependencies Analysis Report\n",
            "## Overview\n"
        ]
        
        # Missing Tools Section
        if deps['missing_tools']:
            report.extend([
                "### 🔧 Missing Analysis Tools",
                *[f"- {tool}" for tool in deps['missing_tools']],
                ""
            ])
        
        # Direct Dependencies Section
        report.extend([
            "### 📦 Direct Dependencies\n",
            "| Package | Version |",
            "|---------|---------|"
        ])
        
        if deps['direct']:
            for pkg, version in deps['direct'].items():
                report.append(f"| {pkg} | {version} |")
        else:
            report.append("| No direct dependencies found | - |")
        
        # Transitive Dependencies Section
        report.extend([
            "\n### 🔄 Transitive Dependencies\n",
            "| Package | Version Constraint |",
            "|---------|-------------------|"
        ])
        
        if deps['transitive']:
            for pkg, version in deps['transitive'].items():
                report.append(f"| {pkg} | {version} |")
        else:
            report.append("| No transitive dependencies found | - |")
        
        # Outdated Packages Section
        report.extend([
            "\n### ⚠️ Outdated Packages\n",
            "| Package | Current | Latest | Upgrade Command |",
            "|---------|---------|--------|-----------------|"
        ])
        
        if deps['outdated']:
            for pkg in deps['outdated']:
                report.append(
                    f"| {pkg['name']} | {pkg['current']} | {pkg['latest']} | `{pkg['upgrade_cmd']}` |"
                )
        else:
            report.append("| No outdated packages found | - | - | - |")
        
        return '\n'.join(report) 

    def _check_outdated_deps(self) -> List[Dict]:
        """Check for outdated dependencies."""
        return []  # Implement later if needed 