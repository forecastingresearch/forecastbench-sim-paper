import unittest,subprocess,sys,tempfile
from pathlib import Path
class Entry(unittest.TestCase):
 def test_smoke(self):subprocess.run([sys.executable,'-m','fbsim_paper','smoke'],check=True,capture_output=True)
 def test_missing_data_fails_without_fetch(self):
  with tempfile.TemporaryDirectory() as d:self.assertNotEqual(subprocess.run([sys.executable,'-m','fbsim_paper','validate','--data-root',d],capture_output=True).returncode,0)
