import os
import re
import math
from typing import Dict, List, Tuple
from collections import defaultdict
import logging
from .base_analyzer import BaseAnalyzer

class CodeQualityAnalyzer(BaseAnalyzer):
    def __init__(self, project_path: str):
        super().__init__(project_path)
        self.thresholds = {
            'function_length': 30,
            'file_length': 300,
            'max_params': 4,
            'min_comment_ratio': 0.1,
            'max_complexity': {
                'low': 10,
                'medium': 20,
                'high': 30
            }
        }
        
    def analyze(self) -> Dict:
        """Analyze code quality metrics."""
        return self.safe_execute(
            lambda: {
                'complexity': self._analyze_complexity(),
                'maintainability': self._analyze_maintainability(),
                'code_smells': self._detect_code_smells(),
                'best_practices': self._check_best_practices()
            },
            "Error analyzing code quality",
            self._get_empty_analysis()
        )
        
    def _analyze_complexity(self) -> Dict:
        """Analyze code complexity."""
        complexity = {
            'cyclomatic': defaultdict(int),
            'cognitive': defaultdict(int),
            'files_by_complexity': [],
            'total_score': 0,
            'complexity_distribution': {
                'low': 0,      # 1-10
                'medium': 0,   # 11-20  
                'high': 0,     # 21-30
                'very_high': 0 # >30
            }
        }
        
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Calculate cyclomatic complexity
                    cyclo_score = self._calculate_cyclomatic_complexity(content)
                    
                    # Calculate cognitive complexity
                    cognitive_score = self._calculate_cognitive_complexity(content)
                    
                    rel_path = os.path.relpath(file_path, self.project_path)
                    complexity['files_by_complexity'].append({
                        'file': rel_path,
                        'cyclomatic': cyclo_score,
                        'cognitive': cognitive_score,
                        'total': cyclo_score + cognitive_score
                    })
                    
                    complexity['total_score'] += cyclo_score + cognitive_score
                    
                    # Calculate complexity distribution
                    total = cyclo_score + cognitive_score
                    if total <= 10:
                        complexity['complexity_distribution']['low'] += 1
                    elif total <= 20:
                        complexity['complexity_distribution']['medium'] += 1  
                    elif total <= 30:
                        complexity['complexity_distribution']['high'] += 1
                    else:
                        complexity['complexity_distribution']['very_high'] += 1
                        
        # Sort files by complexity
        complexity['files_by_complexity'].sort(
            key=lambda x: x['total'], 
            reverse=True
        )
        
        return complexity
        
    def _analyze_maintainability(self) -> Dict:
        """Analyze code maintainability."""
        maintainability = {
            'scores': defaultdict(float),
            'issues': defaultdict(list),
            'suggestions': [],
            'metrics': {
                'avg_function_length': 0,
                'max_function_length': 0,
                'functions_over_30_lines': 0,
                'files_over_300_lines': 0,
                'comment_ratio': 0,
                'total_lines': 0,
                'code_to_comment_ratio': 0,
                'avg_params_per_function': 0,
                'maintainability_index': 0
            }
        }
        
        total_functions = 0
        total_function_lines = 0
        
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    rel_path = os.path.relpath(file_path, self.project_path)
                    maintainability['metrics']['total_lines'] += len(lines)
                    
                    # Calculate comment ratio
                    comment_lines = len([l for l in lines if l.strip().startswith(('#', '//', '/*', '*'))])
                    comment_ratio = comment_lines / len(lines) if len(lines) > 0 else 0
                    maintainability['metrics']['comment_ratio'] += comment_ratio
                    
                    # Calculate maintainability index
                    halstead_metrics = self._calculate_halstead_metrics(content)
                    cyclomatic = self._calculate_cyclomatic_complexity(content)
                    
                    mi = self._calculate_maintainability_index(
                        halstead_metrics['volume'],
                        cyclomatic,
                        len(lines),
                        comment_ratio
                    )
                    
                    maintainability['scores'][rel_path] = mi
                    maintainability['metrics']['maintainability_index'] += mi

        # Normalize maintainability index and comment ratio
        if len(maintainability['scores']) > 0:
            maintainability['metrics']['maintainability_index'] /= len(maintainability['scores'])
            maintainability['metrics']['comment_ratio'] /= len(maintainability['scores'])

        return maintainability
        
    def _detect_code_smells(self) -> List[Dict]:
        """Detect code smells."""
        smells = []
        
        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    rel_path = os.path.relpath(file_path, self.project_path)
                    
                    # Check for duplicate code
                    duplicates = self._find_duplicate_code(content)
                    if duplicates:
                        smells.append({
                            'type': 'duplicate_code',
                            'file': rel_path,
                            'details': duplicates
                        })
                        
                    # Check for long parameter lists
                    long_params = self._find_long_parameter_lists(content)
                    if long_params:
                        smells.append({
                            'type': 'long_parameter_list',
                            'file': rel_path,
                            'details': long_params
                        })
                        
        return smells
        
    def generate_report(self) -> str:
        """Generate a Markdown report about code quality."""
        data = self.analyze()
        
        report = [
            "# Code Quality Analysis Report\n",
            "## 📊 Complexity Metrics\n",
            
            "### Complexity Distribution",
            "| Complexity Level | Number of Files |",
            "|-----------------|-----------------|",
            f"| Low (1-10) | {data['complexity']['complexity_distribution']['low']} |",
            f"| Medium (11-20) | {data['complexity']['complexity_distribution']['medium']} |", 
            f"| High (21-30) | {data['complexity']['complexity_distribution']['high']} |",
            f"| Very High (>30) | {data['complexity']['complexity_distribution']['very_high']} |",
            
            "\n### Most Complex Files",
            "| File | Cyclomatic | Cognitive | Total |",
            "|------|------------|-----------|--------|"
        ]
        
        # Add complexity metrics
        for file_data in data['complexity']['files_by_complexity'][:10]:
            report.append(
                f"| {file_data['file']} | {file_data['cyclomatic']} | "
                f"{file_data['cognitive']} | {file_data['total']} |"
            )
            
        # Add maintainability metrics
        report.extend([
            "\n## 🔧 Maintainability Metrics\n",
            f"- Average Function Length: {data['maintainability']['metrics']['avg_function_length']:.1f} lines",
            f"- Maximum Function Length: {data['maintainability']['metrics']['max_function_length']} lines",
            f"- Functions Over 30 Lines: {data['maintainability']['metrics']['functions_over_30_lines']}",
            f"- Files Over 300 Lines: {data['maintainability']['metrics']['files_over_300_lines']}",
            f"- Comment Ratio: {data['maintainability']['metrics']['comment_ratio']*100:.1f}%",
            
            "\n### Issues Found",
            "#### Long Files",
            *[f"- {file}" for file in data['maintainability']['issues'].get('file_length', [])],
            "\n#### Long Functions",
            *[f"- {func}" for func in data['maintainability']['issues'].get('function_length', [])]
        ])
        
        # Add maintainability index section
        mi_score = data['maintainability']['metrics']['maintainability_index']
        mi_rating = self._get_maintainability_rating(mi_score)
        
        report.extend([
            f"\n## 📈 Maintainability Index: {mi_score:.1f}/100 ({mi_rating})\n",
            self._get_maintainability_badge(mi_score),
            "\nMaintainability ratings:",
            "- 🟢 Highly maintainable (76-100)",
            "- 🟡 Moderately maintainable (51-75)",
            "- 🔴 Difficult to maintain (0-50)"
        ])
        
        # Add suggestions section
        report.extend([
            "\n## 💡 Suggestions for Improvement\n"
        ])
        
        suggestions = self._generate_suggestions(data)
        for category, items in suggestions.items():
            report.extend([
                f"### {category}",
                *[f"- {item}" for item in items],
                ""
            ])
        
        # Add code smells section with severity levels
        report.extend([
            "\n## 🚨 Code Smells\n"
        ])
        
        for smell in data['code_smells']:
            severity = self._calculate_smell_severity(smell)
            icon = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}[severity]
            
            report.extend([
                f"### {icon} {smell['type'].replace('_', ' ').title()} (Severity: {severity})",
                f"File: {smell['file']}",
                "Details:",
                *[f"- {detail}" for detail in smell['details']],
                ""
            ])
            
        return '\n'.join(report)

    def _calculate_cyclomatic_complexity(self, content: str) -> int:
        """Calculate cyclomatic complexity."""
        # Count decision points
        decision_patterns = [
            r'\bif\b', r'\belse\b', r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bcatch\b', r'\b&&\b', r'\b\|\|\b'
        ]
        
        complexity = 1  # Base complexity
        for pattern in decision_patterns:
            complexity += len(re.findall(pattern, content))
            
        return complexity

    def _calculate_cognitive_complexity(self, content: str) -> int:
        """Calculate cognitive complexity."""
        # Simplified, can be expanded later
        cognitive_patterns = [
            (r'\bif\b', 1),
            (r'\belse if\b|\belseif\b', 2),
            (r'\bfor\b', 1),
            (r'\bwhile\b', 1),
            (r'\bcatch\b', 1),
            (r'\?', 1),  # Ternary operators
            (r'\b&&\b|\b\|\|\b', 1)
        ]
        
        complexity = 0
        for pattern, weight in cognitive_patterns:
            complexity += len(re.findall(pattern, content)) * weight
            
        return complexity

    def _find_long_functions(self, content: str) -> List[str]:
        """Find long functions."""
        long_functions = []
        
        # Pattern to match function declarations
        patterns = [
            r'function\s+(\w+)',
            r'(\w+)\s*=\s*function',
            r'(\w+)\s*:\s*function',
            r'(\w+)\s*\([^)]*\)\s*{',
            r'(\w+)\s*=\s*\([^)]*\)\s*=>'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                func_name = match.group(1)
                start_pos = match.start()
                
                # Find function end
                bracket_count = 0
                end_pos = start_pos
                in_function = False
                
                for i, char in enumerate(content[start_pos:], start_pos):
                    if char == '{':
                        bracket_count += 1
                        in_function = True
                    elif char == '}':
                        bracket_count -= 1
                        if in_function and bracket_count == 0:
                            end_pos = i
                            break
                
                if end_pos > start_pos:
                    func_content = content[start_pos:end_pos]
                    lines = func_content.count('\n')
                    if lines > 30:  # Threshold for long functions
                        long_functions.append(f"{func_name} ({lines} lines)")
                        
        return long_functions

    def _find_duplicate_code(self, content: str) -> List[str]:
        """Find duplicate code."""
        duplicates = []
        lines = content.split('\n')
        
        # Find similar blocks of code (simplified)
        block_size = 6  # Minimum lines to consider as a block
        blocks = {}
        
        for i in range(len(lines) - block_size + 1):
            block = '\n'.join(lines[i:i + block_size])
            if block.strip():
                blocks[block] = blocks.get(block, 0) + 1
                
        for block, count in blocks.items():
            if count > 1:
                first_line = block.split('\n')[0].strip()
                duplicates.append(f"Block starting with '{first_line}' repeated {count} times")
                
        return duplicates

    def _find_long_parameter_lists(self, content: str) -> List[str]:
        """Find functions with too many parameters."""
        long_params = []
        
        # Find function declarations with parameters
        pattern = r'(?:function\s+\w+|\w+\s*=\s*function|\w+\s*:)\s*\((.*?)\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            params = match.group(1).split(',')
            if len(params) > 4:  # Threshold for too many parameters
                func_name = re.search(r'\b\w+(?=\s*[(:=])', match.group(0))
                if func_name:
                    long_params.append(
                        f"{func_name.group(0)} has {len(params)} parameters"
                    )
                    
        return long_params 

    def _find_functions(self, content: str) -> List[Dict]:
        """Find all functions and their metrics."""
        functions = []
        
        patterns = [
            r'function\s+(\w+)',
            r'(\w+)\s*=\s*function',
            r'(\w+)\s*:\s*function',
            r'(\w+)\s*\([^)]*\)\s*{',
            r'(\w+)\s*=\s*\([^)]*\)\s*=>'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                func_info = {
                    'name': match.group(1),
                    'start': match.start(),
                    'length': 0,
                    'parameters': []
                }
                
                # Find function end and calculate length
                bracket_count = 0
                in_function = False
                
                for i, char in enumerate(content[match.start():], match.start()):
                    if char == '{':
                        bracket_count += 1
                        in_function = True
                    elif char == '}':
                        bracket_count -= 1
                        if in_function and bracket_count == 0:
                            func_content = content[match.start():i+1]
                            func_info['length'] = func_content.count('\n')
                            break
                            
                functions.append(func_info)
                
        return functions

    def _calculate_smell_severity(self, smell: Dict) -> str:
        """Calculate severity level for a code smell."""
        if smell['type'] == 'duplicate_code':
            count = len(smell['details'])
            if count > 5:
                return 'high'
            elif count > 2:
                return 'medium'
            return 'low'
            
        elif smell['type'] == 'long_parameter_list':
            max_params = max(int(d.split()[3]) for d in smell['details'])
            if max_params > 7:
                return 'high'
            elif max_params > 5:
                return 'medium'
            return 'low'
            
        return 'medium'  # Default severity 

    def _calculate_halstead_metrics(self, content: str) -> Dict:
        """Calculate Halstead complexity metrics."""
        operators = set()
        operands = set()
        
        # Basic operators
        operator_pattern = r'[+\-*/=<>!&|^~%]+'
        operators.update(re.findall(operator_pattern, content))
        
        # Keywords as operators
        keyword_pattern = r'\b(if|else|for|while|do|switch|case|break|continue|return|try|catch|throw)\b'
        operators.update(re.findall(keyword_pattern, content))
        
        # Identifiers and literals as operands
        operand_pattern = r'\b[a-zA-Z_]\w*\b|\b\d+\b|"[^"]*"|\'[^\']*\''
        operands.update(re.findall(operand_pattern, content))
        
        n1 = len(operators)  # Unique operators
        n2 = len(operands)   # Unique operands
        N1 = len(re.findall(operator_pattern, content))  # Total operators
        N2 = len(re.findall(operand_pattern, content))   # Total operands
        
        # Avoid division by zero
        if n1 == 0 or n2 == 0:
            return {'volume': 0, 'difficulty': 0, 'effort': 0}
            
        N = N1 + N2  # Program length
        n = n1 + n2  # Vocabulary size
        V = N * math.log2(n)  # Volume
        D = (n1 * N2) / (2 * n2)  # Difficulty
        E = D * V  # Effort
        
        return {
            'volume': V,
            'difficulty': D,
            'effort': E
        }

    def _calculate_maintainability_index(self, halstead_volume: float, 
                                       cyclomatic: int, loc: int, 
                                       comment_ratio: float) -> float:
        """Calculate maintainability index."""
        # Calculate base maintainability index using standard formula
        # MI = 171 - 5.2 * ln(HV) - 0.23 * CC - 16.2 * ln(LOC)
        try:
            mi = 171 - 5.2 * math.log(halstead_volume + 1) - 0.23 * cyclomatic - 16.2 * math.log(loc + 1)
            
            # Add comment weight
            mi += 50 * math.sin(math.sqrt(2.4 * comment_ratio))
            
            # Normalize to 0-100 scale
            mi = max(0, min(100, mi))
            
            return mi
        except Exception as e:
            logging.warning(f"Error calculating maintainability index: {str(e)}")
            return 50.0  # Return default value if calculation fails

    def _get_maintainability_rating(self, score: float) -> str:
        """Get rating based on maintainability score."""
        if score >= 76:
            return "Highly maintainable"
        elif score >= 51:
            return "Moderately maintainable"
        return "Difficult to maintain"

    def _get_maintainability_badge(self, score: float) -> str:
        """Generate maintainability badge."""
        if score >= 76:
            color = "brightgreen"
            icon = "🟢"
        elif score >= 51:
            color = "yellow"
            icon = "🟡"
        else:
            color = "red"
            icon = "🔴"
            
        return f"{icon} ![Maintainability](https://img.shields.io/badge/maintainability-{score:.1f}%25-{color})"

    def _generate_suggestions(self, data: Dict) -> Dict[str, List[str]]:
        """Generate improvement suggestions based on analysis."""
        suggestions = {
            'Code Organization': [],
            'Complexity': [],
            'Documentation': [],
            'Best Practices': []
        }
        
        # Complexity suggestions
        if data['complexity']['complexity_distribution']['high'] + \
           data['complexity']['complexity_distribution']['very_high'] > 0:
            suggestions['Complexity'].extend([
                "Consider breaking down complex functions into smaller, more manageable pieces",
                "Look for opportunities to simplify conditional logic",
                "Consider extracting complex calculations into separate utility functions"
            ])
            
        # Documentation suggestions
        comment_ratio = data['maintainability']['metrics']['comment_ratio']
        if comment_ratio < self.thresholds['min_comment_ratio']:
            suggestions['Documentation'].extend([
                f"Increase code documentation (current comment ratio: {comment_ratio*100:.1f}%)",
                "Add descriptive comments for complex logic",
                "Consider adding more function/method documentation"
            ])
            
        # Function length suggestions
        if data['maintainability']['metrics']['functions_over_30_lines'] > 0:
            suggestions['Code Organization'].extend([
                "Refactor long functions to improve readability and maintainability",
                "Consider extracting repeated code into helper functions",
                "Break down large functions into smaller, focused functions"
            ])
            
        # File length suggestions
        if data['maintainability']['metrics']['files_over_300_lines'] > 0:
            suggestions['Code Organization'].extend([
                "Consider splitting large files into smaller modules",
                "Look for opportunities to create new classes/modules",
                "Group related functionality into separate files"
            ])
            
        # Best practices
        if data['code_smells']:
            suggestions['Best Practices'].extend([
                "Address identified code smells to improve code quality",
                "Review and refactor duplicate code",
                "Consider implementing design patterns to improve code structure"
            ])
            
        return suggestions 

    def _check_best_practices(self) -> Dict:
        """Check adherence to best practices."""
        best_practices = {
            'violations': [],
            'recommendations': [],
            'metrics': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0
            }
        }

        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                    
                    rel_path = os.path.relpath(file_path, self.project_path)
                    
                    # Check line length
                    best_practices['metrics']['total_checks'] += 1
                    long_lines = [
                        i + 1 for i, line in enumerate(lines) 
                        if len(line.strip()) > 100
                    ]
                    if long_lines:
                        best_practices['violations'].append({
                            'type': 'line_length',
                            'file': rel_path,
                            'details': f"Lines exceeding 100 characters: {long_lines}"
                        })
                        best_practices['metrics']['failed_checks'] += 1
                    else:
                        best_practices['metrics']['passed_checks'] += 1
                    
                    # Check naming conventions
                    best_practices['metrics']['total_checks'] += 1
                    bad_names = self._check_naming_conventions(content)
                    if bad_names:
                        best_practices['violations'].append({
                            'type': 'naming_convention',
                            'file': rel_path,
                            'details': f"Non-conventional names found: {bad_names}"
                        })
                        best_practices['metrics']['failed_checks'] += 1
                    else:
                        best_practices['metrics']['passed_checks'] += 1
                    
                    # Check empty catch blocks
                    best_practices['metrics']['total_checks'] += 1
                    empty_catches = self._find_empty_catch_blocks(content)
                    if empty_catches:
                        best_practices['violations'].append({
                            'type': 'empty_catch',
                            'file': rel_path,
                            'details': "Empty catch blocks found"
                        })
                        best_practices['metrics']['failed_checks'] += 1
                    else:
                        best_practices['metrics']['passed_checks'] += 1

        # Add recommendations based on violations
        if any(v['type'] == 'line_length' for v in best_practices['violations']):
            best_practices['recommendations'].append(
                "Consider breaking long lines to improve readability (max 100 chars)"
            )
            
        if any(v['type'] == 'naming_convention' for v in best_practices['violations']):
            best_practices['recommendations'].append(
                "Follow standard naming conventions (camelCase for JS, snake_case for Python)"
            )
            
        if any(v['type'] == 'empty_catch' for v in best_practices['violations']):
            best_practices['recommendations'].append(
                "Avoid empty catch blocks - at least log the error"
            )

        return best_practices

    def _check_naming_conventions(self, content: str) -> List[str]:
        """Check for adherence to naming conventions."""
        bad_names = []
        
        # Check variable and function names
        patterns = {
            'python': r'\b(?:def|class)\s+([A-Z][a-z]+[A-Z]|\d.*|[a-z]+[A-Z].*)\b',  # Should be snake_case
            'javascript': r'\b(?:let|const|var|function)\s+(_.*|[A-Z].*)\b'  # Should be camelCase
        }
        
        for lang, pattern in patterns.items():
            matches = re.finditer(pattern, content)
            bad_names.extend(match.group(1) for match in matches)
            
        return bad_names

    def _find_empty_catch_blocks(self, content: str) -> bool:
        """Find empty catch blocks."""
        # Look for catch blocks with only comments or whitespace
        catch_pattern = r'catch\s*\([^)]*\)\s*{([^}]*)}'
        matches = re.finditer(catch_pattern, content)
        
        for match in matches:
            catch_body = match.group(1).strip()
            # Check if body is empty or only contains comments
            if not catch_body or all(line.strip().startswith(('/', '#', '*')) 
                                   for line in catch_body.split('\n')):
                return True
                
        return False 