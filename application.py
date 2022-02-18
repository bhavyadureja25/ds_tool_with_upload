#!/usr/bin/env python
# coding: utf-8

# In[1]:


"This file contains the data sanitation dashboard app code"
import os
os.environ['KMP_DUPLICATE_LIB_OK']='True'
import base64
import io
import sys
import time
import json
import pathlib
import warnings
import numpy as np
import pandas as pd
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
warnings.filterwarnings("ignore")

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('white')

import dash
from dash import dcc
from dash import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash_extensions import Download
import dash_bootstrap_components as dbc
from dash.dependencies import Input,Output
from dash_extensions.snippets import send_data_frame

external_stylesheets = [dbc.themes.BOOTSTRAP]

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    external_stylesheets=external_stylesheets
)
app.title = "Data Sanitation Tool"

server = app.server
app.config.suppress_callback_exceptions = True

tab_style = {
    'borderTop': '2px solid #ffaf2a',
}

# App libraries
from data_input.read_system_info import gather_inputs
from data_input.read_meteo_data import read_weather_data
from data_input.read_operational_data import read_inverter_data
from data_input.poa_irradiance import get_operational_irradiance

from data_sanitization.utc import get_tz
from data_sanitization.models import predict_missing_data
from data_sanitization.site_location_pvlib import get_site_location
from data_sanitization.clear_sky_irradiance import clearsky_irradiance
from data_sanitization.eliminate_night_values import eliminate_nightvalues
from data_sanitization.filtering import multiindex_irradiance_filter
from data_sanitization.filtering import multiindex_current_filter
from data_sanitization.filtering import multiindex_voltage_filter

# from data_sanitization.plot_graph import plot_data_analysis_graph
# from data_sanitization.plot_graph import input_data_summary
# from data_sanitization.misc_func import fig_to_uri
from data_sanitization.misc_func import data_summary_table


# In[2]:


def input_data_summary(array_info, df_in):
    df = df_in.drop('P', level='curve', axis=1).copy()

    input_data_summary = pd.DataFrame(index=array_info['input_name'].values,
                                      columns=['Missing/Bad', 'Available'])
    for i, j in array_info.index:
        input_data_summary['Missing/Bad'].loc[i + '-' + j] = (
            round((df[i][j].isna().sum().mean() / len(df)) * 100, 2))
    input_data_summary['Available'] = 100 - input_data_summary['Missing/Bad']

    # Creating Stacked Bar plot using data
    fig = go.Figure(data=[go.Bar(name='Available',
                                 x=input_data_summary.index,
                                 y=input_data_summary['Available'],
                                 marker_color='#FF8800'),

                          go.Bar(name='Missing/Outlier',
                                 x=input_data_summary.index,
                                 y=input_data_summary['Missing/Bad'],
                                 marker_color='#636EFA')],

                    layout=go.Layout(xaxis=dict(title="Inputs"),
                                     yaxis=dict(title="Data %"),
                                     template='plotly_white',
                                     barmode="stack",
                                     autosize=False,
                                     width=1000,
                                     height=500))

    fig.update_layout(margin=dict(l=20, r=10, t=20, b=20),
                      hoverlabel=dict(bgcolor="white",
                                      font_size=16,
                                      font_family="Roboto"),
                      legend=dict(orientation="h", yanchor="top",
                                  y=1.02, xanchor="left", x=0.33))

    return fig


def plot_data_analysis_graph(inverter_data, inverter_data_sanitized, inv_name,
                             variable, ylabel, title):
    df = pd.DataFrame()
    inverter, mppt = inv_name.split('-')[0], inv_name.split('-')[1]
    input_name = inv_name + '-' + variable

    df['Pre Sanitation'] = inverter_data[inverter][mppt][variable]
    df['Post Sanitation'] = inverter_data_sanitized[inverter][mppt][variable]

    fig = go.Figure()
    dash_obj1 = go.Scatter(x=df.index,
                           y=df['Pre Sanitation'],
                           name='Pre Sanitation',
                           line=dict(color='#636EFA', dash='dash'))

    dash_obj2 = go.Scatter(x=df.index,
                           y=df['Post Sanitation'],
                           name='Post Sanitation',
                           line=dict(color='#FF8800'))

    fig.update_layout(xaxis_title='Datetime',
                      yaxis_title=ylabel,
                      template='plotly_white', autosize=False,
                      width=1000, height=350,
                      legend=dict(orientation="h", yanchor="top",
                                  y=1.02, xanchor="right", x=0.33))

    fig.add_trace(dash_obj1)
    fig.add_trace(dash_obj2)
    fig.update_layout(margin=dict(l=20, r=20, t=5, b=20))
    return fig


# In[3]:


def fig_to_uri(in_fig, close_all=True, **save_args):
    """
    Save a figure as a URI
    :param in_fig: Input figure.
    :return: str.
    """
    out_img = io.BytesIO()
    in_fig.savefig(out_img, format = 'png', **save_args)
    if close_all:
        in_fig.clf()
        plt.close('all')
    out_img.seek(0)  # rewind file
    encoded = base64.b64encode(out_img.read()).decode("ascii").replace("\n", "")
    return "data:image/png;base64,{}".format(encoded)


# In[4]:


def generate_card_content(card_header,data_type, overall_value, color):
    card_head_style = {'textAlign':'center','fontSize':'100%', 'color': color}
    card_body_style = {'textAlign':'center','fontSize':'300%', 'color':color, 'background-color':'whitesmoke'} 
    card_header = dbc.CardHeader(card_header,style=card_head_style)
    card_body = dbc.CardBody(
        [
            html.H5("{}".format(data_type), className="card-text",
                                        style={'textAlign':'center',"font-weight": "bold",'fontSize':'90%',
                                              'color':color}),
            html.H3("{}".format(overall_value),
                className="card-title",style={'textAlign':'center',"font-weight": "bold",'fontSize':'200%', 'color':color}
            ),
        ]
    )
    card = [card_header,card_body]
    return card

def generate_cards1(data_summary):
    
    total_data = data_summary.loc['Data Points Available']['Values']
    missing = str(data_summary.loc['Missing Data (%)']['Values']) + '%'
    outlier = str(data_summary.loc['Outliers (%)']['Values']) + '%'
    time_reso = data_summary.loc['Temporal Resolution']['Values']
    missing_data = int(data_summary.loc['Missing Data (%)']['Values'])
    outlier_data = int(data_summary.loc['Outliers (%)']['Values'])
    print('###########Inside generate cards 1 - printing #######')
    print(total_data, 'total_data')
    print('only str missing', missing)
    print('only str outlier', outlier)
    print('outlier data:', outlier_data)
    print('missing_data:', missing_data)
    
    if ((100-(missing_data+outlier_data)) > 99.5):
        status ="Superb"
    elif ((100-(missing_data+outlier_data)) > 98) & ((100-(missing_data+outlier_data)) < 99.5):
        status= "Good"
    elif ((100-(missing_data+outlier_data)) > 95) & ((100-(missing_data+outlier_data)) < 98):
        status = "Normal"
    else:
        status='Poor'
    print('####status', status)

    cards = html.Div(
        [
#             html.H4("Data Quality: Pre Data sanitation",
#             style={'textAlign': 'center',
#                    'fontColor':'#333333'}),
            
            dbc.Row(
                [
                    dbc.Col(dbc.Card(generate_card_content(card_header="Pre-Sanitation",data_type='Total',
                                                           overall_value=total_data, color='#1F77B4'), 
                                     inverse=True),md=dict(size=2,offset=2),width="auto"),
                    dbc.Col(dbc.Card(generate_card_content(card_header="Pre-Sanitation",data_type='Missing',
                                                           overall_value=missing,color='#1F77B4'), 
                                     inverse=True),md=dict(size=2),width="auto"),
                    dbc.Col(dbc.Card(generate_card_content(card_header="Pre-Saniattion",data_type='outlier',
                                                           overall_value=outlier,color='#1F77B4'), 
                                     inverse=True),md=dict(size=2),width="auto"),
                    dbc.Col(dbc.Card(generate_card_content(card_header="Pre-Sanitation",data_type='Status',
                                                           overall_value=status,color='#1F77B4'), 
                                     inverse=True),md=dict(size=2),width="auto"),
                ],
                className="mb-6",
            ),
        ],id='card1'
    )
    return cards

def generate_cards2(data_summary):
    
    missing_data_post_sanitation = int(data_summary.loc['missing_data_post_sanitation']['Values'])
    missing = str(data_summary.loc['missing_data_post_sanitation']) + '%'
    total_data = total_data = data_summary.loc['Data Points Available']['Values']
    outlier ='0 %'
    print('Inside generate cards 2 - printing #######')
    print(total_data, 'total_data')
    print('missing_data:', missing)
    print('outlier data:', outlier)

    if ((100-(missing_data_post_sanitation)) > 99.5):
        status ="Superb"
    elif ((100-(missing_data_post_sanitation)) > 98) & ((100-(missing_data_post_sanitation)) < 99.5):
        status= "Good"
    elif ((100-(missing_data_post_sanitation)) > 95) & ((100-(missing_data_post_sanitation)) < 98):
        status = "Normal"
    else:
        status='Poor'
    print('####status', status)
        
    cards = html.Div(
        [
#             html.H4("Data Quality: Post Data sanitation",
#         style={'textAlign': 'center',
#                 'fontColor':'#333333'}),
            dbc.Row(
                [
                    dbc.Col(dbc.Card(generate_card_content("Post-Sanitation","Datapoints",total_data,'#FF8800'), inverse=True),md=dict(size=2,offset=2), width="auto"), #
                    dbc.Col(dbc.Card(generate_card_content("Post-Sanitation","Missing",missing, '#FF8800'), inverse=True), md=dict(size=2), width="auto"), #
                    dbc.Col(dbc.Card(generate_card_content("Post-Sanitation","Outlier",outlier, "#FF8800"), inverse=True), md=dict(size=2), width="auto"),
                    dbc.Col(dbc.Card(generate_card_content("Post-Sanitation","Status",status, "#FF8800"), inverse=True), md=dict(size=2), width="auto"),
                ],
                className="mb-6",
            ),
        ],id='card2'
    )
    return cards


# In[5]:


def page_footer():
    return html.Footer(
        children=["©smarthelio2022"],
        style={'width':'100%', 'color': '#FFFFFF',
               'text-align': 'center', 'position': 'absolute', 
               'background-color': '#737373', 'left': 0,
               'bottom': 0, 'font-family': 'Roboto'}
    )

from dash import html
import base64
image_filename = 'assets/SmartHelio logo-2 (1).png' # replace with your own image
encoded_image = base64.b64encode(open(image_filename, 'rb').read())


search_bar1 = dbc.Row(
    [
        dbc.Col(dbc.NavItem(dbc.NavLink("Home", href="/home",
                                        style={"color":"#FFFFFF", "font-family": "Roboto", 'fontSize':'110%',
                                              'justify':'right'})),
                width="auto"),
        dbc.Col(dbc.NavItem(dbc.NavLink("Data Sanitation", href="/data_sanitation_dashboard",
                                        style={"color":"#FFFFFF", "font-family": "Roboto", 'fontSize':'110%',
                                              'justify':'right'})),
                width="auto"),
        dbc.Col(dbc.NavItem(dbc.NavLink("API Connect", href="#",
                                        style={"color":"#FFFFFF", "font-family": "Roboto",'fontSize':'110%',
                                              'justify':'right'})),
                width="auto"),
        
        dbc.Col(dbc.NavItem(dbc.NavLink("Learn More", href="/learn_more",
                                        style={"color":"#FFFFFF", "font-family": "Roboto",'fontSize':'110%',
                                              'justify':'right'})),
                width="auto"),
        
    ],
    className="g-0 ms-auto flex-nowrap mt-0 mt-md-3",
    align="left",
)

def Navbar():
    return dbc.Navbar(
        dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(
                                src='data:image/png;base64,{}'.format(encoded_image.decode()),
                                height="25px")),
                    ],
                    align="center",
                    className="g-0",
                ),
                href="https://smarthelio.com",
                style={"textDecoration": "none"},
            ),
            search_bar1 
        ]
    ),
    color="#737373",
    dark=True,
    sticky='top',
#     fluid=True,
)


body = dbc.Container(
    [
        html.Br(),
        dbc.Row(
            [
                dbc.Col(html.H2("Welcome to SmartHelio's Data Sanitation Dashboard", style={'font-family':'Roboto'}),
                        width={"size":10,"offset":1.5}, style={'color':'#333333'}),
            ],
            justify="center",
        ),
        dbc.Row(
            [
                dbc.Col(dcc.Markdown(
                    """
                    Data Sanitation dashboard is the only application that helps you get preprocessed and sanitized data of your solar plant 
                    using SmartHelio's proprietary AI based Data Sanitation Algorithm in seconds."
                    """,
                    style={'font-family':'Roboto','text-align':'center'}
                ),
                width={"size":8, "offset":0.6}, 
                style={'color':'#333333'}
                       ),
            ],
            justify="center",
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Img(
                            src='/assets/solar-panel-health-web.jpg', height="360px",
                            style={'padding-left': '200px'}
                        ), 
                    ],
                    md=5
                ),
            ],
        ),
        html.Br(),
        html.Br(),
        html.Div(
            [
                dbc.Button("Contact Us", color="dark",
                           outline=True, href="https://smarthelio.com",
                           external_link=True, style={'font-family': 'Roboto'}
                          ),
            ],
            className="d-grid gap-0 col-1 mx-auto",
        ),
    ],
    className="mt-4",
)

def Homepage():
    layout = html.Div([
        Navbar(),
        body
    ])
    return layout


# In[6]:


# UPLOAD BUTTON
def upload_data_card():
    """
    :return: A Div containing an Upload button
    """
    return html.Div(
        id='upload-data-card',
        children=[
            dcc.Upload(
                id='upload-data',
                children=html.Div([html.Button('Upload or Drag Files', style={'backgroundColor': 'whitesmoke', 
                                                                              'Color': '#333333'})]),
                style={'width': '150%', 'height': '30px',
                       'textAlign': 'center', 'font-family':'Roboto',
                      'border-radius': '8px','padding-right':'280px'},
                # Don't allow multiple files to be uploaded
                multiple=False
            ),
        ]
    )


# LEFT SIDE TAB INFORMATION
def description_card():
    """
    :return: A Div containing dashboard title & descriptions.
    """
    return html.Div(
        id="description-card",
        children=[
        html.H5("SmartHelio", style={'color':'#FF8800',
                                     "font-weight": "bold",
                                    'font-family': 'Roboto',
                                    'fontSize':'150%'}),
            html.H3("Welcome to the Data Sanitation Dashboard", 
                    style={'fontColor':'#FF8800',
                           'font-family': 'Roboto'}),
            html.H6("Get your data sanitized in one click.", 
                    style={'font-family': 'Roboto'}),
        ],
    )

# LOGO ON THE DASHBOARD
def generate_control_card():
    """
    :return: A Div containing controls for graphs.
    """
    return html.Div(
        id="control-card",
        children=[
            html.P(""),
            html.Div(
                id="banner-logo",
                children=[
                    upload_data_card()]),
            html.Br(),
            html.Div(
                id="reset-btn-outer",
                children=html.Button(id="apply-btn", children="Apply",
                                     n_clicks=0),
            ),
        ],
    )


# In[7]:


def generate_modal():
    return html.Div(
        id="markdown",
        className="modal",
        children=(
            html.Div(
                id="markdown-container",
                className="markdown-container",
                children=[
                    html.Div(
                        className="close-container",
                        children=html.Button(
                            "Close",
                            id="markdown_close",
                            n_clicks=0,
                            className="closeButton",
                        ),
                    ),
                    html.Div(
                        className="markdown-text",
                        children=dcc.Markdown(
                            children=(
                                """
                         ***What is this app about?***
                         SmartHelio's Data Sanitation Dashboard is the only application that helps you preprocess
                         and sanitize your solar plant's data in seconds using **SmartHelio's properietary AI based 
                         Data Preprocessing Algorithm**. 
                         
                         ***How does Data sanitation tool work?***
                         Simply upload your data you want to get preprocessed and download your clean and sanitized data in seconds!
                            
                        ***How much time does it take to preprocess the data?***
                         Depending upon the size and quality of your data, it should take about a few minutes.

                        ***Why should you choose SmartHelio's Automated Data Sanitation Tool?***
                         Because we have industry experience and we work one of the the best research instituions in the world
                         such EPFL, HSLU, etc to create our algorithms.
                        
                        **Glossary**
                        ***Data Points:***
                        The total measurements received in the dataset.
                            
                        ***Missing %:*** 
                        It refers to % of the datapoints given as 'NaN' i.e. not a number in the dataset. 
                            
                        ***Outlier %:*** 
                        It refers to % of the datapoints given as very high or very low (or negative) values which degrades the 
                        quality of dataset. 
                            
                        ***Status:*** 
                        It refers to the overall quality of the dataset after taking into the account missing, bad, 
                        and outlier values. 
                        
                        ***Download Sanitized Data:*** 
                        To download the preprocessed and sanitized data in a csv, simply click the "Download 
                        Sanitized Data". 
                        
                        ***Upload Data:*** 
                        This button helps to upload the data which needs to be cleaned and sanitized. 
                        """
                            ),
                            style={'backgroundColor': '#333333','color': '#FFFFFF','font-family': 'Roboto'},
                        ),
                    ),
                ],
            )
        ),
    )


# In[8]:


def deserialize_multiindex_dataframe(dataframe_json: str) -> pd.DataFrame:
    """
    Deserialize the dataframe json into a dataframe object.
    The dataframe json must be generated with DataFrame.to_json(orient="split")
    This function is to address the fact that `pd.read_json()` isn't behaving correctly (yet)
    https://github.com/pandas-dev/pandas/issues/4889
    """
    def convert_index(json_obj):
        to_tuples = [tuple(i) if isinstance(i, list) else i for i in json_obj]
        if all(isinstance(i, list) for i in json_obj):
            return pd.MultiIndex.from_tuples(to_tuples)
        else:
            return pd.Index(to_tuples)
    json_dict = json.loads(dataframe_json)
    columns = convert_index(json_dict['columns'])
    index = convert_index(json_dict['index'])
    dataframe = pd.DataFrame(json_dict["data"], index, columns)
    return dataframe

## Reading the uploaded file 
@app.callback(
    Output('intermediate-value', 'data'),
    [
        Input('upload-data', 'contents'),
        Input('upload-data', 'filename')
    ],
    prevent_initial_call=True
)
def create_data(contents, filename):
    # Starting the timer
    start_time = time.time()
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            array_info, general_info = gather_inputs(
                io.StringIO(decoded.decode('utf-8')))

            inverter_data,data_points = read_inverter_data(
                general_info, io.StringIO(decoded.decode('utf-8')))
            
            meteo_data, irr_df = read_weather_data(
                general_info, io.StringIO(decoded.decode('utf-8')))

        elif 'xls' or 'xlsx' in filename:
            array_info, general_info = gather_inputs(io.BytesIO(decoded))
            print(array_info)
                        
            inverter_data,data_points = read_inverter_data(general_info, io.BytesIO(decoded))
            print(inverter_data)
            print('INVERTER DATA PROCESSED')
            meteo_data,irr_df = read_weather_data(general_info, io.BytesIO(decoded))
            print(meteo_data)
            
    except Exception as e:
        return html.Div(['There was an error processing this file.'])
    
    # converting irradinace GHI to POA 
    meteo_data = get_operational_irradiance(
        meteo_data, general_info, array_info, poa_model='isotropic')
    
    # Data Sanitization- meteo
    meteo_data_filtered = multiindex_irradiance_filter(meteo_data,
                                                       irrad_low=0,
                                                       irrad_high=1200)
    # Clear sky curve
    csky_curve = clearsky_irradiance(times=inverter_data.index, general_info=general_info,
                                          array_info=array_info, convertGHI_toPOA=True)

    tz_str = get_tz(latitude=general_info['lat'], longitude=general_info['long'])
    csky_curve.index = csky_curve.index.tz_localize('UTC').tz_convert(tz_str).tz_localize(None)

    inverter_data_csky = eliminate_nightvalues(inverter_data,
                                               cs_data=csky_curve, threshold=10)
    
    # Checking for % of missing data
    missing_data = round((inverter_data_csky.isna().sum().sum()/inverter_data_csky.size)*100,2)
    print('Missing data for Inverter is {}'.format(missing_data))
    
    # Data Sanitization-inverter
    inverter_data_filtered = multiindex_current_filter(inverter_data_csky, array_info)
    inverter_data_filtered = multiindex_voltage_filter(inverter_data_filtered,
                                                       array_info)
    # % of outliers
    outlier_data = round(((inverter_data_filtered.isna().sum().sum()/
                               inverter_data_csky.isna().sum().sum())),2)
    print('Outliers: ', outlier_data)

    # meteo data - for graph
    csky_curve_meteo = clearsky_irradiance(times=irr_df.index, general_info=general_info,
                                          array_info=array_info, convertGHI_toPOA=True)
    csky_curve_meteo.index = csky_curve_meteo.index.tz_localize('UTC').tz_convert(tz_str).tz_localize(None)
    meteo_data_csky = eliminate_nightvalues(meteo_data_filtered,
                                               cs_data=csky_curve_meteo, threshold=10)
    
        # Timer ends here
    end_time = time.time()
    print('File Execution Time is {} seconds'.format(end_time - start_time))

    if missing_data > 0.5:
        print('\n MISSING DATA FOUND!!')
        print('\n Computing Missing Data using Machine Learning Models')
        inverter_data_sanitized = predict_missing_data(inverter_data_filtered,
                                                       meteo_data_filtered,
                                                       array_info, general_info)
        # converting df into a multi-index df
        colname = [(i, j, z) for i, j, z in [x.split('-') for x in inverter_data_sanitized.columns]]
        inverter_data_sanitized.columns = pd.MultiIndex.from_tuples(colname, names=['ag_level_2', 'ag_level_1', 'curve'])
        inverter_data_sanitized.index.names = ['datetime']

    else:
        inverter_data_sanitized = inverter_data_csky.fillna(method = 'ffill').fillna(method='bfill')
        print('\nData Availability {} %'.format(100 - missing_data))
        print('\n FINAL STATUS : GOOD FOR ANALYSIS')

    inverter_data_sanitized[inverter_data_sanitized<0] = np.nan
    missing_data_post_sanitation = round((inverter_data_sanitized.isna().sum().sum()/inverter_data_csky.size)*100,2)
    
    data_summary = pd.DataFrame(index=['Data Points Available',
                                         'Temporal Resolution', 'Missing Data (%)',
                                         'Outliers (%)', 'missing_data_post_sanitation'], columns=['Values'])

    data_summary.loc['Data Points Available'] = str(data_points/1000) + ' K'
    data_summary.loc['Temporal Resolution'] = str(general_info['inverter_time_resolution']) + ' Mins'
    data_summary.loc['Missing Data (%)'] = missing_data
    data_summary.loc['Outliers (%)'] = outlier_data
    data_summary.loc['missing_data_post_sanitation'] = missing_data_post_sanitation
    data_summary = data_summary.replace(np.nan,0)
    print('Printing data summary in reading files:', data_summary)
    print('#####################')

    print(array_info)
#     converting dataframes into json object
    datasets = {
        'array_info': array_info.to_json(orient='split', date_format='iso'),
        'inv_data': inverter_data.to_json(orient='split', date_format='iso'),
        'inv_data_csky': inverter_data_csky.to_json(orient='split', date_format='iso'),
        'inv_data_sani': inverter_data_sanitized.to_json(orient='split', date_format='iso'),
        'meteo_data': meteo_data.to_json(orient='split', date_format='iso'),
        'irr_df': irr_df.to_json(orient='split', date_format='iso'),
        'meteo_data_csky': meteo_data_csky.to_json(orient='split', date_format='iso'),
        'data_summary': data_summary.to_json(orient='index'),
        'general_info': json.dumps(general_info)
    } 
    
    end_time = time.time()
    print('Timt taken for processing the data: {}'.format(end_time-start_time))
    
    return json.dumps(datasets)


# In[9]:


# DASHBOARD APP LAYOUT

app.layout = html.Div(
    id="app-container",
    children=[
        Navbar(),
#             # Banner
#             html.Div(
#                 id="banner",
#                 className="banner",
#                 children=[
#                     html.A(
#                         html.Img(src=app.get_asset_url("SH_logo.png")),
#                         href="https://smarthelio.com/",
#                     ),
#                     html.A(      
#                         html.Button(
#                             id="learn-more-button", children="Learn more",
#                             n_clicks=0,
#                             style={'background-color': '#D9D9D9','color': '#333333',
#                                    'border-color': '#333333', 'width':'200px',
#                                   'font-family': 'Roboto',  'border-radius': '12px'},
#                         ),
#                     )
#                 ],
#             ),

                # Left column
                html.Div(
                    id="left-column",
                    className="four columns",
                    children=[
                        description_card(),
                        html.Br(),
                        upload_data_card(),
                        html.Br(),
                #                 html.H4('----OR----',style={'font-family': 'Roboto',
#                                        'fontSize':'130%', 'font-weight':'bold'}),

#                 html.Br(),
#                 html.Label('Select a demo plant',style={'font-family':'Roboto', 'font-weight':'bold'}),
#                 dcc.Dropdown(
#                             id='plant-select',
#                             options=[
#                                 {'label': 'Delhi, India', 'value': 'AB'},
#                                 {'label': 'Lausanne, Switzerland', 'value': 'RE'}
#                             ],
#                       style = {'textAlign':'center',
#                                'width':'350px',
#                                'height':'40px',
#                               'border-radius': '8px',
#                               'background-color': 'whitesmoke'}
#                           ),
                    html.Br(),
                    html.Br(),
#                 html.Button("Submit", id="submit-btn",
#                             style={'width':'120px',
#                                    'height':'50px',
#                                    'border-radius': '8px',
#                                    'fontSize':'90%',
#                                       }),
                    html.Br(),
                    html.Br(),
                    html.Button("Download Sanitized Data", id="btn-download-txt",
                                style={'background-color': '#737373','color': '#FFFFFF', 'width':'280px',
                                       'border-radius': '8px',
                                        'fontSize':'85%'}),
                    dcc.Download(id='download_data'),
                ],
            ),
                #Right column
                dcc.Tabs(
                    id="stitching-tabs",
                    value="data-summary-tab",
                    style={'height': '5%'},
                    children=[
                        dcc.Tab(
                            label="Plant Level Data Summary",
                            value="data-summary-tab",
                            selected_style=tab_style,
                            children=[
            #                             html.H4("Plant Level Data Summary",
            #                                     style={'textAlign': 'center',
            #                                            'fontColor':'#333333'}),
                                html.Br(),
                                html.Div(id='data-values-pre'),
                                html.Br(),
                                html.Div(id='data-values-post'),

#                             html.H4("Input Level Data Summary",
#                                      style={'textAlign': 'center',
#                                             'fontColor':'#333333'}),
#                             html.Div(id='input_level_smmary',
#                                      children=[
#                                          dcc.Loading(id="loading-1",
#                                                      children=[dcc.Graph(id='bar_plot_missing',
#                                                                          config= {'displaylogo': False})],
#                                                      type="circle"),]),
                    html.Br(),
                    dbc.Row([
                        dbc.Col(id='card-markdown'),
                    ],
                    ),
                ]
            ),
            dcc.Tab(
                label="Input Level Data Summary",
                value="weather-data-tab",
                selected_style=tab_style,
                children=[
                    html.Br(),
                    html.P("The graph below shows input level pre-data sanitation comparison in terms of data quality i.e. total data points available for anlaysis, missing data points (%), outliers found (%), etc.",
                          style={'font-family': 'Roboto'}),
                    dcc.Loading(id="loading-1",
                                children=[dcc.Graph(id='bar_plot_missing',config= {'displaylogo': False})],
                                type="circle"),
                ],
             ),
            dcc.Tab(
                label="Data Visualization",
                value="sanitized-data-tab",
                selected_style=tab_style,
                children=[
                    html.Br(),
                    html.P("The graphs below helps you visualize how the data has been cleaned and processed. The dark grey curve represents raw data and light grey curve represents processed data post sanitation. The overlap of dark grey and light grey curve represents good data points in the dataset.",
                          style={'font-family': 'Roboto'}),
                    html.Br(),
                    html.Div(
                        id="sanitized_data_tab",
                        children=[
                            html.B("Select Input for Analysis"),
                            html.Div(dcc.Dropdown(id='input-select', persistence=True), id='input-container'),
                            html.Br(),
                            dcc.Loading(
                                id="loading-2",
                                children=[dcc.Graph(id='current_graph',config= {'displaylogo': False})],
                                type="circle"
                            ),
                            dcc.Loading(
                                id="loading-3",
                                children=[dcc.Graph(id='voltage_graph',config= {'displaylogo': False})],
                                type="circle"
                            ),

                            dcc.Loading(
                                id="loading-4",
                                children=[dcc.Graph(id='irradiance_graph',config= {'displaylogo': False})],
                                type="circle"
                            ),
                            html.Br(),
                            html.Br(),
                        ]
                    )]
            ),

        ],
    ),            
    generate_modal(),
    dcc.Store(id='intermediate-value', storage_type = 'session')
])


# In[ ]:


@app.callback(
    Output('input-container', 'children'),
    Input('intermediate-value', 'data'),
    prevent_initial_call=True
)
def update_output(jsonified_cleaned_data):
    datasets = json.loads(jsonified_cleaned_data)
    
    array_info = deserialize_multiindex_dataframe(datasets['array_info'])
    array_info.index.names = ['ag_level_2', 'ag_level_1']
    all_inputs = array_info['input_name'].unique().tolist()

    return dcc.Dropdown(
        id='input-select',
        options = [{'label': i, 'value': i} for i in all_inputs],
        value = all_inputs[0],
        persistence=True,
        persisted_props=['value'],
        persistence_type='session')
        
@app.callback(
    Output('download-btn', 'n_clicks'),
    Input('intermediate-value', 'data'),
)              
def download_data_button(jsonified_cleaned_data):
    
    datasets = json.loads(jsonified_cleaned_data)
    inverter_data_sanitized = deserialize_multiindex_dataframe(datasets['inv_data_sani'])
    inverter_data_sanitized.index = pd.to_datetime(inverter_data_sanitized.index)
    inverter_data_sanitized.columns.names = ['ag_level_2', 'ag_level_1', 'curve']
    inverter_data_sanitized.index.names = ['datetime']
    
    return html.Button("Download Sanitized Data", id="btn-download-txt",
            style={'background-color': '#737373','color': '#FFFFFF', 'width':'280px',
                   'border-radius': '8px',
                    'fontSize':'105%'}),
    dcc.Download(id='download_data')

@app.callback(
    Output('card-markdown', 'children'),
    Input('upload-data', 'n_clicks'),
)
def markdown_text_cards(clicks):
    time.sleep(15)
    return dcc.Markdown(
            children=(
            """
            ##### **Note:**
            ##### 1. The outliers denotes the datapoints removed from the dataset using plant's configuration.
            ##### 2. The missing data is predicted with high accuracy using AI and ML to reduce data loss.
            ##### 3. Data Status : If data availability > 99.5 % then its 'Superb'
            ##### 3.1. If data availability > 98 % & and < 99.5 % then its 'Good'
            ##### 3.2. If data availability > 95 % and < 98 % then its 'Normal' Else 'Poor' 
            """),
            style={'font-family': 'Roboto', 'fontcolor':'#333333', 'fontSize':'80%',
                  'padding': '90px 0'}
            ),

@app.callback(
    Output('bar_plot_missing', 'figure'),
    Input('intermediate-value', 'data'),
)
def bar_plot_graph(jsonified_cleaned_data):
    datasets = json.loads(jsonified_cleaned_data)
    
    array_info = deserialize_multiindex_dataframe(datasets['array_info'])
    array_info.index.names = ['ag_level_2', 'ag_level_1']
    
    inverter_data_csky = deserialize_multiindex_dataframe(datasets['inv_data_csky'])
    inverter_data_csky.index = pd.to_datetime(inverter_data_csky.index)
    inverter_data_csky.columns.names = ['ag_level_2', 'ag_level_1', 'curve']
    inverter_data_csky.index.names = ['datetime']
    
    figure=input_data_summary(array_info=array_info, df_in=inverter_data_csky)
    return figure

@app.callback(
    Output("markdown", "style"),
    [
        Input("learn-more-button", "n_clicks"), 
        Input("markdown_close", "n_clicks")
    ],
)
def update_click_output(button_click, close_click):
    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "learn-more-button":
            return {"display": "block"}

    return {"display": "none"}

@app.callback(
    Output('data-values-pre', 'children'),
    Input('intermediate-value', 'data'),
)
def update_data_summary(jsonified_cleaned_data):

    datasets = json.loads(jsonified_cleaned_data)
    data_summary = pd.read_json(datasets['data_summary'], orient='index')
    print('data summary:',data_summary)
    print('dat_summary_value: ', data_summary.loc['Data Points Available']['Values'])
    return generate_cards1(data_summary)


@app.callback(
    Output('data-values-post', 'children'),
    Input('intermediate-value', 'data'),
)
def update_data_summary(jsonified_cleaned_data):
    datasets = json.loads(jsonified_cleaned_data)
    data_summary = pd.read_json(datasets['data_summary'], orient='index')
    print('data summary:',data_summary)
    print('dat_summary_value: ', data_summary.loc['Data Points Available']['Values'])
    return generate_cards2(data_summary)


@app.callback(
    Output('current_graph', 'figure'),
    Output('voltage_graph', 'figure'),
    Output('irradiance_graph', 'figure'),
    Input('intermediate-value', 'data'),
    Input("input-select", "value"),
)
def update_current_graph(jsonified_cleaned_data, input_name):
    """
    :param input_name:
    :return:
    """
    datasets = json.loads(jsonified_cleaned_data)
    
    inverter_data = deserialize_multiindex_dataframe(datasets['inv_data'])
    inverter_data.index = pd.to_datetime(inverter_data.index)
    inverter_data.columns.names = ['ag_level_2', 'ag_level_1', 'curve']
    inverter_data.index.names = ['datetime']
    print('update_current_graph: ',inverter_data)
    
    inverter_data_sanitized = deserialize_multiindex_dataframe(datasets['inv_data_sani'])
    inverter_data_sanitized.index = pd.to_datetime(inverter_data_sanitized.index)
    inverter_data_sanitized.columns.names = ['ag_level_2', 'ag_level_1', 'curve']
    inverter_data_sanitized.index.names = ['datetime']
    print('update_current_graph: ',inverter_data_sanitized)
    
    irr_df = deserialize_multiindex_dataframe(datasets['irr_df'])
    irr_df.index = pd.to_datetime(irr_df.index)
    irr_df.columns.names = ['ag_level_2', 'ag_level_1', 'curve']
    irr_df.index.names = ['datetime']
    
    meteo_data_csky = deserialize_multiindex_dataframe(datasets['meteo_data_csky'])
    meteo_data_csky.index = pd.to_datetime(meteo_data_csky.index)
    meteo_data_csky.columns.names = ['ag_level_2', 'ag_level_1', 'curve']
    meteo_data_csky.index.names = ['datetime']

    fig1 = plot_data_analysis_graph(inverter_data, inverter_data_sanitized, inv_name=input_name,
                     variable='I', ylabel='Current (A)', title='')
    fig2 = plot_data_analysis_graph(inverter_data, inverter_data_sanitized, inv_name=input_name,
                     variable='V', ylabel='Voltage (V)', title='')
    fig3 = plot_data_analysis_graph(irr_df, meteo_data_csky, inv_name=input_name, variable='G',
                    ylabel='Irradiance (W/m\u00b2)',title='')

    return fig1, fig2, fig3

        
@app.callback(
    Output("download_data", "data"),
    Input('upload-data', 'n_clicks'),
    Input("btn-download-txt", "n_clicks"),
    Input('intermediate-value', 'data'),
    prevent_initial_call=True,
)
def func2(clicks, n_clicks, jsonified_cleaned_data):
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

    if 'btn-download-txt' in changed_id:
        datasets = json.loads(jsonified_cleaned_data)
        inverter_data_sanitized = deserialize_multiindex_dataframe(datasets['inv_data_sani'])
        inverter_data_sanitized.index = pd.to_datetime(inverter_data_sanitized.index)#, origin = 'unix', unit = 'ms')
        inverter_data_sanitized.columns.names = ['ag_level_2', 'ag_level_1', 'curve']
        inverter_data_sanitized.index.names = ['datetime']
        
    return dcc.send_data_frame(inverter_data_sanitized.to_csv,
                               "sanitized_data.csv")


###########################################
# # Page layout

# app.layout = html.Div([
#     dcc.Location(id = 'url', refresh = False),
#     html.Div(id = 'page-content')
# ])


# @app.callback(
#     Output('page-content', 'children'),
#     Input('url', 'pathname')
# )
# def display_page(pathname):
#     if pathname == '/connected_sites':
#         return app_main()
#     elif pathname == '/data_sanitation_dashboard':
#         return data_app()
#     elif pathname == '/learn_more':
#         return learn_more()
#     else:
#         return Homepage()
    

#Run the server
if __name__ == "__main__":
    app.run_server(debug=False,port=8080)


# In[ ]:


######################################################################################################################

