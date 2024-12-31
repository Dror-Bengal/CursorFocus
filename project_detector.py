import os
import json
from config import load_config

# Load project types from config at module level
_config = load_config()
PROJECT_TYPES = _config.get('project_types', {})

def detect_project_type(project_path):
    """Detect project type based on file presence using configurable rules."""
    # Add Bun project detection
    bun_indicators = [
        os.path.join(project_path, 'bunfig.toml'),
        os.path.join(project_path, 'bun.toml'),
        os.path.join(project_path, 'bun.lockb')
    ]
    if any(os.path.exists(path) for path in bun_indicators):
        return 'bun'
        
    for project_type, rules in PROJECT_TYPES.items():
        # Check for indicator files
        if any(os.path.exists(os.path.join(project_path, f)) for f in rules.get('indicators', [])):
            return project_type
            
        # Check for required files
        if rules.get('required_files') and all(os.path.exists(os.path.join(project_path, f)) for f in rules['required_files']):
            return project_type
            
    return 'generic'

def scan_for_projects(root_path, max_depth=3, ignored_dirs=None):
    """Scan directory recursively for projects."""
    if ignored_dirs is None:
        ignored_dirs = _config.get('ignored_directories', [])
    
    projects = []
    root_path = os.path.abspath(root_path or '.')
    
    # Check root directory first
    project_type = detect_project_type(root_path)
    if project_type != 'generic':
        projects.append({
            'path': root_path,
            'type': project_type,
            'name': os.path.basename(root_path)
        })
    
    def _scan_directory(current_path, current_depth):
        if current_depth > max_depth:
            return
            
        try:
            # Skip ignored directories
            if any(ignored in current_path.split(os.path.sep) for ignored in ignored_dirs):
                return
                
            # Scan subdirectories
            for item in os.listdir(current_path):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    # Check each subdirectory
                    project_type = detect_project_type(item_path)
                    if project_type != 'generic':
                        projects.append({
                            'path': item_path,
                            'type': project_type,
                            'name': item
                        })
                    else:
                        # If not a project, scan further
                        _scan_directory(item_path, current_depth + 1)
                    
        except (PermissionError, OSError):
            # Skip directories we can't access
            pass
    
    # Start scanning from root directory
    _scan_directory(root_path, 0)
    return projects

def get_project_description(project_path):
    """Get project description and key features using standardized approach."""
    try:
        project_type = detect_project_type(project_path)
        project_info = {
            "name": os.path.basename(project_path),
            "description": "Project directory structure and information",
            "key_features": [
                f"Type: {PROJECT_TYPES.get(project_type, {'description': 'Generic Project'})['description']}",
                "File and directory tracking",
                "Automatic updates"
            ]
        }
        
        if project_type == 'chrome_extension':
            manifest_path = os.path.join(project_path, 'manifest.json')
            if os.path.exists(manifest_path):
                with open(manifest_path, 'r') as f:
                    manifest_data = json.load(f)
                    project_info.update({
                        "name": manifest_data.get('name', 'Chrome Extension'),
                        "description": manifest_data.get('description', 'No description available'),
                        "key_features": [
                            f"Version: {manifest_data.get('version', 'unknown')}",
                            f"Type: {PROJECT_TYPES[project_type]['description']}",
                            *[f"Permission: {perm}" for perm in manifest_data.get('permissions', [])[:3]]
                        ]
                    })
                    
        elif project_type == 'node_js':
            package_path = os.path.join(project_path, 'package.json')
            if os.path.exists(package_path):
                with open(package_path, 'r') as f:
                    package_data = json.load(f)
                    project_info.update({
                        "name": package_data.get('name', 'Node.js Project'),
                        "description": package_data.get('description', 'No description available'),
                        "key_features": [
                            f"Version: {package_data.get('version', 'unknown')}",
                            f"Type: {PROJECT_TYPES[project_type]['description']}",
                            *[f"Dependency: {dep}" for dep in list(package_data.get('dependencies', {}).keys())[:3]]
                        ]
                    })
        
        return project_info
        
    except Exception as e:
        print(f"Error getting project description: {e}")
        return {
            "name": os.path.basename(project_path),
            "description": "Error reading project information",
            "key_features": ["File and directory tracking"]
        }

def get_file_type_info(filename):
    """Get file type information."""
    ext = os.path.splitext(filename)[1].lower()
    
    type_map = {
        '.py': ('Python Source', 'Python script containing project logic'),
        '.js': ('JavaScript', 'JavaScript file for client-side functionality'),
        '.jsx': ('React Component', 'React component file'),
        '.ts': ('TypeScript', 'TypeScript source file'),
        '.tsx': ('React TypeScript', 'React component with TypeScript'),
        '.html': ('HTML', 'Web page template'),
        '.css': ('CSS', 'Stylesheet for visual styling'),
        '.md': ('Markdown', 'Documentation file'),
        '.json': ('JSON', 'Configuration or data file')
    }
    
    return type_map.get(ext, ('Generic', 'Project file')) 