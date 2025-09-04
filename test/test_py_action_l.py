import unittest
from pathlib import Path
import tempfile
import numpy as np

from stsp.runner import example_sample_config, run_action_l


class TestActionL(unittest.TestCase):
    def test_action_l_end_to_end(self):
        cfg, spot_triplets, brightness = example_sample_config()

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            workdir, arr, copy_path = run_action_l(cfg, spot_triplets, brightness_correction=brightness, workdir=work)

            # Input file
            in_path = work / "pyact-l.in"
            self.assertTrue(in_path.exists(), "Missing generated input file")

            # Output from C
            out_path = work / "pyact-l_lcout.txt"
            self.assertTrue(out_path.exists(), "Missing STSP output file")

            # Copy written by Python
            self.assertTrue(copy_path.exists(), "Missing Python-written copy of output")

            # Basic shape checks (at least 4 columns, at least 1 row)
            self.assertIsInstance(arr, np.ndarray)
            self.assertGreaterEqual(arr.shape[1], 4)
            self.assertGreater(arr.shape[0], 0)


if __name__ == "__main__":
    unittest.main()

