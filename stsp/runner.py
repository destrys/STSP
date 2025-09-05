import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .stsp import FittingProperties, PlanetProperties, STSP, StarProperties, SpotProperties


class ActionRunner:
    """Base class to assemble common STSP configuration and run an action.

    Subclasses provide the action-specific section via `assemble_action()` and
    can override `input_basename()` to control input/output file roots.
    """

    def __init__(self, config: STSP):
        self.config = config

    # ----- Assembly helpers (no side effects) -----
    def assemble_common(self) -> str:
        """Assemble the common (non-action) sections as a single string."""
        if len(self.config.planets) < 1:
            raise ValueError("At least one planet must be provided in config.planets")

        s = self.config.star_properties
        sp = self.config.spot_properties
        f = self.config.fitting_properties

        lines: List[str] = []

        # PLANET PROPERTIES
        lines.append("#PLANET PROPERTIES\n")
        lines.append(f"{len(self.config.planets)}\n")
        for p in self.config.planets:
            lines.append(f"{p.t0_epoch_days}\n")
            lines.append(f"{p.period_days}\n")
            lines.append(f"{p.transit_depth}\n")
            lines.append(f"{p.duration_days}\n")
            lines.append(f"{p.impact_parameter}\n")
            lines.append(f"{p.inclination_deg}\n")
            lines.append(f"{p.lambda_deg}\n")
            lines.append(f"{p.ecosw}\n")
            lines.append(f"{p.esinw}\n")

        # STAR PROPERTIES
        lines.append("#STAR PROPERTIES\n")
        lines.append(f"{s.mean_stellar_density}\n")
        lines.append(f"{s.stellar_rotation_period_days}\n")
        lines.append(f"{s.temperature_kelvin}\n")
        lines.append(f"{s.stellar_metallicity}\n")
        lines.append(f"{s.rotation_axis_tilt_deg}\n")
        lines.append(
            f"{s.limb_darkening[0]} {s.limb_darkening[1]} {s.limb_darkening[2]} {s.limb_darkening[3]}\n"
        )
        lines.append(f"{s.num_limb_darkening_rings}\n")

        # SPOT PROPERTIES
        lines.append("#SPOT PROPERTIES\n")
        lines.append(f"{sp.num_spots}\n")
        lines.append(f"{sp.fractional_brightness}\n")

        # LIGHT CURVE
        lines.append("#LIGHT CURVE\n")
        lines.append(f"{f.data_filename}\n")
        lines.append(f"{f.start_time}\n")
        lines.append(f"{f.light_curve_duration_days}\n")
        lines.append(f"{f.light_data_max}\n")
        lines.append(f"{1 if f.light_curve_flattened else 0}\n")

        return "".join(lines)

    def assemble_action(self) -> str:
        """Override in subclass to provide action-specific lines including #ACTION."""
        raise NotImplementedError

    def input_basename(self) -> str:
        """Override to control the input filename base (without extension)."""
        return "pyact"

    # ----- Top-level run (side effects) -----
    def run(self, workdir: Optional[Path] = None) -> Tuple[Path, np.ndarray, Path]:

        # Prepare working directory
        made_temp = False
        if workdir is None:
            tdir = tempfile.TemporaryDirectory()
            made_temp = True
            work = Path(tdir.name)
        else:
            work = Path(workdir)
            work.mkdir(parents=True, exist_ok=True)

        # Assemble configuration text
        common = self.assemble_common()
        action = self.assemble_action()

        in_path = work / f"{self.input_basename()}.in"
        in_path.write_text(common + action)

        # Run stsp (assumes 'stsp' is available on PATH)
        subprocess.run(["stsp", str(in_path)], cwd=str(work), check=True)

        # Read outputs
        rootname = str(in_path).rsplit(".in", 1)[0]
        out_path = Path(f"{rootname}_lcout.txt")
        if not out_path.exists():
            raise FileNotFoundError(f"Expected output not found: {out_path}")
        arr = np.loadtxt(out_path)

        # Write a C-compatible copy
        copy_path = work / f"{self.input_basename()}-copy.txt"
        with copy_path.open("w") as f:
            for row in np.atleast_2d(arr):
                # Preserve enough precision to avoid loss when re-reading as float64.
                # Use 17 significant digits which is sufficient for IEEE-754 double.
                if row.shape[0] >= 4:
                    f.write(
                        f"{row[0]:.17g} {row[1]:.17g} {row[2]:.17g} {row[3]:.17g}\n"
                    )
                else:
                    f.write(" ".join(f"{x:.17g}" for x in row) + "\n")

        return work, arr, copy_path


class ActionLRunner(ActionRunner):
    def __init__(
        self,
        config: STSP,
        spot_triplets: Sequence[Tuple[float, float, float]],
        brightness_correction: float = 1.0,
    ) -> None:
        super().__init__(config)
        if len(spot_triplets) != config.spot_properties.num_spots:
            raise ValueError(
                f"Expected {config.spot_properties.num_spots} spot triplets, got {len(spot_triplets)}"
            )
        self.spot_triplets = list(spot_triplets)
        self.brightness_correction = brightness_correction

    def input_basename(self) -> str:
        return f"{super().input_basename()}-l"

    def assemble_action(self) -> str:
        lines: List[str] = []
        lines.append("#ACTION\n")
        lines.append("l\n")
        for (r, th, ph) in self.spot_triplets:
            lines.append(f"{r}\n{th}\n{ph}\n")
        lines.append(f"{self.brightness_correction}\n")
        return "".join(lines)


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

    # Use an absolute path so runs in temporary working directories succeed.
    sample_model = Path(__file__).resolve().parents[1] / "sample" / "model_lc.dat"
    fit = FittingProperties(
        data_filename=str(sample_model),
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
