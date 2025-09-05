import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

import numpy as np

from stsp.stsp import (
    STSP,
    STSPActionL,
    STSPActionM,
    PlanetProperties,
    StarProperties,
    SpotProperties,
    FittingProperties,
)


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

        # Ensure the light curve file is accessible from the working directory
        fit = self.config.fitting_properties
        lc_path = Path(fit.data_filename)
        if not lc_path.is_absolute():
            # If a bare filename is provided and it does not exist in workdir,
            # try to source it from the repo sample/ directory.
            candidate = work / lc_path.name
            if not candidate.exists():
                repo_candidate = Path(__file__).resolve().parents[1] / "sample" / lc_path.name
                if repo_candidate.exists():
                    candidate.write_bytes(repo_candidate.read_bytes())

        # Assemble configuration text
        common = self.assemble_common()
        action = self.assemble_action()

        in_path = work / f"{self.input_basename()}.in"
        in_path.write_text(common + action)

        # Run stsp (assumes 'stsp' is available on PATH)
        try:
            subprocess.run(
                ["stsp", in_path.name],
                cwd=str(work),
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            rootname = str(in_path).rsplit(".in", 1)[0]
            err_path = Path(f"{rootname}_errstsp.txt")
            err_preview = None
            if err_path.exists():
                try:
                    with err_path.open("r") as f:
                        err_preview = "".join(f.readlines()[:40])
                except Exception:
                    err_preview = None
            msg = [
                f"stsp failed with exit code {e.returncode}",
                f"cmd: {' '.join(e.cmd) if isinstance(e.cmd, list) else e.cmd}",
            ]
            if e.stdout:
                msg.append("--- stdout ---\n" + e.stdout)
            if e.stderr:
                msg.append("--- stderr ---\n" + e.stderr)
            if err_preview:
                msg.append(f"--- {err_path.name} (first 40 lines) ---\n" + err_preview)
            raise RuntimeError("\n\n".join(msg))

        # Read outputs
        rootname = str(in_path).rsplit(".in", 1)[0]
        out_path = Path(f"{rootname}_lcout.txt")
        if not out_path.exists():
            # Provide helpful diagnostics when expected outputs are missing
            err_path = Path(f"{rootname}_errstsp.txt")
            msg = [f"Expected output not found: {out_path}"]
            if err_path.exists():
                try:
                    with err_path.open("r") as f:
                        err_preview = "".join(f.readlines()[:80])
                    msg.append(f"--- {err_path.name} (first 80 lines) ---\n{err_preview}")
                except Exception:
                    pass
            try:
                files = "\n".join(sorted(p.name for p in Path(work).iterdir()))
                msg.append(f"--- workdir listing ({work}) ---\n{files}")
            except Exception:
                pass
            raise FileNotFoundError("\n\n".join(msg))
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
    def __init__(self, config: STSPActionL) -> None:
        super().__init__(config)
        if len(config.spot_triplets) != config.spot_properties.num_spots:
            raise ValueError(
                f"Expected {config.spot_properties.num_spots} spot triplets, got {len(config.spot_triplets)}"
            )

    def input_basename(self) -> str:
        return f"{super().input_basename()}-l"

    def assemble_action(self) -> str:
        lines: List[str] = []
        lines.append("#ACTION\n")
        lines.append("l\n")
        for (r, th, ph) in self.config.spot_triplets:  # type: ignore[attr-defined]
            lines.append(f"{r}\n{th}\n{ph}\n")
        lines.append(f"{self.config.brightness_correction}\n")  # type: ignore[attr-defined]
        return "".join(lines)


class ActionMRunner(ActionRunner):
    def __init__(self, config: STSPActionM) -> None:
        super().__init__(config)
        seeded_fields = [
            config.sigma_radius,
            config.sigma_angle,
            config.seed_spot_triplets,
            config.seed_brightness_correction,
        ]
        any_seed = any(v is not None for v in seeded_fields)
        all_seed = (
            config.sigma_radius is not None
            and config.sigma_angle is not None
            and config.seed_spot_triplets is not None
            and config.seed_brightness_correction is not None
        )
        if any_seed and not all_seed:
            raise ValueError(
                "Seeded MCMC requires sigma_radius, sigma_angle, seed_spot_triplets, and seed_brightness_correction"
            )
        if all_seed:
            if len(config.seed_spot_triplets) != config.spot_properties.num_spots:  # type: ignore[arg-type]
                raise ValueError(
                    f"Expected {config.spot_properties.num_spots} seed spot triplets, got {len(config.seed_spot_triplets or [])}"
                )
        self._is_seeded = all_seed

    def input_basename(self) -> str:
        return f"{super().input_basename()}-{'s' if self._is_seeded else 'm'}"

    def assemble_action(self) -> str:
        c = self.config  # type: ignore[assignment]
        lines: List[str] = []
        lines.append("#ACTION\n")
        lines.append("s\n" if self._is_seeded else "m\n")
        # 5 basic MCMC params
        lines.append(f"{c.random_seed}\n")
        lines.append(f"{c.ascale}\n")
        lines.append(f"{c.num_chains}\n")
        lines.append(f"{c.steps_or_time}\n")
        lines.append(f"{c.calc_brightness_factor}\n")
        if self._is_seeded:
            lines.append(f"{c.sigma_radius}\n")
            lines.append(f"{c.sigma_angle}\n")
            for (r, th, ph) in c.seed_spot_triplets:  # type: ignore[union-attr]
                lines.append(f"{r}\n{th}\n{ph}\n")
            lines.append(f"{c.seed_brightness_correction}\n")
        return "".join(lines)
