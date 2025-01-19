import os
import re
from config import (
    BINARY_EXTENSIONS,
    IGNORED_NAMES,
    NON_CODE_EXTENSIONS,
    CODE_EXTENSIONS,
    FUNCTION_PATTERNS,
    IGNORED_KEYWORDS
)
import logging
from datetime import datetime
import json

def get_combined_pattern():
    """Combine all function patterns into a single regex pattern."""
    return '|'.join(f'(?:{pattern})' for pattern in FUNCTION_PATTERNS.values())

def is_binary_file(filename):
    """Check if a file is binary or non-code based on its extension and content."""
    ext = os.path.splitext(filename)[1].lower()
    
    # Binary extensions
    binary_extensions = BINARY_EXTENSIONS.union({
        '.gz', '.zip', '.tar', '.rar', '.7z',  # Compressed files
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',  # Images
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',  # Documents
        '.bin', '.exe', '.dll', '.so', '.dylib',  # Executables and libraries
        '.pack',  # Git pack files
        '.map'   # Source map files
    })
    
    # Check for Next.js build files
    if ('/.next/' in filename or '/out/' in filename) and ext in {'.js', '.mjs', '.cjs'}:
        return True
        
    if ext in binary_extensions:
        return True
        
    # Try to read first few bytes to detect binary content
    try:
        with open(filename, 'rb') as f:
            chunk = f.read(1024)
            if b'\x00' in chunk:  # Null bytes indicate binary
                return True
            try:
                chunk.decode('utf-8')
                return False
            except UnicodeDecodeError:
                return True
    except (IOError, OSError):
        # If we can't read the file, treat it as binary to be safe
        return True
        
    # Documentation and text files that shouldn't be analyzed for functions
    return ext in NON_CODE_EXTENSIONS

def should_ignore_file(name):
    """Check if a file or directory should be ignored."""
    return name in IGNORED_NAMES or name.startswith('.')

def find_duplicate_functions(content, filename):
    """Find duplicate functions in a file and their line numbers."""
    duplicates = {}
    function_lines = {}
    
    # Combined pattern for all function types
    combined_pattern = get_combined_pattern()
    
    # Find all function declarations
    for i, line in enumerate(content.split('\n'), 1):
        matches = re.finditer(combined_pattern, line)
        for match in matches:
            # Get the first non-None group (the function name)
            func_name = next(filter(None, match.groups()), None)
            if func_name and func_name.lower() not in IGNORED_KEYWORDS:
                if func_name not in function_lines:
                    function_lines[func_name] = []
                function_lines[func_name].append(i)
    
    # Identify duplicates with simplified line reporting
    for func_name, lines in function_lines.items():
        if len(lines) > 1:
            # Only store first occurrence and count
            duplicates[func_name] = (lines[0], len(lines))
    
    return duplicates

def parse_comments(content_lines, start_index=0):
    """Parse both multi-line and single-line comments from a list of content lines.
    
    Args:
        content_lines: List of content lines to parse
        start_index: Starting index to parse from (default: 0)
        
    Returns:
        list: List of cleaned comment lines
    """
    description = []
    in_comment_block = False
    
    for line in reversed(content_lines[max(0, start_index):]):
        line = line.strip()
        
        # Handle JSDoc style comments
        if line.startswith('/**'):
            in_comment_block = True
            continue
        elif line.startswith('*/'):
            continue
        elif in_comment_block and line.startswith('*'):
            cleaned_line = line.lstrip('* ').strip()
            if cleaned_line and not cleaned_line.startswith('@'):
                description.insert(0, cleaned_line)
        # Handle single line comments
        elif line.startswith('//'):
            cleaned_line = line.lstrip('/ ').strip()
            if cleaned_line:
                description.insert(0, cleaned_line)
        # Stop if we hit code
        elif line and not line.startswith('/*') and not in_comment_block:
            break
    
    return description

def extract_function_context(content, start_pos, end_pos=None):
    """Extract and analyze the function's content to generate a meaningful description.
    
    Args:
        content: Full file content
        start_pos: Starting position of the function
        end_pos: Optional ending position of the function
        
    Returns:
        str: A user-friendly description of the function
    """
    # Get more context before and after the function
    context_before = content[max(0, start_pos-1000):start_pos].strip()
    
    # Get the next 1000 characters after function declaration to analyze
    context_length = 1000 if end_pos is None else end_pos - start_pos
    context = content[start_pos:start_pos + context_length]
    
    # Try to find function body between first { and matching }
    body_start = context.find('{')
    if body_start != -1:
        bracket_count = 1
        body_end = body_start + 1
        while bracket_count > 0 and body_end < len(context):
            if context[body_end] == '{':
                bracket_count += 1
            elif context[body_end] == '}':
                bracket_count -= 1
            body_end += 1
        function_body = context[body_start:body_end].strip('{}')
    else:
        # For arrow functions or other formats
        function_body = context.split('\n')[0]
    
    # Extract parameters with their types/descriptions
    params_match = re.search(r'\((.*?)\)', context)
    parameters = []
    param_descriptions = {}
    if params_match:
        params = params_match.group(1).split(',')
        for param in params:
            param = param.strip()
            if param:
                # Look for JSDoc param descriptions in context before
                param_name = param.split(':')[0].strip().split('=')[0].strip()
                param_desc_match = re.search(rf'@param\s+{{\w+}}\s+{param_name}\s+-?\s*([^\n]+)', context_before)
                if param_desc_match:
                    param_descriptions[param_name] = param_desc_match.group(1).strip()
                # Make parameter names readable
                readable_param = re.sub(r'([A-Z])', r' \1', param_name).lower()
                readable_param = readable_param.replace('_', ' ')
                parameters.append(readable_param)
    
    # Look for return value and its description
    return_matches = re.findall(r'return\s+([^;]+)', function_body)
    return_info = []
    return_desc_match = re.search(r'@returns?\s+{[^}]+}\s+([^\n]+)', context_before)
    if return_desc_match:
        return_info.append(return_desc_match.group(1).strip())
    elif return_matches:
        for ret in return_matches:
            ret = ret.strip()
            if ret and not ret.startswith('{') and len(ret) < 50:
                return_info.append(ret)
    
    # Look for constants or enums being used
    const_matches = re.findall(r'(?:const|enum)\s+(\w+)\s*=\s*{([^}]+)}', context_before)
    constants = {}
    for const_name, const_values in const_matches:
        values = re.findall(r'(\w+):\s*([^,]+)', const_values)
        if values:
            constants[const_name] = values
    
    # Analyze the actual purpose of the function
    purpose = []
    
    # Check for validation logic
    if re.search(r'(valid|invalid|check|verify|test)\w*', function_body, re.I):
        conditions = []
        # Look for specific conditions being checked
        condition_matches = re.findall(r'if\s*\((.*?)\)', function_body)
        for cond in condition_matches[:2]:  # Get first two conditions
            cond = cond.strip()
            if len(cond) < 50 and '&&' not in cond and '||' not in cond:
                conditions.append(cond.replace('!', 'not '))
        if conditions:
            purpose.append(f"validates {' and '.join(conditions)}")
        else:
            purpose.append("validates input")
    
    # Check for scoring/calculation logic with tiers
    if re.search(r'TIER_\d+|score|calculate|compute', function_body, re.I):
        # Look for tier assignments
        tier_matches = re.findall(r'return\s+(\w+)\.TIER_(\d+)', function_body)
        if tier_matches:
            tiers = [f"Tier {tier}" for _, tier in tier_matches]
            if constants and 'TIER_SCORES' in constants:
                tier_info = []
                for tier_name, tier_score in constants['TIER_SCORES']:
                    if any(t in tier_name for t in tiers):
                        tier_info.append(f"{tier_name.lower()}: {tier_score}")
                if tier_info:
                    purpose.append(f"assigns scores ({', '.join(tier_info)})")
            else:
                purpose.append(f"assigns {' or '.join(tiers)} scores")
        else:
            # Look for other score calculations
            calc_matches = re.findall(r'(\w+(?:Score|Rating|Value))\s*[+\-*/]=\s*([^;]+)', function_body)
            if calc_matches:
                calc_vars = [match[0] for match in calc_matches if len(match[0]) < 30]
                if calc_vars:
                    purpose.append(f"calculates {' and '.join(calc_vars)}")
    
    # Check for store validation
    if re.search(r'store|domain|source', function_body, re.I):
        store_checks = []
        # Look for store list checks
        if 'STORE_CATEGORIES' in constants:
            store_types = [store[0] for store in constants['STORE_CATEGORIES']]
            if store_types:
                store_checks.append(f"checks against {', '.join(store_types)}")
        # Look for domain validation
        domain_checks = re.findall(r'\.(includes|match(?:es)?)\(([^)]+)\)', function_body)
        if domain_checks:
            store_checks.append("validates domain format")
        if store_checks:
            purpose.append(" and ".join(store_checks))
    
    # Check for data transformation
    if re.search(r'(map|filter|reduce|transform|convert|parse|format|normalize)', function_body, re.I):
        transform_matches = re.findall(r'(\w+)\s*\.\s*(map|filter|reduce)', function_body)
        if transform_matches:
            items = [match[0] for match in transform_matches if len(match[0]) < 20]
            if items:
                purpose.append(f"processes {' and '.join(items)}")
    
    # Look for specific number ranges and their context
    range_matches = re.findall(r'([<>]=?)\s*(\d+)', function_body)
    ranges = []
    for op, num in range_matches:
        # Look for variable name or context before comparison
        context_match = re.search(rf'\b(\w+)\s*{op}\s*{num}', function_body)
        if context_match:
            var_name = context_match.group(1)
            var_name = re.sub(r'([A-Z])', r' \1', var_name).lower()
            ranges.append(f"{var_name} {op} {num}")
    
    # Generate a user-friendly description
    description_parts = []
    
    # Add main purpose if found
    if purpose:
        description_parts.append(f"This function {' and '.join(purpose)}")
    
    # Add parameter descriptions if available
    if param_descriptions:
        desc = []
        for param, description in param_descriptions.items():
            if len(description) < 50:  # Keep only concise descriptions
                desc.append(f"{param}: {description}")
        if desc:
            description_parts.append(f"Takes {', '.join(desc)}")
    elif parameters:
        description_parts.append(f"Takes {' and '.join(parameters)}")
    
    # Add range information if found
    if ranges:
        description_parts.append(f"Ensures {' and '.join(ranges)}")
    
    # Add return description if available
    if return_info:
        description_parts.append(f"Returns {return_info[0]}")
    
    # If we couldn't generate a good description, return a simple one
    if not description_parts:
        return "This function helps with the program's functionality"
    
    return " | ".join(description_parts)

def analyze_file_content(file_path):
    """Analyze the content of a file for functions and other relevant information."""
    try:
        if is_binary_file(file_path):
            logging.debug(f"Skipping binary file: {file_path}")
            return None
            
        # Skip files larger than 10MB to prevent memory issues
        if os.path.getsize(file_path) > 10 * 1024 * 1024:
            logging.warning(f"Skipping large file (>10MB): {file_path}")
            return None
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                logging.error(f"Failed to read file {file_path} with both UTF-8 and Latin-1 encodings: {str(e)}")
                return None
                
        # Skip empty files
        if not content.strip():
            return None
            
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Skip files we can't analyze
        if ext not in CODE_EXTENSIONS:
            logging.debug(f"Skipping non-code file: {file_path}")
            return None
            
        # Find duplicate functions
        duplicates = {}
        functions = []
        
        # Get combined pattern
        try:
            combined_pattern = get_combined_pattern()
            
            # Try to find all functions
            for pattern_name, pattern in FUNCTION_PATTERNS.items():
                try:
                    for match in re.finditer(pattern, content, re.MULTILINE):
                        try:
                            # Get function name and position
                            func_name = next(filter(None, match.groups()), None)
                            if not func_name or func_name.lower() in IGNORED_KEYWORDS:
                                continue
                                
                            start_pos = match.start()
                            line_num = content.count('\n', 0, start_pos) + 1
                            
                            # Get function context
                            try:
                                context = extract_function_context(content, start_pos)
                                if context:
                                    functions.append({
                                        'name': func_name,
                                        'line': line_num,
                                        'context': context,
                                        'type': pattern_name
                                    })
                            except Exception as e:
                                logging.debug(f"Error extracting context for function {func_name} in {file_path}: {str(e)}")
                                
                        except Exception as e:
                            logging.debug(f"Error processing match in {file_path}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logging.debug(f"Error with pattern {pattern_name} in {file_path}: {str(e)}")
                    continue
                    
        except Exception as e:
            logging.debug(f"Error getting combined pattern for {file_path}: {str(e)}")
            
        # Check for duplicates
        seen_functions = {}
        for func in functions:
            name = func['name']
            if name in seen_functions:
                if name not in duplicates:
                    duplicates[name] = (seen_functions[name], 2)
                else:
                    _, count = duplicates[name]
                    duplicates[name] = (seen_functions[name], count + 1)
            else:
                seen_functions[name] = func['line']
                
        return {
            'functions': functions,
            'duplicates': duplicates,
            'size': len(content.splitlines())
        }
        
    except Exception as e:
        logging.error(f"Error analyzing file {file_path}: {str(e)}")
        return None

class RulesAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path

    def analyze_project_for_rules(self):
        """Analyze project for .cursorrules generation"""
        try:
            project_info = {
                "name": self.detect_project_name(),
                "version": self.detect_version(),
                "language": self.detect_main_language(),
                "framework": self.detect_framework(),
                "type": self.determine_project_type()
            }
            return project_info
        except Exception as e:
            logging.error(f"Error analyzing project for rules: {e}")
            return self.get_default_project_info() 

class CodeReviewAnalyzer:
    """Handles comprehensive code review analysis with both technical and simplified outputs."""
    
    def __init__(self, project_path):
        self.project_path = project_path
        self.issues = {
            'duplicates': [],
            'unused': [],
            'inconsistent': [],
            'outdated': [],
            'structure': []
        }
        self.metrics = {
            'total_files': 0,
            'total_functions': 0,
            'complexity_scores': {},
            'dependency_issues': []
        }
        
    def analyze_project(self):
        """Analyze the project and return a structured review."""
        try:
            technical_analysis = self._perform_technical_analysis()
            simplified_analysis = self._generate_simplified_analysis(technical_analysis)
            
            return {
                'technical': technical_analysis,
                'simplified': simplified_analysis
            }
        except Exception as e:
            logging.error(f"Error during code review analysis: {str(e)}")
            return None
            
    def _perform_technical_analysis(self):
        """Perform technical analysis of the project."""
        return {
            'project_name': os.path.basename(self.project_path),
            'metrics': self._analyze_metrics(),
            'dependencies': self._analyze_dependencies(),
            'issues': self._analyze_issues()
        }
        
    def _analyze_metrics(self):
        """Analyze project metrics."""
        total_files = 0
        total_lines = 0
        file_types = {}
        
        for root, _, files in os.walk(self.project_path):
            if any(ignored in root for ignored in ['node_modules', '__pycache__', '.git']):
                continue
                
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = len(f.readlines())
                            total_files += 1
                            total_lines += lines
                            ext = os.path.splitext(file)[1]
                            file_types[ext] = file_types.get(ext, 0) + 1
                    except Exception:
                        continue
                        
        return {
            'total_files': total_files,
            'total_lines': total_lines,
            'file_types': file_types
        }
        
    def _analyze_dependencies(self):
        """Analyze project dependencies."""
        dependencies = {
            'direct': [],
            'dev': []
        }
        
        # Check package.json for Node.js projects
        package_json = os.path.join(self.project_path, 'package.json')
        if os.path.exists(package_json):
            try:
                with open(package_json, 'r') as f:
                    data = json.load(f)
                    dependencies['direct'].extend(data.get('dependencies', {}).keys())
                    dependencies['dev'].extend(data.get('devDependencies', {}).keys())
            except Exception:
                pass
                
        # Check requirements.txt for Python projects
        requirements_txt = os.path.join(self.project_path, 'requirements.txt')
        if os.path.exists(requirements_txt):
            try:
                with open(requirements_txt, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            dependencies['direct'].append(line.split('==')[0])
            except Exception:
                pass
                
        return dependencies
        
    def _analyze_issues(self):
        """Analyze code for potential issues."""
        issues = {
            'security': [],
            'performance': [],
            'maintainability': [],
            'style': []
        }
        
        for root, _, files in os.walk(self.project_path):
            if any(ignored in root for ignored in ['node_modules', '__pycache__', '.git']):
                continue
                
            for file in files:
                if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Check for security issues
                            if 'eval(' in content or 'exec(' in content:
                                issues['security'].append({
                                    'file': os.path.relpath(file_path, self.project_path),
                                    'detail': 'Use of eval() or exec() detected',
                                    'severity': 'high'
                                })
                                
                            # Check for performance issues
                            if 'while True:' in content:
                                issues['performance'].append({
                                    'file': os.path.relpath(file_path, self.project_path),
                                    'detail': 'Infinite loop detected',
                                    'severity': 'medium'
                                })
                                
                            # Check for maintainability issues
                            if len(content.splitlines()) > 300:
                                issues['maintainability'].append({
                                    'file': os.path.relpath(file_path, self.project_path),
                                    'detail': 'File exceeds recommended length',
                                    'severity': 'medium'
                                })
                                
                            # Check for style issues
                            if '  ' in content:  # Check for multiple spaces
                                issues['style'].append({
                                    'file': os.path.relpath(file_path, self.project_path),
                                    'detail': 'Inconsistent indentation',
                                    'severity': 'low'
                                })
                    except Exception:
                        continue
                        
        return issues
        
    def _generate_simplified_analysis(self, technical):
        """Generate a simplified analysis from technical results."""
        metrics = technical.get('metrics', {})
        issues = technical.get('issues', {})
        
        # Count total issues by severity
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        for category in issues.values():
            for issue in category:
                severity_counts[issue['severity']] += 1
                
        # Generate summary
        summary = f"Project contains {metrics.get('total_files', 0)} files with {metrics.get('total_lines', 0)} lines of code. "
        if sum(severity_counts.values()) > 0:
            summary += f"Found {sum(severity_counts.values())} potential issues "
            summary += f"({severity_counts['high']} high, {severity_counts['medium']} medium, {severity_counts['low']} low priority)."
        else:
            summary += "No significant issues found."
            
        # Generate file summaries
        file_summaries = []
        for category, category_issues in issues.items():
            for issue in category_issues:
                file_summaries.append({
                    'file': issue['file'],
                    'message': f"{issue['detail']} ({issue['severity']} priority)"
                })
                
        # Generate next steps
        next_steps = []
        if severity_counts['high'] > 0:
            next_steps.append("Address high-priority security concerns")
        if severity_counts['medium'] > 0:
            next_steps.append("Review and refactor complex code sections")
        if severity_counts['low'] > 0:
            next_steps.append("Clean up code style and formatting")
        if not next_steps:
            next_steps.append("Continue maintaining current code quality standards")
            
        return {
            'summary': summary,
            'file_summaries': file_summaries,
            'next_steps': next_steps
        } 