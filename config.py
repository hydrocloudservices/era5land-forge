from datetime import datetime, timedelta


class Config(object):

    # Bucket configuration
    BUCKET = 's3://era5-atlantic-northeast/netcdf/land/day'
    CLIENT_KWARGS = {'endpoint_url': 'https://s3.us-east-2.wasabisys.com',
                     'region_name': 'us-east-2'}
    CONFIG_KWARGS = {'max_pool_connections': 30}
    PROFILE = 'default'

    STORAGE_OPTIONS = {'profile': PROFILE,
                       'client_kwargs': CLIENT_KWARGS,
                       'config_kwargs': CONFIG_KWARGS
                       }

    # Dataset
    START_DATE = "2000-01-01"
    END_DATE = (datetime.utcnow() - timedelta(days=120)).strftime('%Y-%m-%d')

    VARIABLES = {
        '2m_dewpoint_temperature': 'd2m',
        '2m_temperature': 't2m',
        '10m_u_component_of_wind': 'u10',
        '10m_v_component_of_wind': 'v10',
        'evaporation_from_bare_soil': 'evabs',
        'evaporation_from_open_water_surfaces_excluding_oceans': 'evaow',
        'evaporation_from_vegetation_transpiration': 'evavt',
        'evaporation_from_the_top_of_canopy': 'evatc',
        'total_evaporation': 'e',
        'lake_ice_depth': 'licd',
        'potential_evaporation': 'pev',
        'skin_temperature': 'skt',
        'snow_cover': 'snowc',
        'snow_depth_water_equivalent': 'sd',
        'snow_density': 'rsn',
        'snow_depth': 'sde',
        'snow_evaporation': 'es',
        'snowfall': 'sf',
        'snowmelt': 'smlt',
        'surface_net_solar_radiation': 'ssr',
        'surface_runoff': 'sro',
        'sub_surface_runoff': 'ssro',
        'temperature_of_snow_layer': 'tsn',
        'total_precipitation': 'tp',
        'volumetric_soil_water_layer_1': 'swvl1',
        'volumetric_soil_water_layer_2': 'swvl2',
        'volumetric_soil_water_layer_3': 'swvl3',
        'volumetric_soil_water_layer_4': 'swvl4'
    }

    TIMES = ['00:00', '01:00', '02:00',
             '03:00', '04:00', '05:00',
             '06:00', '07:00', '08:00',
             '09:00', '10:00', '11:00',
             '12:00', '13:00', '14:00',
             '15:00', '16:00', '17:00',
             '18:00', '19:00', '20:00',
             '21:00', '22:00', '23:00'
             ]
