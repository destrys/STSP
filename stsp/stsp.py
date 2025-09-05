from dataclasses import dataclass
from typing import List, Tuple


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


@dataclass
class STSPActionL(STSP):
    """STSP configuration for Action-l (generate light curve).

    Extends STSP by adding action-specific parameters.

    - spot_triplets: For each spot, radius, theta (radians), phi (radians).
    - brightness_correction: Brightness correction factor associated with this spot model.
    """

    spot_triplets: List[Tuple[float, float, float]]
    brightness_correction: float = 1.0
