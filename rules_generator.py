import os
import json
from typing import Dict, Any, List
from datetime import datetime

class RulesGenerator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.template_path = os.path.join(os.path.dirname(__file__), 'templates', 'default.cursorrules.json')
        self.focus_template_path = os.path.join(os.path.dirname(__file__), 'templates', 'Focus.md')

    def _get_timestamp(self) -> str:
        """Get current timestamp in standard format."""
        return datetime.now().strftime('%B %d, %Y at %I:%M %p')

    def generate_rules_file(self, project_info: Dict[str, Any]) -> str:
        """Generate the .cursorrules file based on project analysis."""
        # Load template
        template = self._load_template()
        
        # Customize template
        rules = self._customize_template(template, project_info)
        
        # Write to file
        rules_file = os.path.join(self.project_path, '.cursorrules')
        with open(rules_file, 'w', encoding='utf-8') as f:
            json.dump(rules, f, indent=2)
            
        return rules_file

    def _load_template(self) -> Dict[str, Any]:
        """Load the default template."""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading template: {e}")
            return self._get_default_template()

    def _customize_template(self, template: Dict[str, Any], project_info: Dict[str, Any]) -> Dict[str, Any]:
        """Customize the template based on project analysis."""
        rules = template.copy()
        
        # Add timestamp first
        rules['last_updated'] = self._get_timestamp()
        
        # Update project info
        rules['project'].update(project_info)
        
        # Add framework-specific rules
        if project_info['framework'] != 'none':
            framework_rules = self._get_framework_rules(project_info['framework'])
            rules['ai_behavior']['code_generation']['style']['prefer'].extend(framework_rules)
        
        # Add language-specific rules
        language_rules = self._get_language_rules(project_info['language'])
        rules['ai_behavior']['code_generation']['style']['prefer'].extend(language_rules)
        
        # Add project-type specific rules
        self._add_project_type_rules(rules, project_info['type'])
        
        # Update testing frameworks
        rules['ai_behavior']['testing']['frameworks'] = self._detect_testing_frameworks()
        
        return rules

    def _get_framework_rules(self, framework: str) -> List[str]:
        """Get framework-specific coding rules."""
        framework_rules = {
            'react': [
                'use functional components over class components',
                'prefer hooks for state management',
                'use memo for performance optimization'
            ],
            'vue': [
                'use composition API',
                'prefer ref/reactive for state management',
                'use script setup syntax'
            ],
            'angular': [
                'follow angular style guide',
                'use observables for async operations',
                'implement lifecycle hooks properly'
            ],
            'django': [
                'follow Django best practices',
                'use class-based views when appropriate',
                'implement proper model relationships'
            ],
            'flask': [
                'use Flask blueprints for organization',
                'implement proper error handling',
                'use Flask-SQLAlchemy for database operations'
            ]
        }
        return framework_rules.get(framework.lower(), [])

    def _get_language_rules(self, language: str) -> List[str]:
        """Get language-specific coding rules."""
        language_rules = {
            'python': [
                'follow PEP 8 guidelines',
                'use type hints',
                'prefer list comprehension when appropriate'
            ],
            'javascript': [
                'use modern ES features',
                'prefer arrow functions',
                'use optional chaining'
            ],
            'typescript': [
                'use strict type checking',
                'leverage type inference',
                'use interface over type when possible'
            ]
        }
        return language_rules.get(language.lower(), [])

    def _detect_testing_frameworks(self) -> List[str]:
        """Detect testing frameworks used in the project."""
        testing_frameworks = []
        
        # Check package.json for JS/TS testing frameworks
        package_json_path = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r') as f:
                    data = json.load(f)
                    deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
                    
                    if 'jest' in deps:
                        testing_frameworks.append('jest')
                    if 'mocha' in deps:
                        testing_frameworks.append('mocha')
                    if '@testing-library/react' in deps:
                        testing_frameworks.append('testing-library')
            except:
                pass

        # Check requirements.txt for Python testing frameworks
        requirements_path = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(requirements_path):
            try:
                with open(requirements_path, 'r') as f:
                    content = f.read().lower()
                    if 'pytest' in content:
                        testing_frameworks.append('pytest')
                    if 'unittest' in content:
                        testing_frameworks.append('unittest')
            except:
                pass

        return testing_frameworks if testing_frameworks else ['jest']  # Default to jest

    def _add_project_type_rules(self, rules: Dict[str, Any], project_type: str):
        """Add project-type specific rules."""
        type_rules = {
            'web application': {
                'accessibility': {'required': True},
                'performance': {
                    'prefer': [
                        'code splitting',
                        'lazy loading',
                        'performance monitoring'
                    ]
                }
            },
            'mobile application': {
                'performance': {
                    'prefer': [
                        'offline first',
                        'battery optimization',
                        'responsive design'
                    ]
                }
            },
            'library': {
                'documentation': {'required': True},
                'testing': {'coverage_threshold': 90}
            }
        }
        
        specific_rules = type_rules.get(project_type.lower())
        if specific_rules:
            rules['ai_behavior'].update(specific_rules)

    def _get_default_template(self) -> Dict[str, Any]:
        """Get a default template if the template file cannot be loaded."""
        return {
            "version": "1.0",
            "last_updated": self._get_timestamp(),
            "project": {
                "name": "Unknown Project",
                "version": "1.0.0",
                "language": "javascript",
                "framework": "none",
                "type": "application"
            },
            "ai_behavior": {
                "code_generation": {
                    "style": {
                        "prefer": [],
                        "avoid": [
                            "magic numbers",
                            "nested callbacks",
                            "hard-coded values"
                        ]
                    }
                },
                "testing": {
                    "required": True,
                    "frameworks": ["jest"],
                    "coverage_threshold": 80
                }
            }
        } 