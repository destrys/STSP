#!/usr/bin/env python3
from pathlib import Path
from stsp import ActionM, PlanetProperties, StarProperties, SpotProperties, FittingProperties
from stsp.runner import ActionMRunner
import numpy as np


def main() -> None:
    here = Path(__file__).resolve().parent
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
    seed_spots = [
        (0.382525700680, 2.026108848159, 0.744618637426),
        (0.290572978656, 1.727405120396, 1.570800631939),
        (0.301035942796, 1.315591006119, 2.163399563938),
        (0.213239119426, 1.844123549292, 3.372735964458),
        (0.292627124386, 1.100571758314, 4.248530337143),
        (0.300349989200, 1.963252856264, 5.492592578403),
    ]
    cfg = ActionM(
        planets=planets,
        star_properties=star,
        spot_properties=spots,
        fitting_properties=fit,
        random_seed=74384338,
        ascale=1.25,
        num_chains=2,
        steps_or_time=100,
        calc_brightness_factor=1,
        sigma_radius=0.01,
        sigma_angle=0.1,
        seed_spot_triplets=seed_spots,
        seed_brightness_correction=1.0,
    )
    runner = ActionMRunner(cfg)
    arr = runner.run(workdir=here)
    copy_path = here / 'pyact-s-finalparam-copy.txt'
    np.savetxt(copy_path, arr, fmt='%.17g')
    print(f"Wrote: {here/'pyact-s.in'}")
    print(f"Wrote: {here/'pyact-s_finalparam.txt'}")
    print(f"Wrote: {copy_path}")


if __name__ == "__main__":
    main()
