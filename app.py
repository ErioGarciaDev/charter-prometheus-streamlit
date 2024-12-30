import streamlit as st
import boto3
import os
import awswrangler as wr
import time
import datetime
import pandas as pd
import plotly.express as px
import math
from datetime import datetime
import warnings
from utils import display_header_section, plot_graphs
from PIL import Image
icon = Image.open("images/PrometheusIcon.jfif")
warnings.filterwarnings("ignore")


maxUploadSize = 3000
st.set_page_config(
    page_title="Prometheus Parser",
    page_icon=icon,
    layout="wide",
)


ENV = "dev"
PRIMARY_REGION = "us-east-1"
boto3.setup_default_session(region_name=PRIMARY_REGION)

s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')
ssm = boto3.client('ssm')


ATHENA_DB = ssm.get_parameter(Name='/prometheus/' + ENV +'/athena-db-name', WithDecryption=False)['Parameter']['Value']
PREFIX_STORAGE = ssm.get_parameter(Name='/prometheus/'+ ENV + '/storage-prefix-name', WithDecryption=False)['Parameter']['Value']
PREFIX_INGESTION = ssm.get_parameter(Name='/prometheus/' + ENV +'/ingestion-prefix-name', WithDecryption=False)['Parameter']['Value']
LANDING_BUCKET = ssm.get_parameter(Name='/prometheus/' + ENV + "/" + PREFIX_INGESTION + '/landing-bucket-name', WithDecryption=False)['Parameter']['Value']
QUERIES_BUCKET = ssm.get_parameter(Name='/prometheus/' + ENV + "/" + PREFIX_STORAGE + '/queries-bucket-name', WithDecryption=False)['Parameter']['Value']

AGG_SUMMARY_TABLE = 'agg_summary'
SELECT_STATEMENT = "SELECT logfile, network, setup, model, firmware, test, traffic, team, process_date"
get_agg_summary_table = f"{SELECT_STATEMENT} FROM {AGG_SUMMARY_TABLE}"
get_test_date= "SELECT DISTINCT test_date FROM transitions"


display_header_section()

df = wr.athena.read_sql_query(get_agg_summary_table, database=ATHENA_DB, ctas_approach=False, s3_output="s3://"+QUERIES_BUCKET+"/agg-summary-streamlit" )
df2 = wr.athena.read_sql_query(get_test_date, database=ATHENA_DB, ctas_approach=False, s3_output="s3://"+QUERIES_BUCKET+"/agg-summary-streamlit" )

logfiles_filter = list(df.logfile.sort_values().unique())
network_filter = list(df.network.sort_values().unique())
setup_filter = list(df.setup.sort_values().unique())
model_filter = list(df.model.sort_values().unique())
firmware_filter = list(df.firmware.sort_values().unique())
test_filter = list(df.test.sort_values().unique())
traffic_filter = list(df.traffic.sort_values().unique())
team_filter = list(df.team.sort_values().unique())
test_date_filter = list(df2.test_date.sort_values().unique())
date_filter = list(df.process_date.sort_values().unique())

filters = dict()
keys = ["logfile", "network", 'setup','model', 'firmware', 'test', 'traffic', 'process_date']
for key in keys:
    filters[key] = []

with st.container():
    with st.form("filters"):
        with st.sidebar:
            submit = st.form_submit_button('📊Apply Filters & Plot Graphs')
            logfiles = st.multiselect('Log File', logfiles_filter)     
            st.caption("If the 'Log file' field is populated then all other filter selections except 'Transition Threshold' will be ignored.")
            st.markdown('---')
            st.subheader("Metadata Fields")
            networks = st.multiselect('Test Network',network_filter)  
            setups = st.multiselect('Test Set-up',setup_filter)  
            models = st.multiselect('Device Model',model_filter)  
            firmwares = st.multiselect('Device Firmware',firmware_filter)  
            tests = st.multiselect('Test Case',test_filter)  
            traffics = st.multiselect('Traffic Flow',traffic_filter,)  
            teams = st.multiselect('Team',team_filter,)  
            test_dates = st.multiselect('Test Date',test_date_filter)
            dates = st.multiselect('Process Date',date_filter) 
            st.markdown('---')
            st.subheader("Transition Threshold")
            total_transitions = st.checkbox('Total Transitions')
            st.caption("If 'Total Transitions' is selected then the Min and Max values will be ignored.")
            col1, col2 = st.columns(2)
            with col1:
                min_transitions = st.number_input('Min Threshold (sec)',  min_value=0.00, value=.250, step=.05)
            with col2:
                max_transitions = st.number_input('Max Threshold (sec)',  min_value=0.00, value=15.00, step=.05)
            st.markdown('#')
            st.markdown('#')
            st.markdown('#')



if submit:
    filters["logfile"]=logfiles
    filters["network"]=networks
    filters["setup"]=setups
    filters["model"]=models
    filters["firmware"]=firmwares
    filters["test"]=tests
    filters["traffic"]=traffics
    filters["team"]=teams
    filters["test_date"]=test_dates
    filters["process_date"]=dates
    
    subqueries = []
    select_statement= "SELECT direction, transition_time, logfile, network, setup, model, firmware, test, traffic, team, test_date, process_date"
    if filters['logfile']: 
        if total_transitions == True:
            transitions_query = f"{select_statement} FROM transitions WHERE logfile in ({str(filters['logfile'])[1:-1]})" 
        else:
            transitions_query = f"{select_statement} FROM transitions WHERE logfile in ({str(filters['logfile'])[1:-1]}) AND transition_time BETWEEN {min_transitions*1000} AND {max_transitions*1000};" 
    elif filters['network'] or filters['setup'] or filters['model'] or filters['firmware'] or filters['test'] or filters['traffic'] or filters['test_date'] or filters['process_date']:
        if filters['network']: 
            networks_filter = f"network in ({str(filters['network'])[1:-1]})"
            subqueries.append(networks_filter)
        if filters['setup']: 
            setups_filter = f"setup in ({str(filters['setup'])[1:-1]})"
            subqueries.append(setups_filter)
        if filters['model'] : 
            models_filter = f"model in ({str(filters['model'] )[1:-1]})"
            subqueries.append(models_filter)
        if filters['firmware']: 
            firmwares_filter = f"firmware in ({str(filters['firmware'])[1:-1]})"
            subqueries.append(firmwares_filter)
        if filters['test']: 
            tests_filter = f"test in ({str(filters['test'])[1:-1]})"
            subqueries.append(tests_filter)
        if filters['traffic']: 
            traffics_filter = f"traffic in ({str(filters['traffic'])[1:-1]})"
            subqueries.append(traffics_filter)
        if filters['team']: 
            traffics_filter = f"team in ({str(filters['team'])[1:-1]})"
            subqueries.append(traffics_filter)
        if filters['test_date']:
            dates_formatted = []
            char1 = '('
            char2 = ')'
            for date in list(filters['test_date']):
                date = str(date)
                dates_formatted.append(date)    
            dates_filter = []
            if dates_formatted:
                for index, date in enumerate(dates_formatted):
                    dates_filter.append(f"test_date = date('{str(dates_formatted[index])}')")  
            test_date_subquery = (' OR '.join(dates_filter))
            subqueries.append(test_date_subquery)   
        if filters['process_date']:
            dates_formatted = []
            char1 = '('
            char2 = ')'
            for date in list(filters['process_date']):
                date = str(date)
                dates_formatted.append(date)    
            dates_filter = []
            if dates_formatted:
                for index, date in enumerate(dates_formatted):
                    dates_filter.append(f"process_date = date('{str(dates_formatted[index])}')")  
            date_subquery = (' OR '.join(dates_filter))
            subqueries.append(date_subquery)   
        where_subquery = (' AND '.join(subqueries))
        if total_transitions == True:
            transitions_query = f"{select_statement} FROM transitions WHERE {where_subquery}"
        else:
            transitions_query = f"{select_statement} FROM transitions WHERE {where_subquery}  AND transition_time BETWEEN {min_transitions*1000} AND {max_transitions*1000};"
    else: 
        if total_transitions == True:
            transitions_query = f"{select_statement} FROM transitions"
        else:
            transitions_query = f"{select_statement} FROM transitions WHERE transition_time BETWEEN {min_transitions*1000} AND {max_transitions*1000};"

    dff = wr.athena.read_sql_query(transitions_query, database=ATHENA_DB, ctas_approach=False, s3_output="s3://"+QUERIES_BUCKET+"/transitions-streamlit")
    plot_graphs(df=dff, 
                total_transitions=total_transitions,
                min_transitions=min_transitions,
                max_transitions=max_transitions,
                title='Cumulative Transition Data', 
                direction_hand_in_or_last_to_switch='Hand-In',
                direction_hand_out_or_switch_to_first='Hand-Out', 
                line_chart_title='Cumulative', 
                histogram_title_1='Hand-In - Cumulative',
                histogram_title_2='Hand-Out - Cumulative' )   
