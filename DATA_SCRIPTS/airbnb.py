
import os
from os import listdir
import pandas as pd
import openpyxl

def delete_source_file(file):
    if os.path.exists(file):
        os.remove(file)
        return
    else:
        return

def update_log(latest_date, update_date, dataset):
    try:
        update_log = pd.read_excel('DATA/SOURCE DATA/update_log.xlsx')
    except:
        update_log = pd.DataFrame(columns=['Dataset', 'Latest data point', 'Date last updated'])
    new_row = pd.DataFrame({'Dataset': [dataset], 'Latest data point': [latest_date], 'Date last updated': [update_date]})
    update_log = pd.concat([update_log, new_row], ignore_index=True)
    update_log['Latest data point'] = pd.to_datetime(update_log['Latest data point'], format='%d/%m/%Y')
    update_log['Date last updated'] = pd.to_datetime(update_log['Date last updated'], format='%d/%m/%Y')
    update_log = update_log.sort_values(by=['Latest data point', 'Date last updated'], ascending=False).drop_duplicates(subset=['Dataset'], keep='first')
    #convert Latest data point and Date last updated to string
    update_log['Latest data point'] = update_log['Latest data point'].dt.strftime('%d/%m/%Y')
    update_log['Date last updated'] = update_log['Date last updated'].dt.strftime('%d/%m/%Y') 
    update_log.to_excel('DATA/SOURCE DATA/update_log.xlsx', index=False)
    book = openpyxl.load_workbook('DATA/SOURCE DATA/update_log.xlsx')
    sheet = book.active
    for column_cells in sheet.columns:
        length = max(len(as_text(cell.value)) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = length
    book.save('DATA/SOURCE DATA/update_log.xlsx')
    return

def as_text(value):
    if value is None:
        return ""
    return str(value)

def get_airbnb():
    filenames = listdir('DATA/SOURCE DATA/Market and economy/Airbnb')
    airbnb0 = 'DATA/PROCESSED DATA/Market and economy/airbnb_summary.csv'
    dfs = {}
    df_summaries = {}

    for filename in filenames:
        df_name = filename[:10]
        df = pd.read_csv('DATA/SOURCE DATA/Market and economy/Airbnb/' + filename)
        dfs[df_name] = df

    for df_name, df in dfs.items():
        df_summary_name = f"{df_name}_summary"
        #group by room_type, neighbourhood, column for count, calculate mean and median price, mean and median availability_365, store as row in df_summary
        df = df.groupby(['neighbourhood', 'room_type']).agg({'id': 'count', 'price': ['mean', 'median'], 'availability_365': ['mean', 'median']})
        #rename 2 level column names - price mean to mean_price, price median to median_price, availability_365 mean to mean_availability_365, availability_365 median to median_availability_365
        df.columns = ['_'.join(col) for col in df.columns]
        #col1 name = neighbourhood, col2 name = room_type, col3 name = count
        df = df.reset_index()
        #rename count column to count_listings
        df = df.rename(columns={'id_count': 'count_listings'})
        #add column for date
        df['date'] = df_name
        #add df to df_summary
        df_summaries[df_summary_name] = df

    #concatenate all df_summary_name dfs in df_summaries
    df_summary = pd.concat(df_summaries.values())


    latest_date = df_summary['date'].max()
    latest_date = pd.to_datetime(latest_date).strftime('%d/%m/%Y')
    
    #try read csv airbnb0, concatenate df_summary to airbnb0, save as airbnb_summary.csv
    try:
        airbnb0 = pd.read_csv('DATA/PROCESSED DATA/Market and economy/airbnb_summary.csv')
        airbnb0 = pd.concat([airbnb0, df_summary])
        #drop duplicates
        airbnb0 = airbnb0.drop_duplicates()
        airbnb0.to_csv('DATA/PROCESSED DATA/Market and economy/airbnb_summary.csv', index=False)
        update_log(latest_date, pd.to_datetime('today'), 'Airbnb')
        for filename in filenames:
            delete_source_file('DATA/SOURCE DATA/Market and economy/Airbnb/' + filename)
    except:
        df_summary.to_csv('DATA/PROCESSED DATA/Market and economy/airbnb_summary.csv', index=False)
        update_log(latest_date, pd.to_datetime('today'), 'Airbnb')
        for filename in filenames:
            delete_source_file('DATA/SOURCE DATA/Market and economy/Airbnb/' + filename)
    return


def state_total():
    filenames = listdir('DATA/SOURCE DATA/Summary')
    dfs = {}
    df_summaries = {}

    for filename in filenames:
        df_name = filename[:10]
        df = pd.read_csv('DATA/SOURCE DATA/Summary/' + filename)
        df['date'] = df_name
        dfs[df_name] = df
        all_details = pd.concat(dfs.values())
    for df_name, df in dfs.items():
        df_summary_name = f"{df_name}_summary"
        #group by room_type, neighbourhood, column for count, calculate mean and median price, mean and median availability_365, store as row in df_summary
        df = df.groupby(['room_type']).agg({'id': 'count', 'price': ['mean', 'median'], 'availability_365': ['mean', 'median']})
        #rename 2 level column names - price mean to mean_price, price median to median_price, availability_365 mean to mean_availability_365, availability_365 median to median_availability_365
        df.columns = ['_'.join(col) for col in df.columns]
        #col1 name = neighbourhood, col2 name = room_type, col3 name = count
        df = df.reset_index()
        #rename count column to count_listings
        df = df.rename(columns={'id_count': 'count_listings'})
        #add column for date
        df['date'] = df_name
        #add df to df_summary
        df_summaries[df_summary_name] = df
    df_summary_wa = pd.concat(df_summaries.values())
    
    df_summary_wa.to_csv('DATA/PROCESSED DATA/Market and economy/Airbnb_WAtotals.csv', index=False)
    all_details.to_csv('DATA/PROCESSED DATA/Market and economy/Airbnb_full.csv', index=False)
    return

def locs():
    df = pd.read_csv('DATA/PROCESSED DATA/Market and economy/airbnb_summary.csv')
    locs = pd.read_csv('DATA/Data descriptions/australian_postcodes.csv')
    #filter locs to WA
    locs = locs[locs['state'] == 'WA']
    #drop any sa4name = Northern Territory - Outback
    locs = locs[locs['sa4name'] != 'Northern Territory - Outback']
    #drop locs columns id, dc, type, state, status, sa3, sa4, region, SA1_MAINCODE_2011,	SA1_MAINCODE_2016,	SA2_MAINCODE_2016, SA3_CODE_2016, SA4_CODE_2016,	RA_2011	RA_2016	MMM_2015	MMM_2019	ced	altitude	chargezone	phn_code	phn_name
    locs = locs.drop(columns=['id', 'dc', 'type', 'state', 'status', 'sa3', 'sa4', 'sa3name', 'sa4name', 'region', 'SA1_MAINCODE_2011',	'SA1_MAINCODE_2016',	'SA2_MAINCODE_2016', 'SA3_CODE_2016', 'SA4_CODE_2016',	'RA_2011',	'RA_2016',	'MMM_2015',	'MMM_2019',	'altitude',	'chargezone',	'phn_code', 'long', 'lat', 'Lat_precise', 'Long_precise'])
    map = pd.read_csv('DATA/PROCESSED DATA/Market and economy/Airbnb_map.csv')
    map_old = map['old'].unique()


    df_full = pd.read_csv('DATA/PROCESSED DATA/Market and economy/Airbnb_full.csv')
    if df_full['neighbourhood'].isin(map_old).any():
        df_full['neighbourhood'] = df_full['neighbourhood'].replace(map_old, map['new'])

    #merge df_full neighbourhood & locs locality
    df_full = pd.merge(df_full, locs, left_on='neighbourhood', right_on='locality', how='left')
    #drop columns name, host_name, neighbourhood_group, latitude, longitude, last_review, reviews_per_month, number_of_reviews, number_of_reviews_ltm, 'license'

    if df['neighbourhood'].isin(map_old).any():
        df['neighbourhood'] = df['neighbourhood'].replace(map_old, map['new'])
    df = pd.merge(df, locs, left_on='neighbourhood', right_on='locality', how='left')

    df_full.to_csv('DATA/PROCESSED DATA/Market and economy/Airbnb_full.csv', index=False)
    df.to_csv('DATA/PROCESSED DATA/Market and economy/airbnb_summary.csv', index=False)
    return

def full_clean():
    df = pd.read_csv('DATA/PROCESSED DATA/Market and economy/Airbnb_full.csv')
    df = df.drop(columns=['name', 'host_name', 'neighbourhood_group', 'latitude', 'longitude', 'last_review', 'reviews_per_month', 'number_of_reviews', 'number_of_reviews_ltm', 'license'])

    try:
        df = df.rename(columns={'postcode_y': 'postcode', 'locality_y': 'locality', 'SA2_NAME_2016_y': 'SA2_NAME_2016', 'SA3_NAME_2016_y': 'SA3_NAME_2016', 'SA4_NAME_2016_y': 'SA4_NAME_2016', 'ced_y': 'ced', 'phn_name_y': 'phn_name', 'lgaregion_y': 'lgaregion', 'lgacode_y': 'lgacode', 'electorate_y': 'electorate', 'electoraterating_y': 'electoraterating'})
    except:
        pass

    df_allgeo = df.groupby(['date', 'room_type', 'SA2_NAME_2016', 'SA3_NAME_2016', 'SA4_NAME_2016', 'ced', 'lgaregion', 'lgacode', 'electorate', 'electoraterating']).agg({'id': 'count', 'price': ['mean', 'median'], 'availability_365': ['mean', 'median']})
    df_allgeo.columns = ['_'.join(col) for col in df_allgeo.columns]
    df_allgeo = df_allgeo.reset_index()

    df_allgeo.to_csv('DATA/PROCESSED DATA/Market and economy/Airbnb_allgeo.csv', index=False)
    return

full_clean()






