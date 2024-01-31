import pandas as pd
import streamlit as st
import plotly.graph_objects as go

ROGSHomelessnessdf = 'DATA/PROCESSED DATA/ROGS/ROGS G19.csv'

census_data = st.selectbox('Select dataset', ['Total by state', 'Geographic breakdown and income', 'Aboriginal and Torres Strait Islander status', 'Sex and Age'])

if census_data == 'Total by state':
    df = pd.read_csv(ROGSHomelessnessdf, encoding='latin-1')
    df = df.sort_values(by='Year', ascending=True)
    df['Year'] = df['Year'].astype(str)
    df = df.rename(columns={'Aust': 'National'})
    regions = ['National', 'WA', 'Vic', 'Qld', 'SA', 'NSW', 'Tas', 'NT', 'ACT']

    df = df[df['Measure']=="Homelessness; by homelessness operational group"]

    df['Description2'] = df['Description2'].fillna('Persons')
    col1, col2, col3 = st.columns(3)
    with col1:
        Desc2 = st.selectbox('Select Description2 filter', df['Description2'].unique(), index=0)
        df = df[df['Description2'] == Desc2]
    with col2:
        if len(df['Description3'].unique()) > 1:
            Desc3 = st.selectbox('Select Description3 filter', df['Description3'].unique(), index=0)
            df = df[df['Description3'] == Desc3]
    with col3:
        if len(df['Description4'].unique()) > 1:
            Desc4 = st.selectbox('Select Description4 filter', df['Description4'].unique(), index=0)
            df = df[df['Description4'] == Desc4]

    df = df.sort_values(by=['Year'], ascending=True)
    #for region in regions, filter df for region, plotly bar, x=Year, y=Value, color=Region, group
    fig = go.Figure()
    yunits = df['Unit'].unique()[0]
    for region in regions:
        fig.add_trace(go.Bar(x=df['Year'], y=df[region], name=region))
    fig.update_layout(barmode='group', title='Homelessness; by homelessness operational group', xaxis_title="Year", yaxis_title=yunits)
    st.plotly_chart(fig)
elif census_data == 'Geographic breakdown and income':
    