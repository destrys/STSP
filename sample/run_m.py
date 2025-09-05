#!/usr/bin/env python3
from pathlib import Path
from stsp import ActionM, PlanetProperties, StarProperties, SpotProperties, FittingProperties
from stsp.runner import ActionMRunner


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
    cfg = ActionM(
        planets=planets,
        star_properties=star,
        spot_properties=spots,
        fitting_properties=fit,
        random_seed=74384338,
        ascale=1.25,
        num_chains=40,
        steps_or_time=5000,
        calc_brightness_factor=1,
    )
    runner = ActionMRunner(cfg)
    workdir, arr, final_path = runner.run(workdir=here)
    print(f"Wrote: {here/'pyact-m.in'}")
    print(f"Wrote: {final_path}")


if __name__ == "__main__":
    main()
