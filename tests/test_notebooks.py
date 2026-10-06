import json
from pathlib import Path
import unittest

class NotebookTests(unittest.TestCase):
    def test_notebooks_are_valid_and_have_no_outputs(self):
        notebooks = list(Path("colab").glob("*.ipynb"))
        self.assertEqual(len(notebooks), 2)
        for path in notebooks:
            document = json.loads(path.read_text("utf-8"))
            self.assertEqual(document["nbformat"], 4)
            for cell in document["cells"]:
                if cell["cell_type"] == "code":
                    self.assertEqual(cell["outputs"], [])
                    self.assertIsNone(cell["execution_count"])
                    compile("".join(cell["source"]), str(path), "exec")

    def test_setup_notebook_matches_setup_module(self):
        document = json.loads(Path("colab/setup.ipynb").read_text("utf-8"))
        source = Path("setup_gcp.py").read_text("utf-8")
        self.assertTrue(any("".join(cell["source"]).startswith(source)
                            for cell in document["cells"] if cell["cell_type"] == "code"))
