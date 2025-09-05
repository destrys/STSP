from dataclasses import dataclass
from typing import List, Tuple
from pathlib import Path


@dataclass
class PlanetProperties:
    """Orbital and transit properties for a single planet.

    - t0_epoch_days: T0, time of the middle of first transit in days  (Better if this number is closer to zero)
    - period_days: Planet Period      (days)
    - transit_depth: Depth of transit (Rp/Rs)^2         (Rplanet/Rstar)^2
    - duration_days: Duration (days) of transit   (physical duration of transit, not used)
    - impact_parameter: Impact parameter  (0= planet cross over equator, use inclination angle instead)
    - inclination_deg: Inclination angle of orbit (90 deg = planet crosses over equator)
    - lambda_deg: Lambda of orbit (0 deg = orbital axis along z-axis) - angle between spin axis of star and orbital axis of planet
    - ecosw: ecosw
    - esinw: esinw
    """

    t0_epoch_days: float
    period_days: float
    transit_depth: float
    duration_days: float
    impact_parameter: float
    inclination_deg: float
    lambda_deg: float
    ecosw: float
    esinw: float


@dataclass
class StarProperties:
    """Star properties.

    - mean_stellar_density: Mean Stellar density (Msun/Rsun^3)  (related to a/Rstar)
    - stellar_rotation_period_days: Stellar Rotation period (days)
    - temperature_kelvin: Stellar Temperature  (not used)
    - stellar_metallicity: Stellar metallicity  (not used)
    - rotation_axis_tilt_deg: Tilt of the rotation axis of the star down from z-axis (degrees)
    - limb_darkening: Limb darkening (4 coefficients)
    - num_limb_darkening_rings: number of rings for limb darkening approximation
    """

    mean_stellar_density: float
    stellar_rotation_period_days: float
    temperature_kelvin: float
    stellar_metallicity: float
    rotation_axis_tilt_deg: float
    limb_darkening: Tuple[float, float, float, float]
    num_limb_darkening_rings: int


@dataclass
class SpotProperties:
    """Global spot configuration parameters.

    - num_spots: number of spots
    - fractional_brightness: fractional brightness of spots (0.0= totally dark, 1.0=brightness of star)
    """

    num_spots: int
    fractional_brightness: float


@dataclass
class FittingProperties:
    """Description of the observed light curve segment to fit/generate.

    - data_filename: lightcurve data file
    - start_time: start time to start fitting the light curve
    - light_curve_duration_days: duration of light curve to fit (days)
    - light_data_max: real maximum of light curve data (corrected for noise), 0 -> STSP uses simple downfrommax
    - light_curve_flattened: is light curve flattened (to zero) outside of transits?
    """

    data_filename: str
    start_time: float
    light_curve_duration_days: float
    light_data_max: float
    light_curve_flattened: bool


@dataclass
class Action:
    """Top-level STSP configuration container.

    - planets: List of planet property objects
    - star_properties: star properties
    - spot_properties: spot configuration
    - fitting_properties: description of light curve data to fit or generate
    """

    planets: List[PlanetProperties]
    star_properties: StarProperties
    spot_properties: SpotProperties
    fitting_properties: FittingProperties


@dataclass
class ActionL(Action):
    """STSP configuration for Action-l (generate light curve).

    Extends STSP by adding action-specific parameters.

    - spot_triplets: For each spot, radius, theta (radians), phi (radians).
    - brightness_correction: Brightness correction factor associated with this spot model.
    """

    spot_triplets: List[Tuple[float, float, float]]
    brightness_correction: float = 1.0


@dataclass
class ActionM(Action):
    """STSP configuration for affine-invariant MCMC (Action-m/s).

    Unseeded (Action-m): provide the 5 MCMC parameters below and leave the
    seeded options as None. Seeded (Action-s): also provide `sigma_radius`,
    `sigma_angle`, and a single set of spot parameters for all spots.

    - random_seed: Random seed.
    - ascale: MCMC a scale parameter.
    - num_chains: Number of chains (population size).
    - steps_or_time: Number of steps (or time if negative; see C code).
    - calc_brightness_factor: 0 = use downfrommax, 1 = calculate brightness factor.
    - sigma_radius: Optional; required for seeded runs (Action-s).
    - sigma_angle: Optional; required for seeded runs (Action-s).
    - seed_spot_triplets: Optional spot (r, theta, phi) for each spot (Action-s).
    - seed_brightness_correction: Optional brightness factor paired with seeds.
    """

    random_seed: int
    ascale: float
    num_chains: int
    steps_or_time: int
    calc_brightness_factor: int

    sigma_radius: float | None = None
    sigma_angle: float | None = None
    seed_spot_triplets: List[Tuple[float, float, float]] | None = None
    seed_brightness_correction: float | None = None


# --- Serialization helpers ---

def _line(val) -> str:
    return f"{val}\n"


def serialize_common(action: Action) -> str:
    lines: List[str] = []
    # PLANET PROPERTIES
    lines.append("#PLANET PROPERTIES\n")
    lines.append(_line(len(action.planets)))
    for p in action.planets:
        lines.append(_line(p.t0_epoch_days))
        lines.append(_line(p.period_days))
        lines.append(_line(p.transit_depth))
        lines.append(_line(p.duration_days))
        lines.append(_line(p.impact_parameter))
        lines.append(_line(p.inclination_deg))
        lines.append(_line(p.lambda_deg))
        lines.append(_line(p.ecosw))
        lines.append(_line(p.esinw))

    # STAR PROPERTIES
    s = action.star_properties
    lines.append("#STAR PROPERTIES\n")
    lines.append(_line(s.mean_stellar_density))
    lines.append(_line(s.stellar_rotation_period_days))
    lines.append(_line(s.temperature_kelvin))
    lines.append(_line(s.stellar_metallicity))
    lines.append(_line(s.rotation_axis_tilt_deg))
    lines.append(f"{s.limb_darkening[0]} {s.limb_darkening[1]} {s.limb_darkening[2]} {s.limb_darkening[3]}\n")
    lines.append(_line(s.num_limb_darkening_rings))

    # SPOT PROPERTIES
    sp = action.spot_properties
    lines.append("#SPOT PROPERTIES\n")
    lines.append(_line(sp.num_spots))
    lines.append(_line(sp.fractional_brightness))

    # LIGHT CURVE
    f = action.fitting_properties
    lines.append("#LIGHT CURVE\n")
    lines.append(_line(f.data_filename))
    lines.append(_line(f.start_time))
    lines.append(_line(f.light_curve_duration_days))
    lines.append(_line(f.light_data_max))
    lines.append(_line(1 if f.light_curve_flattened else 0))

    return "".join(lines)


def serialize_action_l(action: ActionL) -> str:
    lines: List[str] = ["#ACTION\n", "l\n"]
    for (r, th, ph) in action.spot_triplets:
        lines.append(_line(r))
        lines.append(_line(th))
        lines.append(_line(ph))
    lines.append(_line(action.brightness_correction))
    return "".join(lines)


def serialize_action_m(action: ActionM) -> str:
    seeded = (
        action.sigma_radius is not None
        and action.sigma_angle is not None
        and action.seed_spot_triplets is not None
        and action.seed_brightness_correction is not None
    )
    lines: List[str] = ["#ACTION\n", ("s\n" if seeded else "m\n")]
    lines.append(_line(action.random_seed))
    lines.append(_line(action.ascale))
    lines.append(_line(action.num_chains))
    lines.append(_line(action.steps_or_time))
    lines.append(_line(action.calc_brightness_factor))
    if seeded:
        lines.append(_line(action.sigma_radius))
        lines.append(_line(action.sigma_angle))
        for (r, th, ph) in action.seed_spot_triplets:  # type: ignore[misc]
            lines.append(_line(r))
            lines.append(_line(th))
            lines.append(_line(ph))
        lines.append(_line(action.seed_brightness_correction))
    return "".join(lines)


def expected_output_suffix(action: Action) -> str:
    if isinstance(action, ActionL):
        return "_lcout.txt"
    if isinstance(action, ActionM):
        return "_finalparam.txt"
    # Default to err to force early failure if not overridden
    return "_out.txt"
