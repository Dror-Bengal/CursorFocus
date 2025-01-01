import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

class BaseAnalyzer(ABC):
    """Base class for all analyzers."""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup logging for the analyzer."""
        logger = logging.getLogger(self.__class__.__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        self.logger = logger

    @abstractmethod
    def analyze(self) -> Dict[str, Any]:
        """Analyze the project and return results."""
        pass

    @abstractmethod
    def generate_report(self) -> str:
        """Generate a Markdown report from analysis results."""
        pass

    def _get_empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure when analysis fails."""
        return {}

    def safe_execute(self, func: callable, error_msg: str, default_return: Any = None) -> Any:
        """Safely execute a function with error handling."""
        try:
            return func()
        except Exception as e:
            self.logger.error(f"{error_msg}: {str(e)}")
            return default_return 