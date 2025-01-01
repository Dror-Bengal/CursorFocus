import os
import json
import subprocess
import logging
from typing import Dict, List, Tuple
from collections import defaultdict

class DependencyAnalyzer:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.dependency_files = {
            'python': ['requirements.txt', 'Pipfile', 'pyproject.toml', 'setup.py'],
            'node': ['package.json', 'yarn.lock', 'package-lock.json'],
            'ruby': ['Gemfile', 'Gemfile.lock'],
            'php': ['composer.json', 'composer.lock']
        }

    def analyze(self) -> Dict:
        """Analyze project dependencies."""
        try:
            dependencies = {
                'direct': defaultdict(list),
                'dev': defaultdict(list),
                'outdated': [],
                'security_alerts': [],
                'stats': {
                    'total_dependencies': 0,
                    'direct_dependencies': 0,
                    'dev_dependencies': 0,
                    'outdated_count': 0
                }
            }

            # Detect project type and analyze dependencies
            for lang, files in self.dependency_files.items():
                for file in files:
                    file_path = os.path.join(self.project_path, file)
                    if os.path.exists(file_path):
                        self._analyze_dependency_file(file_path, lang, dependencies)
                        break  # Only analyze first found dependency file per language

            # Check for outdated dependencies
            self._check_outdated_dependencies(dependencies)
            
            # Check for security vulnerabilities
            self._check_security_vulnerabilities(dependencies)

            return dependencies

        except Exception as e:
            logging.error(f"Error analyzing dependencies: {str(e)}")
            return self._get_empty_analysis()

    def _analyze_dependency_file(self, file_path: str, lang: str, dependencies: Dict) -> None:
        """Analyze a specific dependency file."""
        try:
            if lang == 'node':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    deps = data.get('dependencies', {})
                    dev_deps = data.get('devDependencies', {})
                    
                    dependencies['direct'][lang].extend(deps.items())
                    dependencies['dev'][lang].extend(dev_deps.items())
                    
                    dependencies['stats']['direct_dependencies'] += len(deps)
                    dependencies['stats']['dev_dependencies'] += len(dev_deps)
                    
            elif lang == 'python':
                if file_path.endswith('requirements.txt'):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            if line.strip() and not line.startswith('#'):
                                dependencies['direct'][lang].append(line.strip())
                                dependencies['stats']['direct_dependencies'] += 1

            # Update total dependencies count
            dependencies['stats']['total_dependencies'] = (
                dependencies['stats']['direct_dependencies'] + 
                dependencies['stats']['dev_dependencies']
            )

        except Exception as e:
            logging.warning(f"Error analyzing dependency file {file_path}: {str(e)}")

    def _check_outdated_dependencies(self, dependencies: Dict) -> None:
        """Check for outdated dependencies using appropriate package manager."""
        try:
            if os.path.exists(os.path.join(self.project_path, 'package.json')):
                # Use npm to check outdated packages
                result = subprocess.run(
                    ['npm', 'outdated', '--json'],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )
                if result.stdout:
                    outdated = json.loads(result.stdout)
                    for pkg, info in outdated.items():
                        dependencies['outdated'].append({
                            'package': pkg,
                            'current': info.get('current', ''),
                            'latest': info.get('latest', ''),
                            'type': 'npm'
                        })
                        
            dependencies['stats']['outdated_count'] = len(dependencies['outdated'])

        except Exception as e:
            logging.warning(f"Error checking outdated dependencies: {str(e)}")

    def _check_security_vulnerabilities(self, dependencies: Dict) -> None:
        """Check for known security vulnerabilities in dependencies."""
        try:
            if os.path.exists(os.path.join(self.project_path, 'package.json')):
                result = subprocess.run(
                    ['npm', 'audit', '--json'],
                    capture_output=True,
                    text=True,
                    cwd=self.project_path
                )
                if result.stdout:
                    audit_data = json.loads(result.stdout)
                    for vuln in audit_data.get('vulnerabilities', {}).values():
                        dependencies['security_alerts'].append({
                            'package': vuln.get('name'),
                            'severity': vuln.get('severity'),
                            'description': vuln.get('description'),
                            'recommendation': vuln.get('recommendation', 'Update to latest version')
                        })

        except Exception as e:
            logging.warning(f"Error checking security vulnerabilities: {str(e)}")

    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure when analysis fails."""
        return {
            'direct': defaultdict(list),
            'dev': defaultdict(list),
            'outdated': [],
            'security_alerts': [],
            'stats': {
                'total_dependencies': 0,
                'direct_dependencies': 0,
                'dev_dependencies': 0,
                'outdated_count': 0
            }
        } 

    def generate_report(self) -> str:
        """Generate a Markdown report about dependencies."""
        data = self.analyze()
        
        report = [
            "# Dependency Analysis Report\n",
            
            "## 📦 Dependencies Overview\n",
            f"- Total Dependencies: {data['stats']['total_dependencies']}",
            f"- Direct Dependencies: {data['stats']['direct_dependencies']}",
            f"- Dev Dependencies: {data['stats']['dev_dependencies']}",
            f"- Outdated Dependencies: {data['stats']['outdated_count']}",
            
            "\n## 🔍 Direct Dependencies"
        ]
        
        # Add direct dependencies by language
        for lang, deps in data['direct'].items():
            if deps:
                report.extend([
                    f"\n### {lang.title()}",
                    "| Package | Version |",
                    "|---------|----------|"
                ])
                for dep in deps:
                    if isinstance(dep, tuple):  # Node.js dependencies
                        report.append(f"| {dep[0]} | {dep[1]} |")
                    else:  # Python requirements
                        report.append(f"| {dep} | - |")
        
        # Add outdated dependencies section
        if data['outdated']:
            report.extend([
                "\n## ⚠️ Outdated Dependencies",
                "| Package | Current | Latest | Type |",
                "|---------|----------|---------|------|"
            ])
            for dep in data['outdated']:
                report.append(
                    f"| {dep['package']} | {dep['current']} | {dep['latest']} | {dep['type']} |"
                )
        
        # Add security alerts section
        if data['security_alerts']:
            report.extend([
                "\n## 🚨 Security Alerts",
                "| Package | Severity | Description | Recommendation |",
                "|---------|-----------|-------------|----------------|"
            ])
            for alert in data['security_alerts']:
                report.append(
                    f"| {alert['package']} | {alert['severity']} | {alert['description']} | "
                    f"{alert['recommendation']} |"
                )
        
        return '\n'.join(report) 