import pandas as pd



def delete_source_file(file):
    if os.path.exists(source_file):
        os.remove(source_file)
        return
    else:
        return

def update_log(latest_date, update_date, dataset = 'Population (by State, Sex, Age to 65+)'):
    try:
        update_log = pd.read_excel(updatelogfile)
    except:
        update_log = pd.DataFrame(columns=['Dataset', 'Latest data point', 'Date last updated'])
    new_row = pd.DataFrame({'Dataset': [dataset], 'Latest data point': [latest_date], 'Date last updated': [update_date]})
    update_log = pd.concat([update_log, new_row], ignore_index=True)
    update_log['Latest data point'] = pd.to_datetime(update_log['Latest data point'], format='%d/%m/%Y')
    update_log['Date last updated'] = pd.to_datetime(update_log['Date last updated'], format='%d/%m/%Y')
    update_log = update_log.sort_values(by=['Latest data point', 'Date last updated'], ascending=False).drop_duplicates(subset=['Dataset'], keep='first')
    update_log['Latest data point'] = update_log['Latest data point'].dt.strftime('%d/%m/%Y')
    update_log['Date last updated'] = update_log['Date last updated'].dt.strftime('%d/%m/%Y')                            
    update_log.to_excel(updatelogfile, index=False)
    book = openpyxl.load_workbook(updatelogfile)
    sheet = book.active
    for column_cells in sheet.columns:
        length = max(len(as_text(cell.value)) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = length
    book.save(updatelogfile)
    return

def as_text(value):
    if value is None:
        return ""
    return str(value)

def quarter_to_date(quarter):
    year, q = quarter.split('-')
    if q == 'Q1':
        return f'31/03/{year}'
    elif q == 'Q2':
        return f'30/06/{year}'
    elif q == 'Q3':
        return f'30/09/{year}'
    elif q == 'Q4':
        return f'31/12/{year}'

def group_age(age_group):
    if age_group.endswith('+'):
        lower_age_limit = int(age_group[:-1])
    elif age_group == 'All ages':
        return age_group
    else:
        lower_age_limit = int(age_group.split('-')[0])
    if lower_age_limit >= 65:
        return '65+'
    else:
        return age_group

def new_pop_file(file):
    Population_State_Sex_Age = pd.read_csv(file)
    Population_State_Sex_Age = Population_State_Sex_Age.rename(columns={'SEX: Sex': 'Sex', 'AGE: Age': 'Age group', 'TIME_PERIOD: Time Period': 'Quarter', 'REGION: Region': 'Region', 'OBS_VALUE': 'Population'})
    Population_State_Sex_Age = Population_State_Sex_Age.drop(columns=['DATAFLOW', 'MEASURE: Measure', 'FREQ: Frequency', 'UNIT_MEASURE: Unit of Measure', 'OBS_STATUS: Observation Status', 'OBS_COMMENT: Observation Comment'])
    Population_State_Sex_Age['Date'] = Population_State_Sex_Age['Quarter'].apply(quarter_to_date)
    Population_State_Sex_Age = Population_State_Sex_Age.drop(columns=['Quarter'])
    Population_State_Sex_Age['Sex'] = Population_State_Sex_Age['Sex'].map({
    '1: Males': 'Male',
    '2: Females': 'Female',
    '3: Persons': 'Total'
    })
    Population_State_Sex_Age['Age group'] = Population_State_Sex_Age['Age group'].str.split(': ').str[1]
    Population_State_Sex_Age['Region'] = Population_State_Sex_Age['Region'].map({
    '1: New South Wales': 'NSW',
    '2: Victoria': 'Vic',
    '3: Queensland': 'Qld',
    '4: South Australia': 'SA',
    '5: Western Australia': 'WA',
    '6: Tasmania': 'Tas',
    '7: Northern Territory': 'NT',
    '8: Australian Capital Territory': 'ACT',
    'AUS: Australia': 'National'
    })
    Population_State_Sex_Age['Date'] = pd.to_datetime(Population_State_Sex_Age['Date'], format='%d/%m/%Y')
    Population_State_Sex_Age = Population_State_Sex_Age.sort_values(by='Date', ascending=True)
    pivot_df = Population_State_Sex_Age.pivot_table(
        index=['Date', 'Sex', 'Age group'], 
        columns='Region', 
        values='Population',
        fill_value=0
    ).reset_index()

    pivot_df.columns = [f'{col}_Population' if col in ['NSW', 'Vic', 'Qld', 'WA', 'SA', 'Tas', 'ACT', 'NT', 'National'] else col for col in pivot_df.columns]

    Population_State_Sex_Age = pivot_df.rename(columns={'NSW': 'NSW_Population', 'Vic': 'Vic_Population', 'Qld': 'Qld_Population', 'WA': 'WA_Population', 'SA': 'SA_Population', 'Tas': 'Tas_Population', 'ACT': 'ACT_Population', 'NT': 'NT_Population', 'National': 'National_Population'})

    Population_State_Sex_Age['Age group'] = Population_State_Sex_Age['Age group'].apply(group_age)

    Population_State_Sex_Age = Population_State_Sex_Age.groupby(['Age group', 'Sex', 'Date']).agg({
        'NSW_Population': 'sum',
        'Vic_Population': 'sum',
        'Qld_Population': 'sum',
        'WA_Population': 'sum',
        'SA_Population': 'sum',
        'Tas_Population': 'sum',
        'ACT_Population': 'sum',
        'NT_Population': 'sum',
        'National_Population': 'sum'
    }).reset_index()

    latest_date = Population_State_Sex_Age['Date'].max()
    latest_date = pd.to_datetime(latest_date)
    try:
        current_file = pd.read_csv('DATA/PROCESSED DATA/Population/Population_State_Sex_Age_to_65+.csv')
    except:
        current_file = Population_State_Sex_Age
    
    latest_current_date = current_file['Date'].max()
    latest_current_date = pd.to_datetime(latest_current_date)

    if latest_date < latest_current_date:
        return
    else:
        Population_State_Sex_Age.to_csv(PopulationStateSexAge65df, index=False)
        latest_date = latest_date.strftime('%d/%m/%Y')
        update_date = pd.to_datetime('today').strftime('%d/%m/%Y')
        update_log(latest_date, update_date, dataset)
    delete_source_file(PopulationNewFile)
    total(Population_State_Sex_Age)
    return

def total(df):
    df = df[df['Age group'] == 'All ages']
    df = df.drop(columns='Age group')
    save_to = 'DATA/PROCESSED DATA/Population/Population_State_Sex_Total'
    df.to_csv(save_to + '.csv', index=False)
    population_to_monthly(save_to)
    df = df[df['Sex'] == 'Total']
    df = df.drop(columns='Sex')
    save_to = 'DATA/PROCESSED DATA/Population/Population_State_Total'
    df.to_csv(save_to + 'csv', index=False)
    population_to_monthly (save_to)
    columns = df.columns.tolist()
    columns.remove('WA_Population')
    columns.remove('Date')
    df = df.drop(columns=columns)
    df = df.rename(columns={'WA_Population': 'Population'})
    save_to = 'DATA/PROCESSED DATA/Population/Population_WA_Total'
    df.to_csv(save_to + '.csv', index=False)
    return


def import_population_data():
    try:
        new_pop_file(PopulationNewFile)
    except:
        pass
    return

def monthlyStatetotal():
    df = pd.read_csv('DATA/PROCESSED DATA/Population/Population_State_Total.csv')
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')
    df = df.sort_values(by='Date', ascending=True)
    #resample to monthly, interpolate missing values
    df = df.set_index('Date').resample('M').mean().interpolate(method='linear').reset_index()
    df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')
    #round down any numeric columns to 0 decimal places
    df = df.round(0)
    df.to_csv('DATA/PROCESSED DATA/Population/Population_State_Total_monthly.csv', index=False)
    return

monthlyStatetotal()