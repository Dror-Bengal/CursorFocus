import os
from datetime import datetime
from analyzers import (
    analyze_file_content,
    should_ignore_file,
    is_binary_file,
    CodeReviewAnalyzer
)
from project_detector import detect_project_type, get_project_description, get_file_type_info
from config import get_file_length_limit, load_config
import json
import logging
from typing import List

class ProjectMetrics:
    def __init__(self):
        self.total_files = 0
        self.total_lines = 0
        self.files_by_type = {}
        self.lines_by_type = {}
        self.alerts = {
            'warning': 0,
            'critical': 0,
            'severe': 0
        }
        self.duplicate_functions = 0

def get_file_length_alert(line_count, limit, thresholds):
    """Get alert level based on file length and thresholds."""
    ratio = line_count / limit
    if ratio >= thresholds.get('severe', 2.0):
        return 'severe', f"🚨 Critical-Length Alert: File is more than {int(thresholds['severe']*100)}% of recommended length"
    elif ratio >= thresholds.get('critical', 1.5):
        return 'critical', f"⚠️ High-Length Alert: File is more than {int(thresholds['critical']*100)}% of recommended length"
    elif ratio >= thresholds.get('warning', 1.0):
        return 'warning', f"📄 Length Alert: File exceeds recommended length"
    return None, None

def generate_focus_content(project_path: str) -> str:
    """Generate focus content for the project"""
    try:
        files = get_relevant_files(project_path)
        if not files:
            return "No relevant files found for analysis."
            
        # Filter out any CursorFocus files that might have slipped through
        cursorfocus_path = os.path.join(project_path, 'CursorFocus')
        files = [f for f in files if not f.startswith(cursorfocus_path)]
        
        # Rest of the method remains the same...
    except Exception as e:
        logging.error(f"Error generating focus content: {str(e)}", exc_info=True)
        return f"Error generating focus content: {str(e)}"

def get_directory_structure(project_path, max_depth=3, current_depth=0):
    """Get the directory structure."""
    if current_depth > max_depth:
        return {}
    
    structure = {}
    try:
        for item in os.listdir(project_path):
            if should_ignore_file(item):
                continue
                
            item_path = os.path.join(project_path, item)
            
            if os.path.isdir(item_path):
                substructure = get_directory_structure(item_path, max_depth, current_depth + 1)
                if substructure:
                    structure[item] = substructure
            else:
                structure[item] = None
    except Exception as e:
        print(f"Error scanning directory {project_path}: {e}")
    
    return structure

def structure_to_tree(structure, prefix=''):
    """Convert directory structure to tree format."""
    lines = []
    items = sorted(list(structure.items()), key=lambda x: (x[1] is not None, x[0]))
    
    for i, (name, substructure) in enumerate(items):
        is_last = i == len(items) - 1
        connector = '└─ ' if is_last else '├─ '
        
        if substructure is None:
            icon = '📄 '
            lines.append(f"{prefix}{connector}{icon}{name}")
        else:
            icon = '📁 '
            lines.append(f"{prefix}{connector}{icon}{name}")
            extension = '   ' if is_last else '│  '
            lines.extend(structure_to_tree(substructure, prefix + extension))
    
    return lines 

def get_relevant_files(project_path: str) -> List[str]:
    """Get list of relevant files for review"""
    ignored = {'.git', 'node_modules', '.next', 'dist', 'build', 'coverage', 'CursorFocus'}
    files = []
    
    cursorfocus_path = os.path.join(project_path, 'CursorFocus')
    
    for root, dirs, filenames in os.walk(project_path):
        # Skip CursorFocus directory and other ignored directories
        dirs[:] = [d for d in dirs if d not in ignored]
        
        # Skip if we're in the CursorFocus directory or its subdirectories
        if root.startswith(cursorfocus_path):
            continue
            
        for filename in filenames:
            if filename.endswith(('.js', '.jsx', '.ts', '.tsx', '.py', '.css', '.scss')):
                file_path = os.path.join(root, filename)
                # Double check we're not including any CursorFocus files
                if not file_path.startswith(cursorfocus_path):
                    files.append(file_path)
    return files 