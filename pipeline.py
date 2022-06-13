import xarray as xr
import cdsapi
from prefect import task, Flow, case, agent
from datetime import datetime, timedelta
import os
import fsspec
import s3fs
import pandas as pd
import itertools
import numpy as np
from itertools import product
import glob
from config import Config


def fetch_era5(date, variables_long_name):
    c = cdsapi.Client()

    name = 'reanalysis-era5-land'

    request = {'format': 'grib',
               'variable': variables_long_name,
               'area': [63, -96, 40, -52],  # North, West, South, East. Default: global,
               'year': "{:04d}".format(date.year),
               'month': "{:02d}".format(date.month),
               'day': "{:02d}".format(date.day),
               'time': Config.TIMES
               }

    r = c.retrieve(name,
                   request,
                   'tmp.grib2')

@task()
def list_available_data_not_in_bucket():

    """
    Determines list of all possible unique single variable daily files from a list of dates.
    It then compares if those files exist in the bucket (Config.BUCKET)

    :return: Matrix with dates and variables to extract
    """
    fs = fsspec.filesystem('s3', **Config.STORAGE_OPTIONS)

    short_name_variables: list = list(Config.VARIABLES.values())
    date_range: list = pd.date_range(start=Config.START_DATE,
                                     end=Config.END_DATE) \
        .strftime('%Y%m%d')

    all_combinations_filenames: list = ['{}_{}_ERA5_LAND_REANALYSIS.nc'.format(date, variable.upper()) for
                                        date, variable in product(date_range, short_name_variables)]
    current_filenames_in_bucket: list = [os.path.basename(filename)
                                         for filename in fs.ls(Config.BUCKET)[1:]]
    missing_filenames_in_bucket: list = list(set(all_combinations_filenames) \
                                             .difference(set(current_filenames_in_bucket)))

    return pd.DataFrame(data=[tuple(filename.split('_')[0:2]) for filename in missing_filenames_in_bucket],
                        columns=['Date', 'Var']).groupby(['Date'])['Var'] \
        .unique() \
        .reset_index() \
        .values


@task(max_retries=5, retry_delay=timedelta(minutes=5))
def save_unique_variable_date_file(dates_vars):

    fs = fsspec.filesystem('s3', **Config.STORAGE_OPTIONS)

    chosen_date_str, variables = dates_vars

    chosen_date = datetime.strptime(chosen_date_str, '%Y%m%d')
    variables_long_name: list = [var_long_name
                                 for var_long_name, var_short_name in Config.VARIABLES.items()
                                 if var_short_name in list(map(lambda x: x.lower(), variables))]
    print(chosen_date)
    # # add case when return no data
    fetch_era5(chosen_date, variables_long_name)

    import cfgrib

    ds_list = cfgrib.open_datasets('tmp.grib2')

    for ds in ds_list:
        print(ds.valid_time)
        # ds = ds.squeeze()

        if 'step' in list(ds.dims):
            if any(ds.time.shape) == True:
                ds = ds.stack(z=('time', 'step')).reset_index('z')
                # ds['z'] = ds.time + ds.step.fillna(0)
                ds['z'] = (ds.time + ds.step.fillna(0)).values.reshape(-1)
                cleaned_list = [x for x in list(ds.coords.keys()) if x not in ['latitude', 'longitude', 'z']]
                ds = ds.drop(cleaned_list) \
                    .dropna('z', how='all') \
                    .rename({'z': 'time'})
            else:
                ds['step'] = (ds.time + ds.step.fillna(0)).values.reshape(-1)
                cleaned_list = [x for x in list(ds.coords.keys()) if x not in ['latitude', 'longitude', 'step']]
                ds = ds.drop(cleaned_list) \
                    .dropna('step', how='all') \
                    .rename({'step': 'time'})
        else:
            cleaned_list = [x for x in list(ds.coords.keys()) if x not in ['latitude', 'longitude', 'time']]
            ds = ds \
                .drop(cleaned_list)

        if 'expver' in list(ds.dims):
            ds = ds.reduce(np.nansum, 'expver')

        for var in list(ds.keys()):
            filename = "{:04d}{:02d}{:02d}_{}_ERA5_LAND_REANALYSIS.nc".format(chosen_date.year,
                                                                              chosen_date.month,
                                                                              chosen_date.day,
                                                                              var.upper())
            ds[var.lower()].to_netcdf(filename)
            print(filename)
            fs.put(filename,
                   os.path.join(Config.BUCKET,
                                filename))
            os.remove(filename)
    os.remove('tmp.grib2')
    for f in glob.glob("tmp*.idx"):
        os.remove(f)


if __name__ == '__main__':

    with Flow("ERA5-ETL") as flow:
        dates_vars: np.array = list_available_data_not_in_bucket()
        save_unique_variable_date_file.map(dates_vars)

    flow.run()
