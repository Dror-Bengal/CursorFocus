"""
CursorFocus - AI-powered code review and project analysis tool
"""

__version__ = "1.0.0"
__author__ = "Dror Bengal"

from .code_review import CodeReviewGenerator
from .focus import Focus
from .analyzers import CodeAnalyzer
from .project_detector import ProjectDetector

__all__ = [
    'CodeReviewGenerator',
    'Focus',
    'CodeAnalyzer',
    'ProjectDetector'
] 