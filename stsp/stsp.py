from dataclasses import dataclass
from typing import Tuple


@dataclass
class PlanetProperties:
    """Orbital and transit properties for a single planet.

    Fields mirror the PLANET PROPERTIES section of the README input format.

    - num_planets: Number of planets (repeat block if >1).
    - t0_epoch_days: Mid-transit epoch in days (prefer near 0).
    - period_days: Orbital period in days.
    - transit_depth: Transit depth (Rp/Rs)^2.
    - duration_days: Physical transit duration in days (not used by core).
    - impact_parameter: Impact parameter b (0 = equator crossing).
    - inclination_deg: Orbital inclination in degrees (90 = equator crossing).
    - lambda_deg: Sky-projected spin–orbit angle in degrees.
    - ecosw: E*cos(omega) for eccentric orbits.
    - esinw: E*sin(omega) for eccentric orbits.
    """

    num_planets: int
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
    """Stellar and limb-darkening properties.

    Fields mirror the STAR PROPERTIES section of the README input format.

    - mean_density_msun_per_rsun3: Stellar mean density (Msun/Rsun^3).
    - rotation_period_days: Stellar rotation period in days.
    - temperature_kelvin: Effective temperature (not used by core).
    - metallicity: Stellar metallicity (not used by core).
    - rotation_axis_tilt_deg: Tilt down from z-axis (degrees).
    - limb_darkening: Four limb darkening coefficients.
    - num_limb_darkening_rings: Rings used for limb-darkening approximation.
    """

    mean_density_msun_per_rsun3: float
    rotation_period_days: float
    temperature_kelvin: float
    metallicity: float
    rotation_axis_tilt_deg: float
    limb_darkening: Tuple[float, float, float, float]
    num_limb_darkening_rings: int


@dataclass
class SpotProperties:
    """Global spot configuration parameters.

    Mirrors the SPOT PROPERTIES section of the README input format.

    - num_spots: Number of circular spots on the stellar surface.
    - fractional_lightness: Fractional lightness relative to photosphere
      (0.0 = dark, 1.0 = same brightness, >1.0 = bright spots/faculae).
    """

    num_spots: int
    fractional_lightness: float


@dataclass
class FittingProperties:
    """Description of the observed light curve segment to fit/generate.

    Mirrors the FITTING/"LIGHT CURVE" section of the README input format.

    - data_filename: Light curve data file path.
    - start_time: Start time (days) to begin fitting the light curve.
    - light_curve_duration_days: Duration of the segment in days.
    - light_data_max: Real maximum of light curve (set 0 to use downfrommax).
    - light_curve_flattened: If true, expected light curve is 0 outside transits.
    """

    data_filename: str
    start_time: float
    light_curve_duration_days: float
    light_data_max: float
    light_curve_flattened: bool


class STSP:
    def __init__(
        self,
        planet_properties: PlanetProperties,
        star_properties: StarProperties,
        spot_properties: SpotProperties,
        fitting_properties: FittingProperties,
    ):
        self.planet_properties = planet_properties
        self.star_properties = star_properties
        self.spot_properties = spot_properties
        self.fitting_properties = fitting_properties
