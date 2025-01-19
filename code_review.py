import os
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import re
from collections import defaultdict
import time
from difflib import SequenceMatcher

class CodeReviewGenerator:
    def __init__(self, api_key: str):
        self.api_key = api_key
        
    def read_file_content(self, file_path: str) -> str:
        """Read content of a specific file"""
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            logging.error(f"Error reading file {file_path}: {str(e)}")
            return ""

    def get_relevant_files(self, project_path: str) -> List[str]:
        """Get list of relevant files for review"""
        ignored = {'.git', 'node_modules', '.next', 'dist', 'build', 'coverage'}
        files = []
        
        for root, dirs, filenames in os.walk(project_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignored]
            
            # Skip CursorFocus directory
            if 'CursorFocus' in root.split(os.sep):
                continue
                
            for filename in filenames:
                if filename.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.css', '.scss')):
                    file_path = os.path.join(root, filename)
                    files.append(file_path)
        return files

    def analyze_code_structure(self, project_path: str, files: List[str]) -> Dict:
        """Analyze code structure and organization"""
        structure_analysis = {
            'technical': [],
            'simple': [],
            'files_by_type': defaultdict(list),
            'potential_unused': []
        }
        
        # Analyze file organization
        for file in files:
            ext = os.path.splitext(file)[1]
            rel_path = os.path.relpath(file, project_path)
            structure_analysis['files_by_type'][ext].append(rel_path)
            
            # Check for potentially unused files
            if os.path.getsize(file) < 50:  # Small files might be unused
                structure_analysis['potential_unused'].append(rel_path)
                
        return structure_analysis

    def analyze_coding_standards(self, file_contents: Dict[str, str]) -> Dict:
        """Analyze coding standards and style"""
        standards_analysis = {
            'technical': [],
            'simple': [],
            'style_issues': defaultdict(list)
        }
        
        for file_path, content in file_contents.items():
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Check indentation
                if line.strip() and line[0] != ' ' and not line.startswith(('import', 'from', 'class', 'def')):
                    standards_analysis['style_issues']['indentation'].append((file_path, i))
                
                # Check line length
                if len(line) > 100:
                    standards_analysis['style_issues']['line_length'].append((file_path, i))
                    
                # Check naming conventions
                if re.search(r'[a-z][A-Z]', line):  # Detect mixed case
                    standards_analysis['style_issues']['naming'].append((file_path, i))
                    
        return standards_analysis

    def find_duplicate_code(self, file_contents: Dict[str, str]) -> Dict:
        """Detect duplicate code blocks"""
        duplicates = {
            'technical': [],
            'simple': [],
            'duplicates': []
        }
        
        # Simple duplicate function detection
        function_patterns = {
            'py': r'def\s+(\w+)',
            'js': r'function\s+(\w+)|const\s+(\w+)\s*=\s*\(',
            'ts': r'function\s+(\w+)|const\s+(\w+)\s*=\s*\('
        }
        
        functions = defaultdict(list)
        for file_path, content in file_contents.items():
            ext = os.path.splitext(file_path)[1][1:]
            pattern = function_patterns.get(ext)
            if pattern:
                matches = re.finditer(pattern, content)
                for match in matches:
                    func_name = match.group(1) or match.group(2)
                    functions[func_name].append(file_path)
                    
        for func_name, files in functions.items():
            if len(files) > 1:
                duplicates['duplicates'].append((func_name, files))
                
        return duplicates

    def check_security_issues(self, file_contents: Dict[str, str]) -> Dict:
        """Check for security issues"""
        security_analysis = {
            'technical': [],
            'simple': [],
            'issues': []
        }
        
        # Check for hardcoded secrets
        secret_patterns = [
            r'api[_-]key\s*=\s*["\']([^"\']+)["\']',
            r'password\s*=\s*["\']([^"\']+)["\']',
            r'secret\s*=\s*["\']([^"\']+)["\']',
            r'token\s*=\s*["\']([^"\']+)["\']'
        ]
        
        for file_path, content in file_contents.items():
            for pattern in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    security_analysis['issues'].append({
                        'file': file_path,
                        'type': 'hardcoded_secret',
                        'pattern': pattern
                    })
                    
        return security_analysis

    def analyze_error_handling(self, file_contents: Dict[str, str]) -> Dict:
        """Analyze error handling practices"""
        error_analysis = {
            'technical': [],
            'simple': [],
            'missing_error_handling': []
        }
        
        for file_path, content in file_contents.items():
            if file_path.endswith(('.py', '.js', '.ts')):
                # Check for functions without try-catch
                function_blocks = re.finditer(r'(async\s+)?(?:function|def)\s+\w+\s*\([^)]*\)\s*{?[^}]*$', content, re.MULTILINE)
                for match in function_blocks:
                    block_content = content[match.start():match.end()]
                    if 'try' not in block_content and 'catch' not in block_content:
                        error_analysis['missing_error_handling'].append(file_path)
                        
        return error_analysis

    def check_documentation(self, file_contents: Dict[str, str]) -> Dict:
        """Check documentation coverage"""
        doc_analysis = {
            'technical': [],
            'simple': [],
            'missing_docs': []
        }
        
        for file_path, content in file_contents.items():
            if file_path.endswith('.py'):
                # Check for missing docstrings
                functions = re.finditer(r'def\s+\w+\s*\([^)]*\):', content)
                for match in functions:
                    pos = match.end()
                    next_lines = content[pos:pos+100]
                    if '"""' not in next_lines and "'''" not in next_lines:
                        doc_analysis['missing_docs'].append(file_path)
                        
        return doc_analysis

    def generate_review_prompt(self, focus_content: str, analysis_results: Dict) -> str:
        """Generate the prompt for AI review with analysis results"""
        prompt = """As an expert code reviewer, analyze the following codebase and provide a comprehensive review. 

Project Overview from Focus.md:
{focus_content}

Analysis Results:
{analysis_results}

Please provide a detailed review in two sections:

1. Technical Review
   - Code structure and organization assessment
   - Coding standards compliance
   - Security vulnerabilities
   - Performance considerations
   - Error handling practices
   - Documentation coverage
   - Duplicate code analysis
   - Dependency management
   - Testing coverage

2. Simple Explanation
   - Overall project organization
   - Code clarity and maintainability
   - Security concerns in plain language
   - Suggestions for improvement
   - Priority action items

For each section, provide specific examples and actionable recommendations.
"""
        return prompt.format(
            focus_content=focus_content,
            analysis_results=str(analysis_results)
        )

    def analyze_file(self, file_path: str, content: str, all_files_content: Dict[str, str]) -> Dict:
        """Analyze a single file and provide simple explanation"""
        # Store the current file path for use in _extract_functions
        self.current_file = file_path
        
        # Get file type
        file_type = os.path.splitext(file_path)[1][1:]
        
        analysis = {
            'explanation': self._generate_simple_explanation(file_path, content),
            'similar_files': [],
            'functionality_alerts': []
        }
        
        # Get line count
        lines = content.splitlines()
        line_count = len(lines)
        if line_count > 200:  # Even lower threshold for length warnings
            analysis['functionality_alerts'].append({
                'type': 'length_warning',
                'details': f'File exceeds recommended length of 200 lines',
                'count': line_count
            })
        
        # Extract and analyze functions
        functions = self._extract_functions(content, file_type)
        
        # Find duplicate functions with line numbers
        if file_type in ['js', 'jsx', 'ts', 'tsx', 'py']:
            function_counts = defaultdict(list)
            
            # First pass: collect all functions
            for other_path, other_content in all_files_content.items():
                if other_path != file_path:
                    other_functions = self._extract_functions(other_content, os.path.splitext(other_path)[1][1:])
                    for func in other_functions:
                        function_counts[func['name']].append(other_path)
            
            # Second pass: check for duplicates
            for func in functions:
                if func['name'] in function_counts:
                    # Find the line number
                    for i, line in enumerate(lines, 1):
                        if func['name'] in line and ('function' in line or 'def' in line or '=>' in line):
                            analysis['functionality_alerts'].append({
                                'type': 'duplicate_functionality',
                                'details': f"Function '{func['name']}' is duplicated",
                                'count': len(function_counts[func['name']]) + 1,
                                'line': i,
                                'locations': function_counts[func['name']]
                            })
                            break
        
        # Find similar file content
        for other_path, other_content in all_files_content.items():
            if other_path != file_path:
                similarity = self._calculate_similarity(
                    self._clean_content(content),
                    self._clean_content(other_content)
                )
                if similarity > 0.7:  # 70% similarity threshold
                    analysis['functionality_alerts'].append({
                        'type': 'similar_content',
                        'details': f"File has {int(similarity * 100)}% similar content with {os.path.basename(other_path)}",
                        'file': other_path
                    })
                else:
                    # Add to related files if there's some similarity
                    if similarity > 0.3:  # 30% similarity threshold for related files
                        analysis['similar_files'].append({
                            'file': other_path
                        })
        
        return analysis

    def _are_names_similar(self, name1: str, name2: str) -> bool:
        """Check if two file names are similar"""
        # Remove extension and common prefixes/suffixes
        name1 = os.path.splitext(name1)[0]
        name2 = os.path.splitext(name2)[0]
        
        # Remove common words
        common_words = ['test', 'utils', 'helper', 'component', 'page', 'api']
        for word in common_words:
            name1 = name1.replace(word, '')
            name2 = name2.replace(word, '')
        
        # Compare the core names
        return name1 and name2 and (name1 in name2 or name2 in name1)

    def _have_similar_content(self, content1: str, content2: str) -> bool:
        """Check if two files have similar content"""
        # Remove comments and whitespace
        content1 = self._clean_content(content1)
        content2 = self._clean_content(content2)
        
        # If either content is empty, return False
        if not content1 or not content2:
            return False
        
        # Calculate similarity ratio
        similarity = SequenceMatcher(None, content1, content2).ratio()
        return similarity > 0.7  # Files are considered similar if they're 70% identical

    def _clean_content(self, content: str) -> str:
        """Remove comments and whitespace from content"""
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
        
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove empty lines and whitespace
        return '\n'.join(line.strip() for line in content.splitlines() if line.strip())

    def _generate_function_description(self, func_name: str, func_body: str, file_type: str) -> str:
        """Generate a simple description of what a function does"""
        
        # Special case components
        special_components = {
            'RootLayout': "The main layout component that wraps all pages",
            'Layout': "Provides the structure and layout for pages",
            'Loading': "Shows a loading state while content is being prepared",
            'NotFound': "Displays a friendly 404 error page when content isn't found",
            'Error': "Shows an error message when something goes wrong",
            'Page': "The main content component for this route",
            'Header': "The top section of the page with navigation and branding",
            'Footer': "The bottom section of the page with additional links and info",
            'Sidebar': "A side panel with navigation or additional content",
            'Navigation': "Helps users move between different parts of the site",
            'Modal': "A popup window that appears over the main content",
            'Dialog': "A popup window for user interactions or messages",
            'Form': "Collects user input through various fields",
            'Button': "A clickable element that triggers actions",
            'Input': "Allows users to enter text or data",
            'Select': "Lets users choose from a list of options",
            'Card': "Displays content in a card-style container",
            'List': "Shows multiple items in a structured way",
            'Table': "Displays data in rows and columns",
            'Menu': "Shows a list of options or actions",
            'Dropdown': "Reveals additional options when clicked",
            'Tabs': "Organizes content into different sections",
            'Alert': "Shows important messages or notifications",
            'Toast': "Displays temporary notification messages",
            'Tooltip': "Shows helpful text when hovering over elements",
            'Badge': "Displays a small count or status indicator",
            'Avatar': "Shows a user's profile picture or icon",
            'Icon': "Displays a small symbolic image",
            'Spinner': "Shows an animated loading indicator",
            'Progress': "Indicates progress of an operation",
            'Skeleton': "Shows a placeholder while content loads"
        }

        # Check for special case components first
        if func_name in special_components:
            return special_components[func_name]

        # Handle Next.js special files
        if hasattr(self, 'current_file'):
            file_name = os.path.basename(self.current_file)
            base_name = os.path.splitext(file_name)[0]
            
            # Map file names to component descriptions
            next_components = {
                'layout': ('RootLayout', "The main layout component that wraps all pages"),
                'page': ('Page', "The main content component for this route"),
                'loading': ('Loading', "Shows a loading state while content is being prepared"),
                'not-found': ('NotFound', "Displays a friendly 404 error page when content isn't found"),
                'error': ('Error', "Shows an error message when something goes wrong"),
                'middleware': ('middleware', "Handles request middleware for authentication and routing")
            }
            
            if base_name in next_components:
                component_name, description = next_components[base_name]
                return description

        # Extract parameters if they exist
        params = re.findall(r'\((.*?)\)', func_body.split('\n')[0])
        param_list = []
        if params:
            # Clean up parameters
            param_text = params[0].strip()
            if param_text and param_text != '()':
                param_list = [p.strip().split(':')[0] for p in param_text.split(',')]

        # Check if it's a React component
        if file_type in ['tsx', 'jsx'] and func_name[0].isupper():
            # Look for common UI patterns in the name
            component_types = {
                'button': "a clickable button",
                'list': "a list of items",
                'form': "a form for user input",
                'modal': "a popup window",
                'dialog': "a popup window",
                'card': "a card-style container",
                'header': "header content",
                'footer': "footer content",
                'nav': "navigation elements",
                'menu': "a menu of options",
                'input': "an input field",
                'select': "a dropdown selection",
                'table': "a data table",
                'grid': "a grid layout",
                'container': "a content container",
                'wrapper': "a wrapper component",
                'provider': "provides data or functionality",
                'view': "a view component",
                'panel': "a panel of content",
                'section': "a section of content"
            }
            
            description = "A component that shows "
            found_type = False
            
            # Check component name against known types
            for type_key, type_desc in component_types.items():
                if type_key in func_name.lower():
                    description += type_desc
                    found_type = True
                    break
            
            if not found_type:
                # Convert PascalCase to spaces for a readable name
                readable_name = ' '.join(re.findall('[A-Z][^A-Z]*', func_name)).lower()
                description += f"{readable_name}"
            
            # Add parameter context if available
            if param_list:
                description += f" (uses: {', '.join(param_list)})"
            return description

        # Common React/Next.js patterns
        react_patterns = {
            r'^use[A-Z]': "A custom hook that ",
            r'^handle[A-Z]': "Handles when ",
            r'^on[A-Z]': "Responds when ",
            r'^get[A-Z]': "Gets or retrieves ",
            r'^set[A-Z]': "Updates or changes ",
            r'^is[A-Z]': "Checks if ",
            r'^has[A-Z]': "Checks if there is ",
            r'^format[A-Z]': "Formats or arranges ",
            r'^validate[A-Z]': "Checks if valid ",
            r'^parse[A-Z]': "Processes and understands ",
            r'^render[A-Z]': "Shows or displays ",
            r'^create[A-Z]': "Creates or makes new ",
            r'^update[A-Z]': "Updates or modifies ",
            r'^delete[A-Z]': "Removes or deletes ",
            r'^fetch[A-Z]': "Gets data from ",
            r'^load[A-Z]': "Loads or prepares ",
            r'^save[A-Z]': "Saves or stores ",
            r'^convert[A-Z]': "Converts or changes ",
            r'^calculate[A-Z]': "Calculates or computes ",
            r'^filter[A-Z]': "Filters or selects ",
            r'^sort[A-Z]': "Arranges or orders ",
            r'^search[A-Z]': "Searches for ",
            r'^find[A-Z]': "Finds or locates ",
            r'^toggle[A-Z]': "Switches between ",
            r'^show[A-Z]': "Displays or reveals ",
            r'^hide[A-Z]': "Hides or removes from view ",
            r'^open[A-Z]': "Opens or shows ",
            r'^close[A-Z]': "Closes or hides ",
            r'^enable[A-Z]': "Turns on or activates ",
            r'^disable[A-Z]': "Turns off or deactivates ",
            r'^add[A-Z]': "Adds or includes ",
            r'^remove[A-Z]': "Removes or takes away ",
            r'^clear[A-Z]': "Clears or resets ",
            r'^reset[A-Z]': "Resets or restores "
        }

        # Check for common function patterns
        for pattern, desc_prefix in react_patterns.items():
            if re.match(pattern, func_name):
                # Convert camelCase to spaces after the prefix
                name_parts = re.sub(r'([A-Z])', r' \1', func_name).split()
                action_part = ' '.join(name_parts[1:]).lower()
                description = desc_prefix + action_part
                
                # Add parameter context if available
                if param_list:
                    description += f" (uses: {', '.join(param_list)})"
                return description

        # If no pattern matched, create a basic description
        # Convert camelCase/PascalCase to spaces
        readable_name = re.sub(r'([A-Z])', r' \1', func_name).lower()
        description = f"Handles {readable_name}"
        
        # Add parameter context if available
        if param_list:
            description += f" (uses: {', '.join(param_list)})"

        return description

    def _extract_functions(self, content: str, file_type: str) -> List[Dict[str, Any]]:
        """Extract functions and their details from the file content"""
        functions = []
        
        # Skip binary or empty files
        if not content or is_binary_file(content):
            return functions
        
        try:
            # Different patterns for different file types
            if file_type in ('ts', 'tsx', 'js', 'jsx'):
                # React component pattern
                component_pattern = r'(?:export\s+(?:default\s+)?)?(?:const|class|function)\s+([A-Z][a-zA-Z0-9]*)\s*(?:=|\{|\()'
                for match in re.finditer(component_pattern, content):
                    functions.append({
                        'name': match.group(1),
                        'type': 'component',
                        'line': content.count('\n', 0, match.start()) + 1
                    })
                
                # Hook pattern
                hook_pattern = r'(?:export\s+(?:default\s+)?)?(?:const|function)\s+(use[A-Z][a-zA-Z0-9]*)\s*(?:=|\()'
                for match in re.finditer(hook_pattern, content):
                    functions.append({
                        'name': match.group(1),
                        'type': 'hook',
                        'line': content.count('\n', 0, match.start()) + 1
                    })
                
                # Regular function pattern
                function_pattern = r'(?:export\s+(?:default\s+)?)?(?:async\s+)?(?:function|const)\s+([a-z][a-zA-Z0-9]*)\s*(?:=|\()'
                for match in re.finditer(function_pattern, content):
                    functions.append({
                        'name': match.group(1),
                        'type': 'function',
                        'line': content.count('\n', 0, match.start()) + 1
                    })
                
            elif file_type == 'py':
                # Python function pattern
                function_pattern = r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
                for match in re.finditer(function_pattern, content):
                    functions.append({
                        'name': match.group(1),
                        'type': 'function',
                        'line': content.count('\n', 0, match.start()) + 1
                    })
                
                # Python class pattern
                class_pattern = r'class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:\([^)]*\))?\s*:'
                for match in re.finditer(class_pattern, content):
                    functions.append({
                        'name': match.group(1),
                        'type': 'class',
                        'line': content.count('\n', 0, match.start()) + 1
                    })
        except Exception as e:
            logging.debug(f"Error extracting functions: {str(e)}")
        
        return functions

    def _extract_function_body(self, content: str, file_type: str) -> str:
        """Extract function body based on file type"""
        if file_type == 'py':
            # Python: Find indented block
            lines = content.splitlines()
            body = []
            if not lines:
                return ""
            
            # Get first line's indentation
            first_line = lines[0]
            base_indent = len(first_line) - len(first_line.lstrip())
            
            for line in lines:
                if line.strip() and len(line) - len(line.lstrip()) <= base_indent:
                    break
                body.append(line)
            
            return '\n'.join(body)
        else:
            # JavaScript/TypeScript: Find block between { }
            stack = []
            for i, char in enumerate(content):
                if char == '{':
                    stack.append(i)
                elif char == '}':
                    if stack:
                        start = stack.pop()
                        if not stack:  # We found the matching outer brace
                            return content[start:i+1]
            return ""

    def _find_duplicate_functions(self, functions1: List[Dict], functions2: List[Dict]) -> List[str]:
        """Find duplicate functions between two sets by comparing implementation and context"""
        duplicates = []
        
        # Common method names to ignore (these are expected to appear multiple times)
        ignore_methods = {
            # React/Next.js patterns
            'getLayout', 'getInitialProps', 'getStaticProps', 'getServerSideProps',
            'layout', 'loading', 'error', 'notFound',
            # Common React hooks
            'useEffect', 'useState', 'useMemo', 'useCallback',
            # Common utility names
            'init', 'setup', 'configure', 'getConfig', 'getData',
            # Common class methods
            '__init__', '__str__', '__repr__', '__len__', 'toString',
            # Testing functions
            'setUp', 'tearDown', 'beforeEach', 'afterEach',
        }

        for func1 in functions1:
            for func2 in functions2:
                # Skip ignored method names
                if func1['name'] in ignore_methods:
                    continue
                
                # Only compare functions with same name
                if func1['name'] == func2['name']:
                    # Clean and normalize the function bodies
                    body1 = self._normalize_function_body(func1['body'])
                    body2 = self._normalize_function_body(func2['body'])
                    
                    # Calculate similarity score
                    similarity = self._calculate_similarity(body1, body2)
                    
                    # If bodies are very similar (80% or more), it's likely a real duplication
                    if similarity >= 0.8:
                        duplicates.append({
                            'name': func1['name'],
                            'similarity': similarity,
                            'reason': 'Implementation is nearly identical'
                        })
                    # If bodies are somewhat similar (60-80%), check the context
                    elif similarity >= 0.6:
                        context_similarity = self._check_function_context(func1, func2)
                        if context_similarity >= 0.7:
                            duplicates.append({
                                'name': func1['name'],
                                'similarity': similarity,
                                'reason': 'Similar implementation and usage context'
                            })
        
        return duplicates

    def _normalize_function_body(self, body: str) -> str:
        """Normalize function body for comparison by removing noise"""
        # Remove comments
        body = re.sub(r'//.*$', '', body, flags=re.MULTILINE)
        body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
        body = re.sub(r'#.*$', '', body, flags=re.MULTILINE)
        
        # Remove string literals
        body = re.sub(r'"[^"]*"', '""', body)
        body = re.sub(r"'[^']*'", "''", body)
        
        # Remove whitespace and normalize line endings
        body = '\n'.join(line.strip() for line in body.splitlines() if line.strip())
        
        # Remove variable names but keep structure
        body = re.sub(r'\b\w+\s*=', '=', body)
        body = re.sub(r'\bconst\s+\w+\s*=', 'const=', body)
        body = re.sub(r'\blet\s+\w+\s*=', 'let=', body)
        body = re.sub(r'\bvar\s+\w+\s*=', 'var=', body)
        
        return body

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity ratio between two texts"""
        if not text1 or not text2:
            return 0.0
        return SequenceMatcher(None, text1, text2).ratio()

    def _check_function_context(self, func1: Dict, func2: Dict) -> float:
        """Check if functions are used in similar contexts"""
        # Extract function calls and dependencies
        calls1 = set(re.findall(r'\b\w+\(', func1['body']))
        calls2 = set(re.findall(r'\b\w+\(', func2['body']))
        
        # Extract variable usage patterns
        vars1 = set(re.findall(r'\b\w+\s*=|\b\w+\s*\+=|\b\w+\s*-=', func1['body']))
        vars2 = set(re.findall(r'\b\w+\s*=|\b\w+\s*\+=|\b\w+\s*-=', func2['body']))
        
        # Calculate similarity of usage patterns
        calls_similarity = len(calls1.intersection(calls2)) / max(len(calls1), len(calls2), 1)
        vars_similarity = len(vars1.intersection(vars2)) / max(len(vars1), len(vars2), 1)
        
        return (calls_similarity + vars_similarity) / 2

    def _generate_simple_explanation(self, file_path: str, content: str) -> str:
        """Generate an intelligent, context-aware explanation of what the file does"""
        
        # Get file extension and name
        ext = os.path.splitext(file_path)[1][1:].lower()
        name = os.path.basename(file_path)
        
        # Extract key information
        functions = self._extract_functions(content, ext) or []
        imports = self._extract_imports(content)
        exports = self._extract_exports(content)
        
        # Initialize description components
        purpose = []
        features = []
        integrations = []
        
        # Analyze file type and location
        if '/api/' in file_path:
            endpoint = file_path.split('/api/')[-1].split('/')[0]
            purpose.append(f"This API endpoint handles {endpoint} functionality")
            if 'route' in name.lower():
                features.append("implements routing logic")
        
        elif '/components/' in file_path:
            component_names = [f['name'] for f in functions if f['name'][0].isupper()]
            if component_names:
                purpose.append(f"This React component implements {', '.join(component_names)}")
                if any(f['name'].startswith('use') for f in functions):
                    features.append("includes custom hooks")
        
        elif '/services/' in file_path or 'service' in name.lower():
            service_type = next((word for word in file_path.split('/') if 'service' in word.lower()), 'service')
            purpose.append(f"This service module provides {service_type.replace('Service', '').replace('service', '')} functionality")
        
        elif '/utils/' in file_path or 'util' in name.lower() or 'helper' in name.lower():
            purpose.append("This utility module provides helper functions")
            if functions:
                features.append(f"includes {len(functions)} utility functions")
        
        elif '/hooks/' in file_path or any(f['name'].startswith('use') for f in functions):
            hook_names = [f['name'] for f in functions if f['name'].startswith('use')]
            if hook_names:
                purpose.append(f"This custom hook module implements {', '.join(hook_names)}")
        
        elif '/types/' in file_path or file_path.endswith('.d.ts'):
            purpose.append("This type definition file declares interfaces and types")
            if exports:
                features.append(f"defines {len(exports)} types/interfaces")
        
        elif '/tests/' in file_path or 'test' in name.lower() or 'spec' in name.lower():
            purpose.append("This test file verifies functionality")
            if functions:
                features.append(f"contains {len(functions)} test cases")
        
        elif file_path.endswith(('.css', '.scss', '.less')):
            purpose.append("This style file defines visual appearance and layout")
        
        elif 'config' in name.lower() or file_path.endswith(('.json', '.env')):
            purpose.append("This configuration file manages project settings")
        
        else:
            # Default case - analyze based on content
            if functions:
                main_functions = [f['name'] for f in functions[:3]]
                purpose.append("This module implements application logic")
                features.append(f"key functions: {', '.join(main_functions)}")
        
        # Add integration details
        if imports:
            major_deps = [dep for dep in imports.keys() if not dep.startswith('.')][:2]
            if major_deps:
                integrations.append(f"integrates with {' and '.join(major_deps)}")
        
        # Combine all parts
        description = []
        if purpose:
            description.extend(purpose)
        if features:
            description.append(f"It {', '.join(features)}")
        if integrations:
            description.extend(integrations)
        
        return '. '.join(description) + '.'

    def _extract_imports(self, content: str) -> Dict[str, set]:
        """Extract imports from file content"""
        imports = {}
        
        # Match ES6/TypeScript imports
        es6_pattern = r'import\s+(?:{[^}]+}|\*\s+as\s+\w+|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(es6_pattern, content):
            module = match.group(1)
            imports[module] = set()
        
        # Match Python imports
        python_pattern = r'(?:from\s+([^\s]+)\s+import|import\s+([^\s]+))'
        for match in re.finditer(python_pattern, content):
            module = match.group(1) or match.group(2)
            imports[module] = set()
        
        return imports

    def _extract_exports(self, content: str) -> List[str]:
        """Extract exports from file content"""
        exports = []
        
        # Match ES6/TypeScript exports
        es6_patterns = [
            r'export\s+(?:default\s+)?(?:class|interface|type|const|let|var|function)\s+(\w+)',
            r'export\s+{\s*([^}]+)\s*}'
        ]
        
        for pattern in es6_patterns:
            for match in re.finditer(pattern, content):
                if ',' in match.group(1):
                    exports.extend(name.strip() for name in match.group(1).split(','))
                else:
                    exports.append(match.group(1).strip())
        
        # Match Python exports
        python_pattern = r'__all__\s*=\s*\[([^\]]+)\]'
        for match in re.finditer(python_pattern, content):
            exports.extend(name.strip().strip("'\"") for name in match.group(1).split(','))
        
        return exports

    def _analyze_functionality(self, file_path: str, content: str, all_files_content: Dict[str, str]) -> List[Dict]:
        """Analyze functionality duplication and import/export mismatches"""
        alerts = []
        
        # Extract imports and exports from current file
        current_imports = self._extract_imports(content)
        current_exports = self._extract_exports(content)
        
        # Look for functionality duplication
        for other_path, other_content in all_files_content.items():
            if other_path == file_path:
                continue
                
            other_imports = self._extract_imports(other_content)
            other_exports = self._extract_exports(other_content)
            
            # Get relative paths for comparison
            rel_path = os.path.relpath(file_path)
            other_rel_path = os.path.relpath(other_path)
            
            # Extract and compare functions
            current_functions = self._extract_functions(content, os.path.splitext(file_path)[1][1:])
            other_functions = self._extract_functions(other_content, os.path.splitext(other_path)[1][1:])
            
            duplicates = self._find_duplicate_functions(current_functions, other_functions)
            if duplicates:
                details = []
                for dup in duplicates:
                    details.append(f"{dup['name']} ({int(dup['similarity']*100)}% similar - {dup['reason']})")
                
                alerts.append({
                    'type': 'duplicate_functionality',
                    'file': other_path,
                    'details': f"These functions have similar implementations: {', '.join(details)}"
                })
            
            # Check for circular dependencies
            if any(p in other_imports for p in [rel_path, os.path.splitext(rel_path)[0]]) and \
               any(p in current_imports for p in [other_rel_path, os.path.splitext(other_rel_path)[0]]):
                alerts.append({
                    'type': 'circular_dependency',
                    'file': other_path,
                    'details': "These files import each other, which could cause problems"
                })
            
            # Check for mismatched imports
            for source, items in current_imports.items():
                if source in [other_rel_path, os.path.splitext(other_rel_path)[0]]:
                    missing_exports = items - other_exports - {'*'}
                    if missing_exports:
                        alerts.append({
                            'type': 'import_mismatch',
                            'file': other_path,
                            'details': f"Trying to import {', '.join(sorted(missing_exports))} but they're not exported from the file"
                        })
        
        return alerts

    def generate_review(self, project_path: str) -> str:
        """Generate a file-by-file code review"""
        try:
            files = self.get_relevant_files(project_path)
            if not files:
                return "No relevant files found for analysis."
                
            # Filter out any CursorFocus files
            cursorfocus_path = os.path.join(project_path, 'CursorFocus')
            files = [f for f in files if not f.startswith(cursorfocus_path)]
            
            file_contents = {f: self.read_file_content(f) for f in files}
            file_analyses = {}
            for file_path, content in file_contents.items():
                file_analyses[file_path] = self.analyze_file(file_path, content, file_contents)
            
            # Format the review
            formatted_review = "# Code Review Report\n\n"
            
            # Group files by directory
            by_directory = defaultdict(list)
            for file_path in files:
                dir_path = os.path.dirname(file_path)
                by_directory[dir_path].append(file_path)
            
            # Generate review for each directory
            for dir_path, dir_files in sorted(by_directory.items()):
                rel_dir = os.path.relpath(dir_path, project_path)
                formatted_review += f"\n## 📁 {rel_dir}\n"
                formatted_review += f"{self._get_directory_purpose(rel_dir)}\n\n"
                
                for file_path in sorted(dir_files):
                    rel_path = os.path.relpath(file_path, project_path)
                    analysis = file_analyses[file_path]
                    content = file_contents[file_path]
                    line_count = len(content.splitlines())
                    
                    # Add empty line before each file entry
                    formatted_review += "\n"
                    
                    # File header with line count
                    formatted_review += f"`/{rel_path}` ({line_count} lines)\n"
                    
                    # Description
                    formatted_review += "**What this file does:**\n"
                    formatted_review += f"{analysis['explanation']}\n"
                    
                    # Alerts
                    if analysis['functionality_alerts']:
                        formatted_review += "**⚠️ Alerts:**\n"
                        for alert in analysis['functionality_alerts']:
                            if alert['type'] == 'length_warning':
                                formatted_review += f"- 📏 {alert['details']} (Current: {alert['count']} lines)\n"
                            elif alert['type'] == 'duplicate_functionality':
                                locations = ', '.join(f'`{os.path.relpath(loc, project_path)}`' for loc in alert.get('locations', []))
                                formatted_review += f"- 🔄 {alert['details']} (Found in: {locations})\n"
                            elif alert['type'] == 'similar_content':
                                formatted_review += f"- 👯 {alert['details']}\n"
                    
                    # Key Functions
                    functions = self._extract_functions(content, os.path.splitext(file_path)[1][1:])
                    if functions:
                        formatted_review += "**Key Functions:**\n"
                        for func in functions:
                            description = self._generate_function_description(func['name'], '', os.path.splitext(file_path)[1][1:])
                            formatted_review += f"<{func['name']}>: {description}\n"
                    
                    # Related files
                    if analysis['similar_files']:
                        formatted_review += "**Related files:**\n"
                        for similar in analysis['similar_files']:
                            formatted_review += f"- Works with `{os.path.relpath(similar['file'], project_path)}`\n"
                    
                    formatted_review += "---\n\n\n"  # Added an extra newline here
            
            formatted_review += f"\n## Review Date\n{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            return formatted_review
                
        except Exception as e:
            logging.error(f"Error in review generation: {str(e)}", exc_info=True)
            return f"Error generating review: {str(e)}"

    def _get_directory_purpose(self, dir_path: str) -> str:
        """Get a simple explanation of what a directory is for"""
        # Generic directory purposes
        common_dirs = {
            '.': "Project root directory",
            'src': "Source code directory",
            'components': "Reusable components",
            'utils': "Utility functions",
            'styles': "Style definitions",
            'api': "API-related code",
            'public': "Public assets",
            'types': "Type definitions",
            'tests': "Test files",
            'docs': "Documentation",
            'config': "Configuration files",
            'lib': "Library code",
            'assets': "Static assets",
            'scripts': "Build and utility scripts"
        }

        # Handle nested paths
        parts = dir_path.split(os.sep)
        if len(parts) > 1:
            if parts[0] in common_dirs:
                base_purpose = common_dirs[parts[0]]
                sub_path = '/'.join(parts[1:])
                return f"{base_purpose} - {sub_path}"

        return common_dirs.get(dir_path, f"Directory: {dir_path}")

def is_binary_file(content: str) -> bool:
    """Check if file content appears to be binary"""
    try:
        content.encode('utf-8')
        return False
    except UnicodeError:
        return True

def main():
    """Main function to generate code review."""
    logging.basicConfig(level=logging.INFO)
    
    # Load environment variables
    from dotenv import load_dotenv
    cursorfocus_env = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(cursorfocus_env)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logging.error("GEMINI_API_KEY not found in environment variables")
        return
    
    # Use parent directory as project path
    project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Generate review
    reviewer = CodeReviewGenerator(api_key)
    review_content = reviewer.generate_review(project_path)
    
    # Save review in project root
    output_file = os.path.join(project_path, 'CodeReview.md')
    try:
        with open(output_file, 'w') as f:
            f.write(review_content)
        print(f"Code review saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving review: {str(e)}")

if __name__ == '__main__':
    main() 