import logging
import unittest
from pathlib import Path
import tempfile
import numpy as np

from stsp.runner import ActionLRunner, example_sample_config


class TestActionL(unittest.TestCase):
    def test_action_l_end_to_end(self):
        cfg, spot_triplets, brightness = example_sample_config()

        with tempfile.TemporaryDirectory() as td:
            work = Path(td)
            runner = ActionLRunner(cfg, spot_triplets, brightness_correction=brightness)
            workdir, arr, copy_path = runner.run(workdir=work)

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

            # Debug: log the first 5 lines of each output for troubleshooting
            logger = logging.getLogger(__name__)
            try:
                with out_path.open("r") as f:
                    out_preview = "".join(f.readlines()[:5])
                with copy_path.open("r") as f:
                    py_preview = "".join(f.readlines()[:5])
                logger.info("C output (first 5 lines) from %s:\n%s", out_path.name, out_preview)
                logger.info("Python copy (first 5 lines) from %s:\n%s", copy_path.name, py_preview)
            except Exception as e:
                logger.info("Preview logging failed: %s", e)

            # Verify Python copy numerically matches C output (first 4 columns)
            c = np.loadtxt(out_path)
            py = np.loadtxt(copy_path)
            # Compare equal shapes in columns (py has exactly 4 columns by writer design)
            self.assertEqual(py.shape[1], 4)
            self.assertEqual(c.shape[0], py.shape[0])

            # Use tolerances to account for decimal formatting on write
            np.testing.assert_allclose(c[:, :4], py, rtol=1e-10, atol=5e-7)


if __name__ == "__main__":
    unittest.main()
