import pandas as pd
import streamlit as st
import plotly.graph_objects as go

ROGSHomelessnessdf = 'DATA/PROCESSED DATA/ROGS/ROGS G19.csv'

census_data = st.selectbox('Select dataset', ['Total by state', 'Geographic breakdown', 'Aboriginal and Torres Strait Islander status', 'Sex and Age'])

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

elif census_data == 'Geographic breakdown':
    st.markdown(f'Note - error in ABS table builder for LGAs, awaiting help on file and limited to SA4 for time being however quick swap in once received')
    df = pd.read_csv('DATA/PROCESSED DATA/Census/Multiyear/SA4Income_1621.csv')
    df = df.melt(id_vars=['OPGP HOMELESSNESS OPERATIONAL GROUPS', 'SA4', 'CENSUS_YEAR'], var_name='Income', value_name='Value')
    #replace Not Applicable with Not applicable
    df['OPGP HOMELESSNESS OPERATIONAL GROUPS'] = df['OPGP HOMELESSNESS OPERATIONAL GROUPS'].replace('Not Applicable', 'Not applicable')
    df = df[df['Income']=='TOTAL']
    df = df.drop(columns=['Income'])
    #in SA4, replace "Western Australia - " with ""
    df['SA4'] = df['SA4'].str.replace('Western Australia - ', '')
    geoselect = st.multiselect('Select area', df['SA4'].unique())
    datalabels = st.radio('Data labels', ['On', 'Off'], index=0, horizontal=True, key='censusSA4datalabels')
    dftotal = df[df['OPGP HOMELESSNESS OPERATIONAL GROUPS']=='Total']
    dfna = df[df['OPGP HOMELESSNESS OPERATIONAL GROUPS']=='Not applicable']
    dftotalna = pd.concat([dftotal, dfna])
    #pivot so OPGP HOMELESSNESS OPERATIONAL GROUPS is columns
    dftotalna = dftotalna.pivot(index=['SA4', 'CENSUS_YEAR'], columns='OPGP HOMELESSNESS OPERATIONAL GROUPS', values='Value').reset_index()
    dftotalna['Total homelessness'] = dftotalna['Total'] - dftotalna['Not applicable']
    dftotalna['per 10k'] = dftotalna['Total homelessness'] / dftotalna['Total'] * 10000
    #drop Not applicable
    dftotalna = dftotalna.drop(columns=['Not applicable'])
    #melt back to long format
    dftotalna = dftotalna.melt(id_vars=['SA4', 'CENSUS_YEAR'], var_name='Measure', value_name='Value')
    df = df[df['OPGP HOMELESSNESS OPERATIONAL GROUPS']!='Total']
    df = df[df['OPGP HOMELESSNESS OPERATIONAL GROUPS']!='Not applicable']
    df16 = df[df['CENSUS_YEAR']==2016]
    df21 = df[df['CENSUS_YEAR']==2021]

    #filter dftotal21 for geoselect
    df10k = dftotalna[dftotalna['SA4'].isin(geoselect)]
    df10k = df10k[df10k['Measure']=='per 10k']
    df10k = df10k.drop(columns=['Measure'])

    dftotal = dftotalna[dftotalna['SA4'].isin(geoselect)]
    dftotal = dftotal[dftotal['Measure']=='Total homelessness']
    dftotal = dftotal.drop(columns=['Measure'])

    fig = go.Figure()
    fig.add_trace(go.Bar(x=[df10k['SA4'], df10k['CENSUS_YEAR']], y=df10k['Value'], name='per 10k'))

    if datalabels == 'On':
        fig.update_traces(texttemplate='%{text:.2s}', textposition='inside', text=df10k['Value'])
    fig.update_layout(barmode='group', title='Homelessness; per 10k population', xaxis_title="SA4", yaxis_title='Value')
    st.plotly_chart(fig)

    fig = go.Figure()
    fig.add_trace(go.Bar(x=[dftotal['SA4'], dftotal['CENSUS_YEAR']], y=dftotal['Value'], name='Total persons in homelessness groups'))
    if datalabels == 'On':
        fig.update_traces(texttemplate='%{text:.2s}', textposition='inside', text=dftotal['Value'])
    fig.update_layout(barmode='group', title='Homelessness; total persons in homelessness groups', xaxis_title="SA4", yaxis_title='Value')
    st.plotly_chart(fig)

    for sa4 in geoselect:
        filtereddf16 = df16[df16['SA4']==sa4]
        filtereddf21 = df21[df21['SA4']==sa4]
    
        #plotly bar, x=OPGP HOMELESSNESS OPERATIONAL GROUPS, y=Value, color=CENSUS_YEAR
        fig = go.Figure()
        fig.add_trace(go.Bar(x=filtereddf16['OPGP HOMELESSNESS OPERATIONAL GROUPS'], y=filtereddf16['Value'], name='2016'))
        if datalabels == 'On':
            fig.update_traces(texttemplate='%{text:.2s}', textposition='inside', text=filtereddf16['Value'])
        fig.add_trace(go.Bar(x=filtereddf21['OPGP HOMELESSNESS OPERATIONAL GROUPS'], y=filtereddf21['Value'], name='2021'))
        if datalabels == 'On':
            fig.update_traces(texttemplate='%{text:.2s}', textposition='inside', text=filtereddf21['Value'])
        fig.update_layout(barmode='group', title='Homelessness; by homelessness operational group', yaxis_title='persons')
        st.plotly_chart(fig)

        #pie chart for each year
        fig = go.Figure()
        fig.add_trace(go.Pie(labels=filtereddf16['OPGP HOMELESSNESS OPERATIONAL GROUPS'], values=filtereddf16['Value'], name='2016'))
        fig.update_layout(title='Homelessness groups - 2016', yaxis_title='persons')
        if datalabels == 'On':
            fig.update_traces(textposition='inside', textinfo='percent+value')
        st.plotly_chart(fig)
        fig = go.Figure()
        fig.add_trace(go.Pie(labels=filtereddf21['OPGP HOMELESSNESS OPERATIONAL GROUPS'], values=filtereddf21['Value'], name='2021'))
        fig.update_layout(title='Homelessness groups - 2021', xaxis_title="Homelessness operational group", yaxis_title='Value')
        if datalabels == 'On':
            fig.update_traces(textposition='inside', textinfo='percent+value')
        st.plotly_chart(fig)




