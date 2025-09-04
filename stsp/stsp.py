from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PlanetProperties:
    """Orbital and transit properties for a single planet.

    - t0_epoch_days: Mid-transit epoch in days (prefer near 0).
    - period_days: Orbital period in days.
    - transit_depth: Transit depth (Rplanet/Rstar)^2
    - duration_days: Physical transit duration in days (not used).
    - impact_parameter: Impact parameter (0 = planet cross over equator, not used).
    - inclination_deg: Orbital inclination in degrees (90 = planet crosses over equator).
    - lambda_deg: Lambda of orbit (0 deg = orbital axis along z-axis) - angle between spin axis of star and orbital axis of planet
    - ecosw: (currently placeholders)
    - esinw: (currently placeholders)
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

    - mean_stellar_density: Stellar mean density (Msun/Rsun^3). (not used if nplanets = 0)
    - stellar_rotation_period_days: Stellar rotation period in days.
    - temperature_kelvin: stellar temperature (not used).
    - stellar_metallicity: Stellar metallicity (not used by core).
    - rotation_axis_tilt_deg: Tilt of the rotation axis of the star down from z-axis (degrees)
    - limb_darkening: Four limb darkening coefficients.
    - num_limb_darkening_rings: number of rings for limb-darkening approximation.
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

    - num_spots: Number of spots
    - fractional_brightness: fractional brightness (0.0= totally dark, 1.0=brightness of star)
    """

    num_spots: int
    fractional_brightness: float


@dataclass
class FittingProperties:
    """Description of the observed light curve segment to fit/generate.

    - data_filename: Light curve data file path.
    - start_time: Start time (days) to begin fitting the light curve.
    - light_curve_duration_days: Duration of the segment in days.
    - light_data_max: real maximum of light curve data (corrected for noise), 0 -> use downfrommax	
    - light_curve_flattened: If true, expected light curve is 0 outside transits.
    """

    data_filename: str
    start_time: float
    light_curve_duration_days: float
    light_data_max: float
    light_curve_flattened: bool


@dataclass
class STSP:
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
