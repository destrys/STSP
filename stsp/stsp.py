class PlanetProperties: pass
class StarProperties: pass
class SpotProperties: pass


class FittingProperties:
    def __init__(
        self,
        data_filename: str,
        start_time: float,
        light_curve_duration_days: int,
        light_data_max: float,
        light_curve_flattened: bool,
    ):
        """Description of Light Curve to Fit to

        Args:
            data_filename (str): 
                lightcurve data file
            start_time (float): 
                start time to start fitting the light curve
            light_curve_duration_days (int):
                druation of light curve to fit (days)
            light_data_max (float):
                real maximum of light curve data (corrected for
                noise). If this is set to zero, STSP uses simple down
                from max.
            light_curve_flattened (bool):
                If this is set to true, the expected light curve is
                set to zero outside transits.
        """
        data_filename: str,
        start_time: float,
        light_curve_duration_days: int,
        light_data_max: float,
        light_curve_flattened: bool,
        


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
