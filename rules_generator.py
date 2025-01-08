import os
from typing import Dict, Any, List
from datetime import datetime
import json


class RulesGenerator:
    def __init__(self, project_path: str):
        self.project_path = project_path
        template_dir = os.path.join(
            os.path.dirname(__file__), 'templates'
        )
        self.template_path = os.path.join(
            template_dir, 'default.cursorrules.json'
        )
        self.focus_template_path = os.path.join(template_dir, 'Focus.md')

    def _get_timestamp(self) -> str:
        """Get current timestamp in standard format."""
        return datetime.now().strftime('%B %d, %Y at %I:%M %p')

    def _load_project_info(self) -> str:
        """Load project info from project_info.mdx if it exists."""
        project_info_path = os.path.join(self.project_path, 'project_info.mdx')
        if not os.path.exists(project_info_path):
            return ""

        try:
            with open(project_info_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            print(f"Error loading project_info.mdx: {e}")
            return ""

    def _get_framework_rules(
        self, framework: str, is_frontend: bool = False
    ) -> List[str]:
        """Get framework-specific coding rules.

        Args:
            framework: Framework name
            is_frontend: Whether this is a frontend framework
        """
        frontend_rules = {
            'react': [
                'use functional components over class components',
                'prefer hooks for state management',
                'use memo for performance optimization',
                'implement proper component lifecycle',
                'use proper state management (Redux/Context)',
                'implement responsive design principles',
                'follow React best practices for forms',
                'use proper routing (React Router)',
                'implement proper error boundaries',
                'use proper code splitting and lazy loading'
            ],
            'vue': [
                'use composition API',
                'prefer ref/reactive for state management',
                'use script setup syntax',
                'implement proper component lifecycle',
                'use Vuex/Pinia for state management',
                'follow Vue.js style guide',
                'use proper routing (Vue Router)',
                'implement proper error handling',
                'use proper code splitting',
                'implement proper component communication'
            ],
            'angular': [
                'follow angular style guide',
                'use observables for async operations',
                'implement lifecycle hooks properly',
                'use proper dependency injection',
                'implement proper routing strategy',
                'use proper state management (NgRx)',
                'follow proper module organization',
                'implement proper form validation',
                'use proper change detection strategy',
                'implement proper error handling'
            ],
            'nextjs': [
                'use server-side rendering appropriately',
                'implement proper data fetching strategies',
                'use static site generation when possible',
                'implement proper routing and navigation',
                'use proper image optimization',
                'implement proper API routes',
                'use proper environment variables',
                'implement proper error handling and 404 pages',
                'use proper dynamic imports and code splitting',
                'implement proper SEO optimization',
                'use proper caching strategies',
                'implement proper authentication flows',
                'use proper middleware when needed',
                'follow Next.js best practices for performance'
            ]
        }

        backend_rules = {
            'flask': [
                'use Flask blueprints for organization',
                'implement proper error handling',
                'use Flask-SQLAlchemy for database operations',
                'implement proper request validation',
                'use proper authentication/authorization',
                'implement proper caching',
                'use proper configuration management',
                'implement proper logging',
                'use proper session handling',
                'follow RESTful API best practices'
            ],
            'fastapi': [
                'use Pydantic models for request/response validation',
                'leverage async/await for better performance',
                'implement proper dependency injection',
                'use proper status codes and error responses',
                'follow OpenAPI/Swagger documentation standards',
                'implement proper middleware for cross-cutting concerns',
                'use proper security practices (OAuth2, JWT, etc.)',
                'implement proper rate limiting and throttling',
                'use background tasks for long-running operations',
                'implement proper CORS handling'
            ]
        }

        rules = frontend_rules if is_frontend else backend_rules
        return rules.get(framework.lower(), [])

    def _get_language_rules(self, language: str) -> List[str]:
        """Get language-specific coding rules."""
        language_rules = {
            'python': [
                'follow PEP 8 guidelines',
                'use type hints',
                'prefer list comprehension when appropriate',
                'use proper exception handling',
                'implement proper logging',
                'use proper package structure',
                'follow SOLID principles',
                'use proper docstrings',
                'implement proper testing',
                'use proper dependency management'
            ],
            'javascript': [
                'use modern ES features',
                'prefer arrow functions',
                'use optional chaining',
                'implement proper error handling',
                'use proper module system',
                'follow proper naming conventions',
                'use proper async/await patterns',
                'implement proper testing',
                'use proper package management',
                'follow clean code principles'
            ],
            'typescript': [
                'use strict type checking',
                'leverage type inference',
                'use interface over type when possible',
                'implement proper error handling',
                'use proper decorators',
                'follow proper naming conventions',
                'use proper generics',
                'implement proper testing',
                'use proper module system',
                'follow TypeScript best practices'
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
                    deps = {
                        **data.get('dependencies', {}),
                        **data.get('devDependencies', {})
                    }

                    if 'jest' in deps:
                        testing_frameworks.append('jest')
                    if 'mocha' in deps:
                        testing_frameworks.append('mocha')
                    if '@testing-library/react' in deps:
                        testing_frameworks.append('testing-library')
            except IOError as e:
                print(f"Error reading package.json: {e}")

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
            except IOError as e:
                print(f"Error reading requirements.txt: {e}")

        return testing_frameworks if testing_frameworks else ['jest']

    def generate_rules_file(self, project_info: Dict[str, Any]) -> str:
        """Generate the .cursorrules file based on project analysis."""
        # Load project_info.mdx
        manual_info = self._load_project_info()

        # Get frontend and backend frameworks
        frontend_framework = project_info.get('frontend_framework', '')
        backend_framework = project_info.get('backend_framework', '')

        # Combine manual and auto-generated content
        combined_content = f"""<cursorrules>

<metadata>
    <version>1.0</version>
    <last_updated>{self._get_timestamp()}</last_updated>
</metadata>

<project_analysis>
    <basic_info>
        <name>{project_info['name']}</name>
        <version>{project_info.get('version', '1.0.0')}</version>
        <language>{project_info['language']}</language>
        <frontend_framework>{frontend_framework}</frontend_framework>
        <backend_framework>{backend_framework}</backend_framework>
        <type>{project_info['type']}</type>
    </basic_info>

    <ai_behavior>
        <code_generation>
            <style>
                <prefer>
                    {self._list_to_mdx(
                        self._get_language_rules(project_info['language'])
                    )}
                    {self._list_to_mdx(
                        self._get_framework_rules(frontend_framework, True)
                    ) if frontend_framework else ''}
                    {self._list_to_mdx(
                        self._get_framework_rules(backend_framework, False)
                    ) if backend_framework else ''}
                </prefer>
                <avoid>
                    - magic numbers
                    - nested callbacks
                    - hard-coded values
                    - complex conditionals
                </avoid>
            </style>
            <error_handling>
                <prefer>
                    - try/catch for async operations
                    - custom error messages
                    - meaningful error states
                </prefer>
                <avoid>
                    - silent errors
                    - empty catch blocks
                    - generic error messages
                </avoid>
            </error_handling>
            <performance>
                <prefer>
                    - lazy loading
                    - debouncing and throttling for events
                    - memoization for expensive calculations
                </prefer>
                <avoid>
                    - blocking synchronous code
                    - large inline scripts
                    - unnecessary re-renders
                </avoid>
            </performance>
        </code_generation>

        <testing>
            <frameworks>
                {self._list_to_mdx(self._detect_testing_frameworks())}
            </frameworks>
            <coverage_threshold>80</coverage_threshold>
            <requirements>
                - unit tests for new functions
                - integration tests for critical workflows
                - edge case scenarios
            </requirements>
        </testing>

        {self._get_project_type_rules_mdx(project_info['type'])}
    </ai_behavior>

    <communication>
        <style>step-by-step</style>
        <level>beginner-friendly</level>
        <on_error>
            - log error details
            - suggest alternative solutions
            - ask for clarification if unsure
        </on_error>
        <on_success>
            - summarize changes
            - provide context for future improvements
            - highlight any potential optimizations
        </on_success>
    </communication>
</project_analysis>

{manual_info}

</cursorrules>"""

        # Write to file
        rules_file = os.path.join(self.project_path, '.cursorrules')
        with open(rules_file, 'w', encoding='utf-8') as f:
            f.write(combined_content)

        return rules_file

    def _list_to_mdx(self, items: List[str]) -> str:
        """Convert a list to MDX bullet points."""
        return '\n                    '.join(f'- {item}' for item in items)

    def _get_project_type_rules_mdx(self, project_type: str) -> str:
        """Get project-type specific rules in MDX format."""
        type_rules = {
            'web application': '''
        <accessibility>
            <required>true</required>
            <standards>
                - WCAG 2.1
            </standards>
        </accessibility>
        <performance>
            <prefer>
                - code splitting
                - lazy loading
                - performance monitoring
            </prefer>
        </performance>''',
            'mobile application': '''
        <performance>
            <prefer>
                - offline first
                - battery optimization
                - responsive design
            </prefer>
        </performance>''',
            'library': '''
        <documentation>
            <required>true</required>
        </documentation>
        <testing>
            <coverage_threshold>90</coverage_threshold>
        </testing>'''
        }

        return type_rules.get(project_type.lower(), '')
