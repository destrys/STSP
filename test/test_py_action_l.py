import logging
from pathlib import Path
import numpy as np
import pytest

from stsp.runner import ActionLRunner
from stsp.stsp import ActionL, FittingProperties, PlanetProperties, StarProperties, SpotProperties



@pytest.fixture
def stsp_config_l() -> ActionL:
    """Build a sample STSPActionL config matching sample-l.in values."""
    planets = [
        PlanetProperties(
            t0_epoch_days=1.0,
            period_days=1.5,
            transit_depth=0.0038688,
            duration_days=0.120,
            impact_parameter=0.732,
            inclination_deg=90.0,
            lambda_deg=0.0,
            ecosw=0.0,
            esinw=0.0,
        )
    ]

    star = StarProperties(
        mean_stellar_density=1.3450000,
        stellar_rotation_period_days=12.0,
        temperature_kelvin=5576,
        stellar_metallicity=0.0,
        rotation_axis_tilt_deg=0.0,
        limb_darkening=(0.5742, -0.2175, 0.8311, -0.4144),
        num_limb_darkening_rings=100,
    )

    spots = SpotProperties(num_spots=6, fractional_brightness=0.70)

    # Use an absolute path so runs in temporary working directories succeed.
    sample_model = Path(__file__).resolve().parents[1] / "sample" / "model_lc.dat"
    fit = FittingProperties(
        data_filename=str(sample_model),
        start_time=0.0,
        light_curve_duration_days=12.0,
        light_data_max=996.942768414,
        light_curve_flattened=False,
    )

    spot_triplets = [
        (0.382525700680, 2.026108848159, 0.744618637426),
        (0.290572978656, 1.727405120396, 1.570800631939),
        (0.301035942796, 1.315591006119, 2.163399563938),
        (0.213239119426, 1.844123549292, 3.372735964458),
        (0.292627124386, 1.100571758314, 4.248530337143),
        (0.300349989200, 1.963252856264, 5.492592578403),
    ]
    cfg = ActionL(
        planets=planets,
        star_properties=star,
        spot_properties=spots,
        fitting_properties=fit,
        spot_triplets=spot_triplets,
        brightness_correction=1.0,
    )
    return cfg


def test_action_l_end_to_end(stsp_config_l, tmp_path):
    cfg = stsp_config_l
    runner = ActionLRunner(cfg)
    workdir, arr, copy_path = runner.run(workdir=tmp_path, emit_copy=True)

    # Input file
    in_path = Path(tmp_path) / "pyact-l.in"
    assert in_path.exists(), "Missing generated input file"

    # Output from C
    out_path = Path(tmp_path) / "pyact-l_lcout.txt"
    assert out_path.exists(), "Missing STSP output file"

    # Copy written by Python
    assert copy_path is not None and copy_path.exists(), "Missing Python-written copy of output"

    # Basic shape checks (at least 4 columns, at least 1 row)
    assert isinstance(arr, np.ndarray)
    assert arr.shape[1] >= 4
    assert arr.shape[0] > 0

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
    assert py.shape[1] == 4
    assert c.shape[0] == py.shape[0]

    # Use tolerances to account for decimal formatting on write
    np.testing.assert_allclose(c[:, :4], py, rtol=1e-10, atol=5e-7)
