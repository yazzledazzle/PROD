def Waitlist_load_data(source_file):
    new_waitlist = pd.read_excel(source_file)
    current = pd.read_csv(Waitlist_trend_longdf)
    df = pd.concat([current, new_waitlist])
    df = df.drop_duplicates()
    return df

def Waitlist_clear_new_data(source_file):
    wb = load_workbook(source_file)
    ws = wb.active
    ws.delete_rows(2, ws.max_row)
    wb.save(source_file)
    return

def Waitlist_convert_to_long_form(df):
    df_long = df.melt(id_vars=["Date"], 
                      var_name="Category", 
                      value_name="Number")
    df_long['Date'] = pd.to_datetime(df_long['Date'], dayfirst=True)
    df_long = df_long.sort_values(['Category', 'Date'], ascending=[True, True])
    df_long = df_long.dropna(subset=['Number'])
    return df_long

def Waitlist_gap_filler(df_long):
    missing_dates = []
    Category_dfs = []
    for Category in df_long['Category'].unique():
        Category_df = df_long[df_long['Category'] == Category].copy()
        for i in range(len(Category_df)-1):
            if Category_df['Date'].iloc[i] + pd.DateOffset(days=1) + pd.offsets.MonthEnd(0) != Category_df['Date'].iloc[i+1]:    
                gap = round((Category_df['Date'].iloc[i+1] - Category_df['Date'].iloc[i]).days / 30) - 1
                diff = Category_df['Number'].iloc[i+1] - Category_df['Number'].iloc[i]
                for j in range(gap):
                    missing_date = Category_df['Date'].iloc[i] + pd.DateOffset(days=1) + pd.offsets.MonthEnd(0)
                    proxy_value = round(Category_df['Number'].iloc[i] + (diff / (gap+1)))
                    missing_dates.append(missing_date)
                    new_row = {'Date': missing_date, 'Category': Category, 'Number': proxy_value, 'Estimate flag - Number': 'Y'}
                    Category_df = pd.concat([Category_df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
        Category_dfs.append(Category_df)
    df_long = pd.concat(Category_dfs)
    df_long = df_long.sort_values(by=['Date'])
    df_long = df_long.reset_index(drop=True)
    df_long['Estimate flag - Number'] = df_long['Estimate flag - Number'].fillna('')
    df_long['Estimate flag - Number'] = df_long['Estimate flag - Number'].astype(str)
    df_long['Date'] = pd.to_datetime(df_long['Date'])
    df_long['Category'] = df_long['Category'].astype(str)
    df_long['Number'] = df_long['Number'].astype(float)
    return df_long

def Waitlist_FYtdchange(df_long):
    for Category in df_long['Category'].unique():
        
        df_long_Category = df_long[df_long['Category'] == Category].copy()
        for i, row in df_long_Category.iterrows():
            if row['Date'].month > 6:
                eofy = str(row['Date'].year) + "-06-30"
            else:
                eofy = str((row['Date'].year)-1) + "-06-30"
            eofy = pd.to_datetime(eofy, format='%Y-%m-%d')
            if eofy in df_long_Category['Date'].values:
                df_long_Category.loc[i, 'Difference - financial year to date'] = row['Number'] - df_long_Category.loc[df_long_Category['Date']==eofy, 'Number'].values[0]
                df_long_Category.loc[i, 'Difference - financial year to date (per cent)'] = df_long_Category.loc[i, 'Difference - financial year to date'] / df_long_Category.loc[df_long_Category['Date']==eofy, 'Number'].values[0] * 100 
            else:
                df_long_Category.loc[i, 'Difference - financial year to date'] = float('nan')
                df_long_Category.loc[i, 'Difference - financial year to date (per cent)'] = float('nan')
        df_long = df_long.drop(df_long[df_long['Category'] == Category].index)
        df_long = pd.concat([df_long, df_long_Category])
    return df_long

def Waitlist_month_diff(df_long):
    df_long['Estimate flag - prior month'] = ''
    for Category in df_long['Category'].unique():
        df_long_Category = df_long[df_long['Category'] == Category].copy()
        df_long_Category['helper'] = df_long_Category['Date'] - pd.offsets.MonthEnd(1)
        df_long_Category['helper2'] = df_long_Category['helper'].apply(lambda x: df_long_Category.loc[df_long_Category['Date']==x, 'Number'].values[0] if x in df_long_Category['Date'].values else float('nan'))
        df_long_Category['Difference - prior month'] = df_long_Category['Number'] - df_long_Category['helper2']
        df_long_Category['Difference - prior month (per cent)'] = df_long_Category['Difference - prior month'] / df_long_Category['helper2'] * 100
        df_long_Category['Estimate flag - prior month'] = df_long_Category['helper2'].apply(lambda x: 'Y' if pd.isnull(x) else '')
        for i, row in df_long_Category.iterrows():
            if i == 0:
                continue
            if row['Estimate flag - prior month'] == 'Y':
                if i-1 in df_long_Category.index:
                    month_diff = row['Date'].month - df_long_Category.at[i-1, 'Date'].month
                    if month_diff != 0:
                        df_long_Category.loc[i, 'Difference -  month'] = (row['Number'] - df_long_Category.at[i-1, 'Number']) / month_diff
                        df_long_Category.loc[i, 'Difference - prior month (per cent)'] = df_long_Category.loc[i, 'Difference - prior month'] / df_long_Category.at[i-1, 'Number'] * 100
        df_long_Category = df_long_Category.drop(['helper', 'helper2'], axis=1)
        df_long = df_long.drop(df_long[df_long['Category'] == Category].index)
        df_long = pd.concat([df_long, df_long_Category])
    return df_long


def Waitlist_year_diff(df_long):
    df_long['Estimate flag - prior year'] = ''
    for Category in df_long['Category'].unique():
        df_long_Category = df_long[df_long['Category'] == Category].copy()
        df_long_Category['helper'] = df_long_Category['Date'] - pd.offsets.MonthEnd(12)
        df_long_Category['helper2'] = df_long_Category['helper'].apply(lambda x: df_long_Category.loc[df_long_Category['Date']==x, 'Number'].values[0] if x in df_long_Category['Date'].values else float('nan'))
        df_long_Category['Difference - prior year'] = df_long_Category['Number'] - df_long_Category['helper2']
        df_long_Category['Difference - prior year (per cent)'] = df_long_Category['Difference - prior year'] / df_long_Category['helper2'] * 100
        df_long_Category['Estimate flag - prior year'] = df_long_Category['helper2'].apply(lambda x: 'Y' if pd.isnull(x) else '')
        for i, row in df_long_Category.iterrows():
            if row['Date'] < df_long_Category['Date'].min() + pd.offsets.MonthEnd(12):
                continue
            if row['Estimate flag - prior year'] == 'Y':
                year_prior_date = row['Date'] - pd.offsets.MonthEnd(12)
                closest_date = min(df_long_Category['Date'], key=lambda x: abs(x - year_prior_date))
                df_long_Category.loc[i, 'Difference - prior year'] = (row['Number'] - df_long_Category.loc[df_long_Category['Date']==closest_date, 'Number'].values[0]/(row['Date'].month-closest_date.month/12))
                df_long_Category.loc[i, 'Difference - prior year (per cent)'] = df_long_Category.loc[i, 'Difference - prior year'] / df_long_Category.loc[df_long_Category['Date']==closest_date, 'Number'].values[0] * 100
        df_long_Category = df_long_Category.drop(['helper', 'helper2'], axis=1)
        df_long = df_long.drop(df_long[df_long['Category'] == Category].index)
        df_long = pd.concat([df_long, df_long_Category])
    return df_long

def Waitlist_calculate_12_month_average(df_long):
    def average_last_12_months(row):
        start_date = row['Date'] - pd.offsets.MonthEnd(11)
        end_date = row['Date']
        filtered_df = df_long[(df_long['Date'] >= start_date) & (df_long['Date'] <= end_date) & (df_long['Category'] == row['Category'])]
        return filtered_df['Number'].sum() / len(filtered_df)
    def average_prior_month_difference_last_12_months(row):
        start_date = row['Date'] - pd.offsets.MonthEnd(11)
        end_date = row['Date']
        filtered_df = df_long[(df_long['Date'] >= start_date) & (df_long['Date'] <= end_date) & (df_long['Category'] == row['Category'])]
        return filtered_df['Difference - prior month'].sum() / len(filtered_df)
    def average_prior_year_difference_last_12_months(row):
        start_date = row['Date'] - pd.offsets.MonthEnd(11)
        end_date = row['Date']
        filtered_df = df_long[(df_long['Date'] >= start_date) & (df_long['Date'] <= end_date) & (df_long['Category'] == row['Category'])]
        return filtered_df['Difference - prior year'].sum() / len(filtered_df)
    df_long['12 month rolling average'] = df_long.apply(average_last_12_months, axis=1)
    df_long['Difference - 12 month rolling average'] = df_long['Number'] - df_long['12 month rolling average']
    df_long['Difference - 12 month rolling average (per cent)'] = df_long['Difference - 12 month rolling average'] / df_long['12 month rolling average'] * 100
    df_long['12 month rolling average - prior month change'] = df_long.apply(average_prior_month_difference_last_12_months, axis=1)
    df_long['12 month rolling average - prior month change (per cent)'] = df_long['12 month rolling average - prior month change'] / df_long['12 month rolling average'] * 100
    df_long['12 month rolling average - prior year change'] = df_long.apply(average_prior_year_difference_last_12_months, axis=1)
    df_long['12 month rolling average - prior year change (per cent)'] = df_long['12 month rolling average - prior year change'] / df_long['12 month rolling average'] * 100
    return df_long

def Waitlist_calculate_cydiff(df_long):
    df_long['helper'] = df_long['Date'] - pd.offsets.YearEnd(1)
    df_long['helper2'] = df_long['helper'].apply(lambda x: df_long['Number'][df_long['Date']==x].values[0] if x in df_long['Date'].values else float('nan'))
    df_long['Difference - calendar year to date'] = df_long['Number'] - df_long['helper2']
    df_long['Difference - calendar year to date (per cent)'] = df_long['Difference - calendar year to date'] / df_long['helper2'] * 100
    df_long = df_long.drop(['helper', 'helper2'], axis=1)
    return df_long

def Waitlist_calculate_Priority_proportion(df_long):
    new_rows = pd.DataFrame()
    for date in df_long['Date'].unique():
        df_long_date = df_long[df_long['Date'] == date].copy()
        totalind = df_long_date[df_long_date['Category'] == 'Total individuals']['Number']
        priorityind = df_long_date[df_long_date['Category'] == 'Priority individuals']['Number']
        if totalind.empty or priorityind.empty:
            continue
        else:
            totalind = df_long_date[df_long_date['Category'] == 'Total individuals']['Number'].values[0]
            priorityind = df_long_date[df_long_date['Category'] == 'Priority individuals']['Number'].values[0]
            new_row_ind = pd.DataFrame([{'Date': date, 'Category': 'Proportion priority - individuals', 'Number': priorityind / totalind * 100}])
            new_rows = pd.concat([new_rows, new_row_ind])

            totalapp = df_long_date[df_long_date['Category'] == 'Total applications']['Number'].values[0]
            priorityapp = df_long_date[df_long_date['Category'] == 'Priority applications']['Number'].values[0]
            
            new_row_app = pd.DataFrame([{'Date': date, 'Category': 'Proportion priority - applications', 'Number': priorityapp / totalapp * 100}])
            new_rows = pd.concat([new_rows, new_row_app])

            new_row_avg_total = pd.DataFrame([{'Date': date, 'Category': 'Average number of individuals per application - total', 'Number': totalind / totalapp}])
            new_rows = pd.concat([new_rows, new_row_avg_total])

            new_row_avg_priority = pd.DataFrame([{'Date': date, 'Category': 'Average number of individuals per application - priority', 'Number': priorityind / priorityapp}])
            new_rows = pd.concat([new_rows, new_row_avg_priority])

            new_row_avg_nonpriority = pd.DataFrame([{'Date': date, 'Category': 'Average number of individuals per application - nonpriority', 'Number': (totalind - priorityind) / (totalapp - priorityapp)}])
            new_rows = pd.concat([new_rows, new_row_avg_nonpriority])

    df_long = pd.concat([df_long, new_rows])

    return df_long



def Waitlist_date_to_quarter_end(date):
    if date.month in [1, 2]:
        return pd.Timestamp(f'31-12-{(date.year)-1}')
    elif date.month in [4, 5]:
        return pd.Timestamp(f'31-03-{date.year}')
    elif date.month in [7, 8]:
        return pd.Timestamp(f'30-06-{date.year}')
    elif date.month in [10, 11]:
        return pd.Timestamp(f'30-09-{date.year}')
    else:
        return date

def Waitlist_add_quarter(df_long):
    df_long['Quarter'] = df_long['Date'].apply(Waitlist_date_to_quarter_end)
    return df_long



def Waitlist_nonpriority(df_long):
    new_rows = pd.DataFrame()
    for date in df_long['Date'].unique():
        df_long_date = df_long[df_long['Date'] == date].copy()
        totalind = df_long_date[df_long_date['Category'] == 'Total individuals']['Number']
        priorityind = df_long_date[df_long_date['Category'] == 'Priority individuals']['Number']
        if totalind.empty or priorityind.empty:
            continue
        else:
            totalind = df_long_date[df_long_date['Category'] == 'Total individuals']['Number'].values[0]
            priorityind = df_long_date[df_long_date['Category'] == 'Priority individuals']['Number'].values[0]
            new_row_ind = pd.DataFrame([{'Date': date, 'Category': 'nonPriority individuals', 'Number': totalind - priorityind}])
            new_rows = pd.concat([new_rows, new_row_ind])

        totalapp = df_long_date[df_long_date['Category'] == 'Total applications']['Number']
        priorityapp = df_long_date[df_long_date['Category'] == 'Priority applications']['Number']
        if totalapp.empty or priorityapp.empty:
            continue
        else:
            totalapp = df_long_date[df_long_date['Category'] == 'Total applications']['Number'].values[0]
            priorityapp = df_long_date[df_long_date['Category'] == 'Priority applications']['Number'].values[0]
            new_row_app = pd.DataFrame([{'Date': date, 'Category': 'nonPriority applications', 'Number': totalapp - priorityapp}])
            new_rows = pd.concat([new_rows, new_row_app])
    df_long = pd.concat([df_long, new_rows])
    return df_long

         
def Waitlist_add_population(df_long, population):
    population = population[['DATE', 'POPULATION']]
    df_long = df_long.merge(population, how='left', left_on='Date', right_on='DATE')
    df_long['Percentage of population'] = df_long.apply(lambda row: row['Number'] / row['POPULATION'] * 100 if row['Category'] in ['Total individuals', 'Priority individuals', 'nonPriority individuals'] else float('nan'), axis=1)
    df_long['Value per 10 000'] = df_long.apply(lambda row: row['Number'] / row['POPULATION'] * 10000 if row['Category'] in ['Total individuals', 'Priority individuals', 'nonPriority individuals'] else float('nan'), axis=1)
    if 'Difference - prior month' in df_long.columns:
        df_long['Difference - prior month per 10 000'] = df_long.apply(lambda row: row['Difference - prior month'] / row['POPULATION'] * 10000 if row['Category'] in ['Total individuals', 'Priority individuals', 'nonPriority individuals'] else float('nan'), axis=1)
    if 'Difference - prior year' in df_long.columns:
        df_long['Difference - prior year per 10 000'] = df_long.apply(lambda row: row['Difference - prior year'] / row['POPULATION'] * 10000 if row['Category'] in ['Total individuals', 'Priority individuals', 'nonPriority individuals'] else float('nan'), axis=1)
    if '12 month rolling average' in df_long.columns:
        df_long['12 month rolling average per 10 000'] = df_long.apply(lambda row: row['12 month rolling average'] / row['POPULATION'] * 10000 if row['Category'] in ['Total individuals', 'Priority individuals', 'nonPriority individuals'] else float('nan'), axis=1)
    df_long = df_long.drop(['DATE'], axis=1)
    return df_long

def Waitlist_final_long(df_long, save_latest, save):
    df_long['Category'] = df_long['Category'].str.replace('_', ' ')
    df_long['Category'] = df_long['Category'].str.title()
    df_long.loc[df_long['Category'].str.contains('Proportion'), 'Group'] = df_long.loc[df_long['Category'].str.contains('Proportion'), 'Category'].str.split(' - ').str[0]  
    df_long.loc[df_long['Category'].str.contains('Proportion'), 'Count'] = df_long.loc[df_long['Category'].str.contains('Proportion'), 'Category'].str.split(' - ').str[1]
    df_long.loc[df_long['Category'].str.contains('Average'), 'Group'] = df_long.loc[df_long['Category'].str.contains('Average'), 'Category'].str.split(' - ').str[0]
    df_long.loc[df_long['Category'].str.contains('Average'), 'Count'] = df_long.loc[df_long['Category'].str.contains('Average'), 'Category'].str.split(' - ').str[1]
    df_long.loc[df_long['Group'].isnull(), 'Group'] = df_long.loc[df_long['Group'].isnull(), 'Category'].str.split(' ').str[0]
    df_long.loc[df_long['Count'].isnull(), 'Count'] = df_long.loc[df_long['Count'].isnull(), 'Category'].str.split(' ').str[1]
    cols = df_long.columns.tolist()
    ids =["Date", "Category", "Group", "Count", "Estimate flag - Number", "Estimate flag - prior month", "Estimate flag - prior year"]
    values = [col for col in cols if col not in ids]
    df_long = df_long.melt(id_vars=ids, value_vars=values, var_name="Metric", value_name="Value")
    df_long = df_long[df_long['Metric'] != 'POPULATION']
    df_long['change from prior month'] = df_long.groupby(['Category', 'Metric'])['Value'].diff()
    df_long['change from prior month (per cent)'] = df_long['change from prior month'] / df_long['Value'].shift(1) * 100
    df_long['change from prior year'] = df_long.groupby(['Category', 'Metric'])['Value'].diff(12)
    df_long['change from prior year (per cent)'] = df_long['change from prior year'] / df_long['Value'].shift(12) * 100
    df_long.loc[(df_long['Metric'] == 'Difference - financial year to date') & (df_long['Date'].dt.month == 7), 'change from prior month'] = float('nan')
    df_long.loc[(df_long['Metric'] == 'Difference - financial year to date (per cent)') & (df_long['Date'].dt.month == 7), 'change from prior month'] = float('nan')
    df_long.loc[(df_long['Metric'] == 'Difference - calendar year to date') & (df_long['Date'].dt.month == 1), 'change from prior month'] = float('nan')
    df_long.loc[(df_long['Metric'] == 'Difference - calendar year to date (per cent)') & (df_long['Date'].dt.month == 1), 'change from prior month'] = float('nan')
    df_long.loc[df_long['Metric'] == 'Number', 'change from prior month'] = float('nan')
    df_long.loc[(df_long['Metric'] == 'Difference - financial year to date') & (df_long['Date'].dt.month == 7), 'change from prior year'] = float('nan')
    df_long.loc[(df_long['Metric'] == 'Difference - financial year to date (per cent)') & (df_long['Date'].dt.month == 7), 'change from prior year'] = float('nan')
    df_long.loc[(df_long['Metric'] == 'Difference - calendar year to date') & (df_long['Date'].dt.month == 1), 'change from prior year'] = float('nan')
    df_long.loc[(df_long['Metric'] == 'Difference - calendar year to date (per cent)') & (df_long['Date'].dt.month == 1), 'change from prior year'] = float('nan')
    df_long.loc[df_long['Metric'] == 'Number', 'change from prior year'] = float('nan')
    cols = df_long.columns.tolist()
    ids =["Date", "Category", "Group", "Count", "Estimate flag - Number", "Estimate flag - prior month", "Estimate flag - prior year", "Metric"]
    values = [col for col in cols if col not in ids]
    df_long = df_long.melt(id_vars=ids, value_vars=values, var_name="Value type", value_name="Number")
    df_long = df_long.dropna(subset=['Number'])
    df_long = df_long.rename(columns={'Number': 'Value'})


    df_long['Number type 1'] = df_long['Value']
    df_long['Number type 2'] = df_long['Value']
    df_long['Metric 1'] = df_long['Metric']
    df_long['Metric 2'] = df_long['Metric']

    df_long.loc[df_long['Metric'].str.contains('per cent'), 'Number type 1'] = 'Percentage'
    df_long.loc[~df_long['Metric'].str.contains('per cent'), 'Number type 1'] = 'Actual'
    df_long.loc[df_long['Metric'].str.contains('per cent'), 'Metric'] = df_long.loc[df_long['Metric'].str.contains('per cent'), 'Metric'].str.replace(' (per cent)', '')
    df_long.loc[df_long['Metric'].str.contains('Percentage'), 'Number type 1'] = 'Percentage'
    df_long.loc[df_long['Metric'].str.contains('per 10 000'), 'Number type 1'] = 'per 10 000'
    df_long.loc[df_long['Metric'].str.contains('per 10 000'), 'Metric'] = df_long.loc[df_long['Metric'].str.contains('per 10 000'), 'Metric'].str.replace(' per 10 000', '')
    df_long.loc[df_long['Value type'].str.contains('per cent'), 'Number type 2'] = 'Percentage'
    df_long.loc[~df_long['Value type'].str.contains('per cent'), 'Number type 2'] = 'Actual'
    df_long.loc[df_long['Value type'].str.contains('per cent'), 'Value type'] = df_long.loc[df_long['Value type'].str.contains('per cent'), 'Value type'].str.replace(' (per cent)', '')

    df_long.loc[df_long['Metric'].str.contains(' - '), 'Metric 1'] = df_long.loc[df_long['Metric'].str.contains(' - '), 'Metric'].str.split(' - ').str[0]
    df_long.loc[df_long['Metric'].str.contains(' - '), 'Metric 2'] = df_long.loc[df_long['Metric'].str.contains(' - '), 'Metric'].str.split(' - ').str[1]
    df_long.loc[~df_long['Metric'].str.contains(' - '), 'Metric 1'] = df_long.loc[~df_long['Metric'].str.contains(' - '), 'Metric']
    df_long.loc[~df_long['Metric'].str.contains(' - '), 'Metric 2'] = ''
    df_long = df_long.drop(['Metric'], axis=1)

    df_long['Estimate'] = 'N'
    
    df_long.loc[(df_long['Estimate flag - prior month'] == 'Y') & (df_long['Metric 1'].str.contains('prior month') | df_long['Metric 2'].str.contains('prior month') | df_long['Value type'].str.contains('prior month')), 'Estimate'] = 'Y'
    df_long.loc[(df_long['Estimate flag - prior year'] == 'Y') & (df_long['Metric 1'].str.contains('prior year') | df_long['Metric 2'].str.contains('prior year') | df_long['Value type'].str.contains('prior year')), 'Estimate'] = 'Y'
    df_long.loc[(df_long['Estimate flag - Number'] == 'Y') & (df_long['Metric 1'] == 'Number'), 'Estimate'] = 'Y'
    df_long = df_long.drop(['Estimate flag - prior month', 'Estimate flag - prior year', 'Estimate flag - Number'], axis=1)

    df_long = df_long.rename(columns={'Group': 'Description1', 'Count': 'Description2', 'Metric 1': 'Description3', 'Metric 2': 'Description4', 'Number type 1': 'Description5', 'Value type': 'Description6', 'Number type 2': 'Description7'})
    df_long = df_long[['Date', 'Category', 'Description1', 'Description2', 'Description3', 'Description4', 'Description5', 'Description6', 'Description7', 'Estimate', 'Value']]
    df_long.loc[df_long['Description3'] == 'Value', 'Description3'] = 'Number'
    df_long.loc[df_long['Description4'] == '', 'Description4'] = '-'
    df_long.loc[df_long['Description6'] == 'Value', 'Description7'] = '-'
    df_long.loc[df_long['Description6'] == 'Value', 'Description6'] = '-'
    df_long.to_csv(Waitlist_trend_longdf, index=False)


    df_latest = pd.DataFrame()
    for Category in df_long['Category'].unique():
        max_date = df_long[df_long['Category'] == Category]['Date'].max()
        df_cat_latest = df_long[(df_long['Category'] == Category) & (df_long['Date'] == max_date)]
        df_latest = pd.concat([df_latest, df_cat_latest])
    df_latest = df_latest.reset_index(drop=True)
    df_latest.to_csv(Waitlist_latestdf, index=False)
    return max_date


def import_waitlist_data():
    try:
        df = Waitlist_load_data('DATA/SOURCE DATA/Public housing/Waitlist_trend.xlsx')
        df_long = Waitlist_convert_to_long_form(df)
        df_long = Waitlist_gap_filler(df_long)
        df_long = Waitlist_nonpriority(df_long)
        df_long = Waitlist_calculate_Priority_proportion(df_long)
        df_long = Waitlist_add_population(df_long, pd.read_csv(PopulationStateMonthlydf))
        df_long = Waitlist_month_diff(df_long)
        df_long = Waitlist_year_diff(df_long)
        df_long = Waitlist_calculate_cydiff(df_long)
        df_long = Waitlist_calculate_12_month_average(df_long)
        df_long = Waitlist_FYtdchange(df_long)
        max_date = Waitlist_final_long(df_long, Waitlist_latestdf, Waitlist_trend_longdf)
        update_date = pd.to_datetime('today').strftime('%d/%m/%Y')
        Waitlist_clear_new_data('DATA/SOURCE DATA/Public housing/Waitlist_trend.xlsx')
        update_log(max_date, update_date, 'Waitlist trend - statewide')
    except:
        pass
    return





