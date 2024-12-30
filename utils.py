import streamlit as st
import pandas as pd 
import plotly.express as px
import time
import math

order_of_df = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', '90%', 'median', 'max']

def plot_graphs(df, total_transitions, min_transitions, max_transitions, title, direction_hand_in_or_last_to_switch, direction_hand_out_or_switch_to_first, line_chart_title, histogram_title_1, histogram_title_2 ):
    
    st.success(title)
    df['transition_time'] = df['transition_time']/1000
    if total_transitions==True:
        pass
    else:
        df = df[df["transition_time"].between(min_transitions, max_transitions)]
    df.rename(columns = {'transition_time':'median' }, inplace = True)
    pd.set_option('display.float_format', lambda x: '%.5f' % x)

    transposed_concatenated_df=pd.concat([df.groupby("direction")["median"].describe(percentiles=[.25,.50,.75,.90]).transpose(),
                                        df.groupby("direction")["median"].median().to_frame().transpose() 
                                        ]).round(2).reset_index()
    ordered_df = transposed_concatenated_df.astype({'index' : pd.CategoricalDtype(order_of_df,ordered=True)})
    ordered_df.sort_values('index', inplace=True)
    ordered_df.rename(columns={"index": ""}, inplace=True)

    hide_table_row_index = """
            <style>
            thead tr th:first-child {display:none}
            tbody th {display:none}
            </style>
            """

    st.markdown(hide_table_row_index, unsafe_allow_html=True)
    st.table(ordered_df)

    df.rename(columns = {'median':'Transition Time (s)' }, inplace = True)
    graph=df[['direction', 'Transition Time (s)']]
    graph.sort_values(by=['direction', 'Transition Time (s)'], inplace=True)
    
    hand_in_or_last_to_switch = graph[graph['direction']==direction_hand_in_or_last_to_switch]
    hand_in_or_last_to_switch['% of Transitions'] = len(hand_in_or_last_to_switch) and 1/len(hand_in_or_last_to_switch) or 0
    hand_in_or_last_to_switch['% of Transitions'] = hand_in_or_last_to_switch['% of Transitions'].cumsum()
    
    hand_out_or_switch_to_first = graph[graph['direction']==direction_hand_out_or_switch_to_first]
    hand_out_or_switch_to_first['% of Transitions'] = len(hand_out_or_switch_to_first) and 1/len(hand_out_or_switch_to_first) or 0
    hand_out_or_switch_to_first['% of Transitions'] = hand_out_or_switch_to_first['% of Transitions'].cumsum()

    graph = pd.concat([hand_in_or_last_to_switch, hand_out_or_switch_to_first])
    
    max_value = len(graph) and math.ceil(graph['Transition Time (s)'].max()) or 0
    if max_value == 1:
        max_value = graph['Transition Time (s)'].max()
    min_value = len(graph) and math.ceil(graph['Transition Time (s)'].min())-1 or 0
    
    fig = px.line(graph, x="Transition Time (s)", y="% of Transitions", color='direction',height=350, template="none", labels={
                                                                                                                        "Transition Time (s)": "Transition Time (sec)",
                                                                                                                        "% of Transitions" : "% of Transitions",
                                                                                                                        "direction": "Direction"
                                                                                                                        },
                )
    fig.update_xaxes(range=[min_value, max_value] ,dtick=max_value/20)
    fig.update_yaxes(range=[0, 1],tick0=0, dtick=0.2)
    fig.update_layout(title=f"Transition CDF - {line_chart_title}", font_family="Arial") 
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns([1,1])
    with col1:
        fig = px.histogram(hand_in_or_last_to_switch, x="Transition Time (s)", nbins=3,text_auto=True, height=350, template="none")
        fig.update_layout(xaxis_title="Transition Duration (sec)", yaxis_title="Switch Count")
        fig.update_layout(title=f"Transition Duration {histogram_title_1}", font_family="Arial",) 
        fig.layout.bargap = .01
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.histogram(hand_out_or_switch_to_first, x="Transition Time (s)", nbins=3,text_auto=True, height=350,template="none")
        fig.update_layout(xaxis_title="Transition Duration (sec)", yaxis_title="Switch Count")
        fig.update_layout(title=f"Transition Duration {histogram_title_2}", font_family="Arial",) 
        fig.layout.bargap = .01
        st.plotly_chart(fig, use_container_width=True)

def display_header_section():
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.image('images/charter.jpg', width=150)
    with col4:
        st.image('images/CNX_Catalyst_Logo.png')

    with st.expander('', expanded=True):
        col1, col2, col3 = st.columns([1,1.5,1])

        with col1:
            st.header("Prometheus Log Parser")
        with col2:
            box_slot = st.empty()
