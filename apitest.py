import pandas as pd
import streamlit as st
import pandas as pd
import os
import openpyxl

def upload_data():
    #select data to upload (ROGS, SHS, Airbnb, Waitlist - WA total, Waitlist - breakdowns, Images or links)
    select_data_to_upload = st.selectbox('Select what content to upload', ['ROGS', 'SHS', 'Airbnb', 'Waitlist - WA total', 'Waitlist - breakdowns', 'Images or links'])
    if select_data_to_upload == 'SHS':
        st.markdown(f'Please download Data Tables from <a href="https://www.aihw.gov.au/reports/homelessness-services/specialist-homelessness-services-monthly-data/data">=here</a> for uploading')
        SHSnew = st.file_uploader("Select downloaded file")
        if SHSnew is not None:
            source_file = pd.read_excel(SHSnew)
            import_shs_data(source_file)
    return


def delete_source_file(source_file):
    if os.path.exists(source_file):
        os.remove(source_file)
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

def get_SHS(source_file):
    xls = pd.ExcelFile(source_file)

    # Read all the sheets into a dictionary of DataFrames
    all_sheets = {sheet_name: pd.read_excel(xls, sheet_name, header=3) for sheet_name in xls.sheet_names}
    xls.close()

    #for each sheet in the dictionary
    for sheet_name, sheet in all_sheets.items():
        #check if has at least 100 rows
        if len(sheet) > 100:
            #drop last 2 rows
            sheet = sheet.drop(sheet.index[-2:])
            for col in sheet.columns:
                #if object
                if sheet[col].dtype == 'object':
                    sheet[col] = sheet[col].str.replace(chr(8211), "-").str.replace(chr(8212), "-")

            save_sheet_name = sheet_name.replace(' ', '_')
            sheet.to_csv('DATA/PROCESSED DATA/SHS/SHS_' + save_sheet_name + '.csv', index=False)
            all_sheets.update({sheet_name: sheet})

def find_csv_filenames(prefix, path_to_dir, suffix):
    filenames = os.listdir(path_to_dir)
    return [ filename for filename in filenames if filename.endswith( suffix ) and filename.startswith(prefix) ]

def convert_case(df):
    # Convert column names to uppercase
    df.columns = [col.upper() for col in df.columns]
    
    # Convert string values in all columns to uppercase
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].str.capitalize()

    return df

def identify_ignore_columns(dataframes_dict):
    ignore_columns = set()
    for _, df in dataframes_dict.items():
        for column in df.columns:
            if df[column].dtype in ['int64', 'float64']:
                ignore_columns.add(column)
            elif 'datetime64' in str(df[column].dtype):
                ignore_columns.add(column)
            elif column == 'MONTH':  # specifically ignore 'MONTH' column
                ignore_columns.add(column)
    return list(ignore_columns)

def load_and_preprocess_data(prefix, path_to_dir, suffix):
    # use find_csv_filenames function to find all csv files in Data/CSV/ with prefix 'SHS_' and suffix '.csv', read in
    filenames = find_csv_filenames(prefix, path_to_dir, suffix)
    processed_dataframes = {}

    # First, iterate over filenames to load the dataframes and store them in processed_dataframes
    for filename in filenames:
        df_name = filename.replace('.csv', '')
        df = pd.read_csv(path_to_dir + '/'+ filename)
        df = convert_case(df)

        # Drop any rows where specified columns are null / NaN
        cols_to_check = ['NSW','VIC','QLD','WA','SA','TAS','ACT','NT', 'NATIONAL']
        df = df.dropna(subset=cols_to_check)

        # Identify columns that should not be checked for NaN (those with numeric and datetime values)
        ignore_cols = identify_ignore_columns({df_name: df})

        # Columns to check for NaN (non-numeric columns)
        check_for_nan_cols = [col for col in df.columns if col not in ignore_cols]

        # Drop rows where columns (that aren't in ignore_cols) contain NaN values
        df = df.dropna(subset=check_for_nan_cols)
        #set AGE GROUP column to string, SEX to string

        if 'AGE GROUP' in df.columns:
            df['AGE GROUP'] = df['AGE GROUP'].str.replace(chr(45), "-").str.replace(chr(8211), "-")
            df['AGE GROUP'] = df['AGE GROUP'].astype(str)
            if 'All females' in df['AGE GROUP'].unique() or 'All males' in df['AGE GROUP'].unique():
                df = df[~df['AGE GROUP'].isin(['All females', 'All males'])]
                df['AGE GROUP'] = df['AGE GROUP'].str.replace(" years", "")

                #group 15-17 and 18-19 into 15-19
                df.loc[df['AGE GROUP'] == '15-17', 'AGE GROUP'] = '15-19'
                df.loc[df['AGE GROUP'] == '18-19', 'AGE GROUP'] = '15-19'
                #sum 15 to 19 numerical columns, retain datetime and object columns
                object_cols = [col for col in df.columns if df[col].dtype == 'object']
                datetime_cols = [col for col in df.columns if 'datetime64' in str(df[col].dtype)]
                numeric_cols = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
                df = df.groupby(object_cols + datetime_cols)[numeric_cols].sum().reset_index()
                
        # Convert Month column to a Date format
        if 'MONTH' in df.columns:
            df['DATE'] = '20' + df['MONTH'].str[3:5] + '-' + df['MONTH'].str[0:3] + '-01'
            df['DATE'] = pd.to_datetime(df['DATE'], format='%Y-%b-%d')
            df['DATE'] = df['DATE'] + pd.offsets.MonthEnd(0)
        
        # Sort dataframe by Date ascending
        df = df.sort_values(by='DATE', ascending=True)
        #CONVERT TO STRING %d/%m/%Y
        df['DATE'] = df['DATE'].dt.strftime('%d/%m/%Y')

        processed_dataframes[df_name] = df
    return processed_dataframes

def merge_and_calculate(processed_dataframes, Population_Sex_Age, Population_Sex, Population_Total):

    pop_dfs = ['Population_Sex_Age', 'Population_Sex', 'Population_Total']
    for pop_df in pop_dfs:
        globals()[pop_df] = convert_case(globals()[pop_df])
        globals()[pop_df]['DATE'] = pd.to_datetime(globals()[pop_df]['DATE'], format='%Y-%m-%d', dayfirst=True, errors='coerce')
        globals()[pop_df] = globals()[pop_df].set_index('DATE')
    Population_Sex_Age['AGE GROUP'] = Population_Sex_Age['AGE GROUP'].str.replace(chr(45), "-").str.replace(chr(8211), "-")

    regions = ['NSW', 'VIC', 'QLD', 'WA', 'SA', 'TAS', 'ACT', 'NT']
    SHS_with_population_calcs = {}

    for df_name, df in processed_dataframes.items():
        df['DATE'] = pd.to_datetime(df['DATE'], format='%d/%m/%Y', dayfirst=True)
        if 'AGE GROUP' in df.columns:
            df['JoinLeft'] = df['DATE'].astype(str) + ' ' + df['SEX'].astype(str) + ' ' + df['AGE GROUP'].astype(str)
            Population_Sex_Age['JoinRight'] = Population_Sex_Age['DATE'].astype(str) + ' ' + Population_Sex_Age['SEX'].astype(str) + ' ' + Population_Sex_Age['AGE GROUP'].astype(str)
            merged_df = pd.merge(df, Population_Sex_Age, left_on=['JoinLeft'], right_on=['JoinRight'], how='left')
            merged_df = merged_df.sort_values(by=['SEX_y', 'AGE GROUP_y', 'DATE_y'])
            
        else:
            if 'SEX' in df.columns:
                df['JoinLeft'] = df['DATE'].astype(str) + ' ' + df['SEX'].astype(str)
                Population_Sex['JoinRight'] = Population_Sex['DATE'].astype(str) + ' ' + Population_Sex['SEX'].astype(str)
                merged_df = pd.merge(df, Population_Sex, left_on=['JoinLeft'], right_on=['JoinRight'], how='left')
                merged_df = merged_df.sort_values(by=['SEX_y', 'DATE_y']) 
            else:
                merged_df = pd.merge(df, Population_Total, left_on=['DATE'], right_on=['DATE'], how='left')
                merged_df = merged_df.sort_values(by=['DATE_y'])
            
        pop_cols = [col for col in merged_df.columns if col.endswith('_POPULATION')]
        merged_df[pop_cols] = merged_df[pop_cols].ffill(axis=1)
        merged_df = merged_df.sort_values(by=['DATE_x'])
        merged_df = merged_df.fillna(method='ffill')
        merged_df = merged_df.drop(columns=['JoinLeft', 'JoinRight'])
        merged_df = merged_df.loc[:,~merged_df.columns.str.endswith('_y')]
        merged_df = merged_df.rename(columns=lambda x: x.replace('_x', '') if x.endswith('_x') else x)
        cols = list(merged_df.columns)
        cols.insert(0, cols.pop(cols.index('DATE')))
        merged_df = merged_df[cols]

        merged_df['NATIONAL_PER_10k'] = merged_df['NATIONAL'] / merged_df['NATIONAL_POPULATION'] * 10000
        for region in regions:
            population_column_name = f"{region}_POPULATION"
            per_10000_column = f"{region}_PER_10k"
            merged_df[per_10000_column] = merged_df[region] / merged_df[population_column_name] * 10000
            proportion_of_national_column = f"{region}_PROPORTION_OF_NATIONAL"
            merged_df[proportion_of_national_column] = (merged_df[region] / merged_df['NATIONAL']) * 100
            proportion_of_national_per_10000_column = f"{region}_PROPORTION_OF_NATIONAL_PER_10k"
            merged_df[proportion_of_national_per_10000_column] = (merged_df[per_10000_column] / merged_df['NATIONAL_PER_10k']) * 100
            prop_national_pop_column = f"{region}_PROPORTION_OF_NATIONAL_POPULATION"     
            merged_df[prop_national_pop_column] = (merged_df[population_column_name] / merged_df['NATIONAL_POPULATION']) * 100
            prop_compared_prop_pop = f"{region}_PROPORTION_OF_NATIONAL_COMPARED_TO_PROP_POP"
            merged_df[prop_compared_prop_pop] = (merged_df[proportion_of_national_column] / merged_df[prop_national_pop_column]) * 100
        numeric_cols = [col for col in merged_df.columns if merged_df[col].dtype in ['int64', 'float64']]
        merged_df[numeric_cols] = merged_df[numeric_cols].round(1)
        SHS_with_population_calcs[df_name] = merged_df
        merged_df.to_csv(f'DATA/PROCESSED DATA/SHS/WithPopulation/{df_name}_WithPopulation.csv', index=False)
    return SHS_with_population_calcs

def long_formSHS(SHS_with_population_calcs, source_file):
    long_form_dfs = {}
    latest_dates = []
    for df_name, df in SHS_with_population_calcs.items():
        id_vars = ['DATE'] + [col for col in df.columns if df[col].dtype == 'object']
        value_vars = [col for col in df.columns if df[col].dtype in ['int64', 'float64']]
        long_form_dfs[df_name] = pd.melt(df, id_vars=id_vars, value_vars=value_vars, var_name='MEASURE', value_name='VALUE')
        long_form_dfs[df_name]['MEASURE'] = long_form_dfs[df_name]['MEASURE'].str.replace('_', ' ')
        long_form_dfs[df_name]['MEASURE'] = long_form_dfs[df_name]['MEASURE'].str.lower()
        long_form_dfs[df_name]['MEASURE'] = long_form_dfs[df_name]['MEASURE'].str.capitalize()
        #create column State, which is measure before first space
        long_form_dfs[df_name]['STATE'] = long_form_dfs[df_name]['MEASURE'].str.split(' ').str[0]
        #create column Measure, which is remaining measure after moving State to its own column
        long_form_dfs[df_name]['MEASURE'] = long_form_dfs[df_name]['MEASURE'].str.split(' ').str[1:].str.join(' ')
        long_form_dfs[df_name]['STATE'] = long_form_dfs[df_name]['STATE'].str.replace('Wa', 'WA').str.replace('Nsw', 'NSW').str.replace('Sa', 'SA').str.replace('Nt', 'NT').str.replace('Act', 'ACT')
        #move State column to second column
        cols = list(long_form_dfs[df_name].columns)
        cols.insert(1, cols.pop(cols.index('STATE')))
        long_form_dfs[df_name] = long_form_dfs[df_name][cols]
        long_form_dfs[df_name].to_csv(f'DATA/PROCESSED DATA/SHS/Long_Form/{df_name}_Long_Form.csv', index=False)
        latest_date = df['DATE'].max()
        latest_date = pd.to_datetime(latest_date)
        latest_dates.append(latest_date)


    latest_date = max(latest_dates)
    latest_date = pd.to_datetime(latest_date)
    update_date = pd.to_datetime('today').strftime('%d/%m/%Y')
    update_log(latest_date, update_date, dataset)

    return 

def import_shs_data(source_file):
    path_to_dir = "DATA/PROCESSED DATA/SHS"
    prefix = 'SHS_'
    suffix = '.csv'
    dataset = 'Monthly SHS data from AIHW'
    Population_Sex_Age = pd.read_csv('DATA\PROCESSED DATA\Population\Population_State_Sex_Age_to_65+.csv')
    Population_Sex = pd.read_csv('DATA\PROCESSED DATA\Population\Population_State_Sex_Total.csv')
    Population_Total = pd.read_csv('DATA\PROCESSED DATA\Population\Population_State_Total_monthly.csv')
    try:
        get_SHS(source_file)
        processsed_dataframes = load_and_preprocess_data()
        SHS_with_population_calcs = merge_and_calculate(processsed_dataframes, Population_Sex_Age, Population_Sex, Population_Total)
        long_formSHS(SHS_with_population_calcs)
        delete_source_file(source_file)
    except:
        pass
    return

