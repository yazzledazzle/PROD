import pandas as pd
from os import listdir

path_to_dir = 'DATA/PROCESSED DATA/Census/Multiyear'
description_file = 'DATA/Data descriptions/Census/census_file_details.csv'

def find_csv_filenames(path_to_dir, suffix='.csv'):
    filenames = listdir(path_to_dir)
    return [filename for filename in filenames if filename.endswith( suffix )]

def get_data(path_to_dir, filenames, description_file):
    dataframes, homeless_data, total_data, objects_dict, numeric_dict, description = {}, {}, {}, {}, {}, {}
    description_df = pd.read_csv(description_file)
    for filename in filenames:
        key = filename.replace('_1621.csv', '')
        df = pd.read_csv(path_to_dir + '/' + filename)
        df['CENSUS_YEAR'] = df['CENSUS_YEAR'].astype('object')
        dataframes[key] = df
        homeless_data[key] = df.drop(columns=['TOTAL', 'NOT APPLICABLE'])
    for key in dataframes:
        objects = []
        numerics = []
        for column in dataframes[key].columns:
            if column in ['TOTAL', 'NOT APPLICABLE', 'CENSUS_YEAR']:
                continue
            elif dataframes[key][column].dtype == 'object':
                objects.append(column)

            elif dataframes[key][column].dtype in ['int64', 'float64']:
                numerics.append(column)
        objects_dict[key] = objects
        numeric_dict[key] = numerics
        description[description_df[description_df['FILE_NAME'] == key]['FILE_DESCRIPTION1'].values[0]] = key
        total_data[key] = dataframes[key].drop(columns=numerics)
    return dataframes, homeless_data, total_data, objects_dict, numeric_dict, description    
    
