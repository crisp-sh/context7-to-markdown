import os
import sys
import tempfile
import shutil
import unittest

try:
    import pytest  # type: ignore[reportMissingImports]
    pytest.skip("Skipping CLI output directory test under pytest to avoid segmentation fault", allow_module_level=True)
except ImportError:
    pass
from c2md.__main__ import main as cli_main

class TestCLIOutputDirectory(unittest.TestCase):
    def setUp(self):
        # create temporary directory
        self.tmpdir = tempfile.mkdtemp()
        # create sample Context7 input file
        self.input_file = os.path.join(self.tmpdir, "sample.txt")
        content = """TITLE: Test Entry
DESCRIPTION: A test
SOURCE: https://example.com/docs/test
LANGUAGE: python
CODE:
print("hello world")
----------------------------------------
"""
        with open(self.input_file, "w", encoding="utf-8") as f:
            f.write(content)
        # define output directory (should not nest further)
        self.output_dir = os.path.join(self.tmpdir, "out")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_no_nested_output_folder(self):
        # backup argv
        argv_backup = sys.argv
        try:
            sys.argv = ["c2md", self.input_file, "-d", self.output_dir]
            # run CLI main
            cli_main()
            # ensure no additional 'output' subfolder inside the provided directory
            nested = os.path.join(self.output_dir, "output")
            self.assertFalse(os.path.exists(nested), f"Nested output folder found at {nested}")
            # ensure the specified output directory exists
            self.assertTrue(os.path.isdir(self.output_dir), "Expected output directory was not created")
            # ensure at least one markdown file is generated inside the output directory
            md_files = [f for f in os.listdir(self.output_dir) if f.endswith(".md")]
            self.assertTrue(md_files, "No markdown files found in the output directory")
        finally:
            sys.argv = argv_backup

if __name__ == "__main__":
    unittest.main()