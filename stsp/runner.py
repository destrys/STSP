import os
import shutil
import subprocess
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .stsp import FittingProperties, PlanetProperties, SpotProperties, STSP, StarProperties


def _ensure_binary() -> Path:
    """Ensure ./bin/stsp exists by building it if needed."""
    repo_root = Path(__file__).resolve().parents[1]
    bin_path = repo_root / "bin" / "stsp"
    if bin_path.exists():
        return bin_path
    # Build via make
    subprocess.run(["make"], cwd=str(repo_root), check=True)
    if not bin_path.exists():
        raise RuntimeError("Failed to build stsp binary at ./bin/stsp")
    return bin_path


def _write_l_input(
    config: STSP,
    spot_triplets: Sequence[Tuple[float, float, float]],
    brightness_correction: float,
    out_path: Path,
) -> None:
    """Write an Action-l input file at `out_path`.

    This mirrors the format used by sample/*.in and parsed by src/stsp.c.
    """
    if len(config.planets) < 1:
        raise ValueError("At least one planet is required for action l")
    if len(spot_triplets) != config.spot_properties.num_spots:
        raise ValueError(
            f"Expected {config.spot_properties.num_spots} spot triplets, got {len(spot_triplets)}"
        )

    p = config.planets[0]  # Action-l runs are typically single-planet
    s = config.star_properties
    sp = config.spot_properties
    f = config.fitting_properties

    lines: List[str] = []
    lines.append("#PLANET PROPERTIES\n")
    lines.append("1\n")  # Number of planets (Python API uses a list; write 1 here)
    lines.append(f"{p.t0_epoch_days}\t\t\t; T0, epoch         (middle of first transit) in days.\n")
    lines.append(f"{p.period_days}\t\t\t; Planet Period      (days)\n")
    lines.append(f"{p.transit_depth}\t\t; (Rp/Rs)^2         (Rplanet / Rstar )^ 2\n")
    lines.append(f"{p.duration_days}\t\t\t; Duration (days)   (physical duration of transit, not used)\n")
    lines.append(f"{p.impact_parameter}\t\t\t; Impact parameter  (0= planet cross over equator)\n")
    lines.append(f"{p.inclination_deg}\t\t\t; Inclination angle of orbit (90 deg = planet crosses over equator)\n")
    lines.append(f"{p.lambda_deg}\t\t\t; Lambda of orbit (0 deg = orbital axis along z-axis)\n")
    lines.append(f"{p.ecosw}\t\t\t; ecosw\n")
    lines.append(f"{p.esinw}\t\t\t; esinw\n")

    lines.append("#STAR PROPERTIES\n")
    lines.append(f"{s.mean_stellar_density}\t\t; Mean Stellar density (Msun/Rsun^3)\n")
    lines.append(f"{s.stellar_rotation_period_days}\t\t\t; Stellar Rotation period (days)\n")
    lines.append(f"{s.temperature_kelvin}\t\t\t; Stellar Temperature\n")
    lines.append(f"{s.stellar_metallicity}\t\t\t; Stellar metallicity\n")
    lines.append(
        f"{s.rotation_axis_tilt_deg}\t\t\t; Tilt of the rotation axis of the star down from z-axis (degrees)\n"
    )
    lines.append(
        f"{s.limb_darkening[0]} {s.limb_darkening[1]} {s.limb_darkening[2]} {s.limb_darkening[3]}\t; Limb darkening (4 coefficients)\n"
    )
    lines.append(f"{s.num_limb_darkening_rings}\t\t\t; number of rings for limb darkening appoximation\n")

    lines.append("#SPOT PROPERTIES\n")
    lines.append(f"{sp.num_spots}\t\t\t\t; number of spots\n")
    lines.append(
        f"{sp.fractional_brightness}\t\t\t\t; fractional lightness of spots (0.0=total dark, 1.0=same as star)\n"
    )

    lines.append("#LIGHT CURVE\n")
    lines.append(
        f"{config.fitting_properties.data_filename}\t\t\t; light curve input data file (only used to get times for generating lightcurve)\n"
    )
    lines.append(f"{f.start_time}\t\t\t\t; start time to start fitting the light curve\n")
    lines.append(f"{f.light_curve_duration_days}\t\t\t; duration of light curve to fit (days)\n")
    lines.append(
        f"{f.light_data_max}\t\t\t; real maximum of light curve data (corrected for noise), 0 -> use downfrommax\t\n"
    )
    lines.append(
        f"{1 if f.light_curve_flattened else 0}\t\t\t\t; is light curve flattened (to zero) outside of transits?\n"
    )

    lines.append("#ACTION\n")
    lines.append("l\t\t\t; l= generate light curve from parameters\n")
    for (r, th, ph) in spot_triplets:
        lines.append(f"{r}\n{th}\n{ph}\n")
    lines.append(f"{brightness_correction}\n")

    out_path.write_text("".join(lines))


def run_action_l(
    config: STSP,
    spot_triplets: Sequence[Tuple[float, float, float]],
    brightness_correction: float = 1.0,
    workdir: Optional[Path] = None,
) -> Tuple[Path, np.ndarray, Path]:
    """Run Action-l end-to-end.

    - Writes `pyact-l.in` in `workdir` (or a temp dir if None).
    - Runs `./bin/stsp` with that config.
    - Reads the output `*_lcout.txt` into a numpy array.
    - Writes a second C-compatible copy named `pyact-l-copy.txt` in `workdir`.

    Returns: (workdir, numpy_array, copy_path)
    """
    bin_path = _ensure_binary()

    # Prepare working directory
    made_temp = False
    if workdir is None:
        tdir = tempfile.TemporaryDirectory()
        made_temp = True
        work = Path(tdir.name)
    else:
        work = Path(workdir)
        work.mkdir(parents=True, exist_ok=True)

    try:
        # Ensure model_lc.dat is present
        src_model = Path(__file__).resolve().parents[1] / "sample" / "model_lc.dat"
        dst_model = work / "model_lc.dat"
        if not dst_model.exists():
            shutil.copy2(src_model, dst_model)

        # Input path
        in_path = work / "pyact-l.in"

        # If the fitting properties point to a filename only, keep it; otherwise
        # rewrite to basename so stsp reads the local file.
        fit = config.fitting_properties
        local_fit = FittingProperties(
            data_filename=Path(fit.data_filename).name,
            start_time=fit.start_time,
            light_curve_duration_days=fit.light_curve_duration_days,
            light_data_max=fit.light_data_max,
            light_curve_flattened=fit.light_curve_flattened,
        )
        cfg = STSP(
            planets=config.planets,
            star_properties=config.star_properties,
            spot_properties=config.spot_properties,
            fitting_properties=local_fit,
        )

        _write_l_input(cfg, spot_triplets, brightness_correction, in_path)

        # Run stsp with absolute config path so output uses the same rootname
        proc = subprocess.run([str(bin_path), str(in_path)], cwd=str(work), check=True)

        # Output path is <root>_lcout.txt where root is input path without .in
        rootname = str(in_path).rsplit(".in", 1)[0]
        out_path = Path(f"{rootname}_lcout.txt")
        if not out_path.exists():
            raise FileNotFoundError(f"Expected output not found: {out_path}")

        # Read into numpy
        arr = np.loadtxt(out_path)

        # Write C-compatible copy
        copy_path = work / "pyact-l-copy.txt"
        with copy_path.open("w") as f:
            for row in np.atleast_2d(arr):
                # Match the default lcgen formatting: time 9 dp, others 6 dp
                if row.shape[0] >= 4:
                    f.write(
                        f"{row[0]:0.9f} {row[1]:0.6f} {row[2]:0.6f} {row[3]:0.6f}\n"
                    )
                else:
                    # Fallback: join with 6 dp
                    f.write(" ".join(f"{x:0.6f}" for x in row) + "\n")

        return work, arr, copy_path
    finally:
        if made_temp:
            # Keep the temp dir alive for caller inspection? For now, cleanup.
            # If persistent is desired, we could return the TemporaryDirectory object.
            pass


def example_sample_config() -> Tuple[STSP, List[Tuple[float, float, float]], float]:
    """Build a sample STSP config matching sample-l.in values."""
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

    fit = FittingProperties(
        data_filename="model_lc.dat",
        start_time=0.0,
        light_curve_duration_days=12.0,
        light_data_max=996.942768414,
        light_curve_flattened=False,
    )

    cfg = STSP(planets=planets, star_properties=star, spot_properties=spots, fitting_properties=fit)

    spot_triplets = [
        (0.382525700680, 2.026108848159, 0.744618637426),
        (0.290572978656, 1.727405120396, 1.570800631939),
        (0.301035942796, 1.315591006119, 2.163399563938),
        (0.213239119426, 1.844123549292, 3.372735964458),
        (0.292627124386, 1.100571758314, 4.248530337143),
        (0.300349989200, 1.963252856264, 5.492592578403),
    ]

    brightness = 1.0

    return cfg, spot_triplets, brightness

