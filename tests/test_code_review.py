import unittest
from unittest.mock import patch, MagicMock
from cursorfocus.code_review import CodeReviewGenerator

class TestCodeReview(unittest.TestCase):
    def setUp(self):
        self.reviewer = CodeReviewGenerator("dummy_api_key")
        
    def test_read_file_content(self):
        with patch("builtins.open", unittest.mock.mock_open(read_data="test content")):
            content = self.reviewer.read_file_content("test.py")
            self.assertEqual(content, "test content")
            
    def test_get_relevant_files(self):
        with patch("os.walk") as mock_walk:
            mock_walk.return_value = [
                ("/root", ["dir"], ["test.py", "test.js", "ignored.pyc"]),
            ]
            files = self.reviewer.get_relevant_files("/root")
            self.assertEqual(len(files), 2)
            self.assertTrue(any(f.endswith("test.py") for f in files))
            self.assertTrue(any(f.endswith("test.js") for f in files))
            
    def test_generate_function_description(self):
        description = self.reviewer._generate_function_description(
            "handleClick",
            "function handleClick(event) { }",
            "js"
        )
        self.assertTrue("handle" in description.lower())
        self.assertTrue("click" in description.lower())

if __name__ == '__main__':
    unittest.main() 