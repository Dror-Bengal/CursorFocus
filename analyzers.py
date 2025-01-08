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

def get_combined_pattern():
    """Combine all function patterns into a single regex pattern."""
    return '|'.join(f'(?:{pattern})' for pattern in FUNCTION_PATTERNS.values())

def is_binary_file(filename):
    """Check if a file is binary or non-code based on its extension."""
    ext = os.path.splitext(filename)[1].lower()

    # Binary extensions
    if ext in BINARY_EXTENSIONS:
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
    """Analyze file content for functions and their descriptions."""
    try:
        # Skip binary and non-code files
        if is_binary_file(file_path):
            return [], 0

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Skip files that don't look like actual code files
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in CODE_EXTENSIONS:
            return [], 0

        functions = []
        duplicates = find_duplicate_functions(content, file_path)

        # Use combined pattern for function detection
        combined_pattern = get_combined_pattern()

        matches = re.finditer(combined_pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            func_name = next(filter(None, match.groups()), None)
            if not func_name or func_name.lower() in IGNORED_KEYWORDS:
                continue

            # Get comment block before function
            start = match.start()
            comment_block = content[:start].strip().split('\n')[-10:]  # Get up to 10 lines before function
            description = parse_comments(comment_block)

            # If no comment found or comment is too generic, analyze function content
            if not description or len(description[0].split()) < 5:
                # Extract detailed context from function body
                context_description = extract_function_context(content, start)

                # Analyze function name parts for additional context
                name_parts = re.findall('[A-Z][a-z]*|[a-z]+', func_name)
                verb = name_parts[0].lower() if name_parts else ''
                subject = ' '.join(name_parts[1:]).lower() if len(name_parts) > 1 else ''

                # Combine name analysis with context analysis
                if verb in ['is', 'has', 'should', 'can', 'will']:
                    description = [f"Validates if {subject} meets criteria | {context_description}"]
                elif verb in ['get', 'fetch', 'retrieve']:
                    description = [f"Retrieves {subject} data | {context_description}"]
                elif verb in ['set', 'update', 'modify']:
                    description = [f"Updates {subject} | {context_description}"]
                elif verb in ['calc', 'compute', 'calculate']:
                    description = [f"Calculates {subject} | {context_description}"]
                elif verb in ['handle', 'process']:
                    description = [f"Processes {subject} | {context_description}"]
                elif verb in ['validate', 'verify']:
                    description = [f"Validates {subject} | {context_description}"]
                elif verb in ['create', 'init', 'initialize']:
                    description = [f"Creates {subject} | {context_description}"]
                elif verb in ['sort', 'order']:
                    description = [f"Sorts {subject} | {context_description}"]
                else:
                    description = [context_description]

            final_description = ' '.join(description)

            # Add duplicate alert if needed, now with simplified line reporting
            if func_name in duplicates:
                first_line, count = duplicates[func_name]
                final_description += f" **🔄 Duplicate Alert: Function appears {count} times (first occurrence: line {first_line})**"

            functions.append((func_name, final_description))

        return functions, len(content.split('\n'))
    except Exception as e:
        print(f"Error analyzing file {file_path}: {e}")
        return [], 0

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
