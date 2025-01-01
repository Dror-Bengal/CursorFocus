import re
import os
from typing import Dict, List, Optional
from collections import defaultdict
from .base_analyzer import BaseAnalyzer

class APIDocAnalyzer(BaseAnalyzer):
    def __init__(self, project_path: str):
        super().__init__(project_path)
        self.api_patterns = {
            'rest': r'@api\s+{([^}]+)}\s+([^\n]+)',
            'method': r'@method\s+(\w+)',
            'param': r'@param\s+{([^}]+)}\s+(\w+)\s+([^\n]+)',
            'returns': r'@returns?\s+{([^}]+)}\s+([^\n]+)',
            'example': r'@example\s+([^\n]+)',
            'description': r'@description\s+([^\n]+)',
            'route': r'@route\s+([^\n]+)'
        }

    def analyze(self) -> Dict:
        """Analyze API documentation in the project."""
        return self.safe_execute(
            self._analyze_api_docs,
            "Error analyzing API documentation",
            self._get_empty_analysis()
        )

    def _analyze_api_docs(self) -> Dict:
        """Internal method to analyze API documentation."""
        api_docs = {
            'endpoints': [],
            'models': defaultdict(dict),
            'services': defaultdict(list),
            'total_endpoints': 0,
            'coverage': {
                'documented': 0,
                'undocumented': 0,
                'coverage_ratio': 0
            }
        }

        for root, _, files in os.walk(self.project_path):
            for file in files:
                if file.endswith(('.js', '.ts', '.py')):
                    file_path = os.path.join(root, file)
                    self._analyze_file(file_path, api_docs)

        # Calculate coverage ratio
        total = api_docs['coverage']['documented'] + api_docs['coverage']['undocumented']
        api_docs['coverage']['coverage_ratio'] = (
            api_docs['coverage']['documented'] / total if total > 0 else 0
        )

        return api_docs

    def _analyze_file(self, file_path: str, api_docs: Dict) -> None:
        """Analyze a single file for API documentation."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Extract API documentation
            endpoints = self._extract_endpoints(content)
            if endpoints:
                rel_path = os.path.relpath(file_path, self.project_path)
                for endpoint in endpoints:
                    endpoint['file'] = rel_path
                    api_docs['endpoints'].append(endpoint)
                    api_docs['total_endpoints'] += 1
                    
                    if endpoint.get('documented', False):
                        api_docs['coverage']['documented'] += 1
                    else:
                        api_docs['coverage']['undocumented'] += 1
        except Exception as e:
            self.logger.warning(f"Error analyzing file {file_path}: {str(e)}")

    def _get_empty_analysis(self) -> Dict:
        """Return empty analysis structure when analysis fails."""
        return {
            'endpoints': [],
            'models': defaultdict(dict),
            'services': defaultdict(list),
            'total_endpoints': 0,
            'coverage': {
                'documented': 0,
                'undocumented': 0,
                'coverage_ratio': 0
            }
        }

    def _extract_endpoints(self, content: str) -> List[Dict]:
        """Extract API endpoint documentation."""
        endpoints = []
        
        # Find all API documentation blocks
        api_blocks = re.finditer(r'/\*\*[\s\S]*?\*/', content)
        
        for block in api_blocks:
            doc_block = block.group(0)
            endpoint = {
                'method': None,
                'path': None,
                'description': None,
                'params': [],
                'returns': None,
                'examples': [],
                'documented': False
            }
            
            # Extract API information
            api_match = re.search(self.api_patterns['rest'], doc_block)
            if api_match:
                endpoint['method'], endpoint['path'] = api_match.groups()
                endpoint['documented'] = True
                
                # Extract method
                method_match = re.search(self.api_patterns['method'], doc_block)
                if method_match:
                    endpoint['method'] = method_match.group(1)
                
                # Extract description
                desc_match = re.search(self.api_patterns['description'], doc_block)
                if desc_match:
                    endpoint['description'] = desc_match.group(1)
                
                # Extract parameters
                param_matches = re.finditer(self.api_patterns['param'], doc_block)
                for param in param_matches:
                    param_type, param_name, param_desc = param.groups()
                    endpoint['params'].append({
                        'name': param_name,
                        'type': param_type,
                        'description': param_desc
                    })
                
                # Extract return type
                returns_match = re.search(self.api_patterns['returns'], doc_block)
                if returns_match:
                    return_type, return_desc = returns_match.groups()
                    endpoint['returns'] = {
                        'type': return_type,
                        'description': return_desc
                    }
                
                # Extract examples
                example_matches = re.finditer(self.api_patterns['example'], doc_block)
                endpoint['examples'] = [m.group(1) for m in example_matches]
                
                endpoints.append(endpoint)

        return endpoints

    def generate_report(self) -> str:
        """Generate a Markdown report for API documentation."""
        data = self.analyze()
        
        report = [
            "# API Documentation Report\n",
            "## 📊 Overview\n",
            f"Total Endpoints: **{data['total_endpoints']}**\n",
            "### Documentation Coverage",
            f"- Documented Endpoints: {data['coverage']['documented']}",
            f"- Undocumented Endpoints: {data['coverage']['undocumented']}",
            f"- Coverage Ratio: {data['coverage']['coverage_ratio']*100:.1f}%\n",
            "## 🔌 API Endpoints\n"
        ]

        # Group endpoints by method
        endpoints_by_method = defaultdict(list)
        for endpoint in data['endpoints']:
            endpoints_by_method[endpoint['method']].append(endpoint)

        # Add endpoints documentation
        for method in sorted(endpoints_by_method.keys()):
            report.append(f"### {method} Endpoints\n")
            
            for endpoint in endpoints_by_method[method]:
                report.extend([
                    f"#### `{endpoint['path']}`",
                    f"**File:** `{endpoint['file']}`\n",
                    f"{endpoint['description']}\n" if endpoint['description'] else "",
                    "**Parameters:**" if endpoint['params'] else "**No Parameters**"
                ])
                
                if endpoint['params']:
                    report.extend([
                        "| Name | Type | Description |",
                        "|------|------|-------------|"
                    ])
                    for param in endpoint['params']:
                        report.append(
                            f"| {param['name']} | `{param['type']}` | {param['description']} |"
                        )
                
                if endpoint['returns']:
                    report.extend([
                        "\n**Returns:**",
                        f"- Type: `{endpoint['returns']['type']}`",
                        f"- Description: {endpoint['returns']['description']}"
                    ])
                
                if endpoint['examples']:
                    report.extend([
                        "\n**Examples:**",
                        *[f"```\n{example}\n```" for example in endpoint['examples']]
                    ])
                
                report.append("\n---\n")

        return '\n'.join(report) 