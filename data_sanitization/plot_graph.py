import pandas as pd
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt
import plotly.graph_objects as go

sns.set_style('white')

def input_data_summary(array_info, df_in):
    df = df_in.drop('P', level='curve' ,axis=1).copy()
    input_data_summary = pd.DataFrame(index=array_info['input_name'].values,
                                      columns=['Missing/Bad', 'Available'])
    for i, j in array_info.index:
        input_data_summary['Missing/Bad'].loc[i + '-' + j] = (round(
            (df[i][j].isna().sum().mean() /
             len(df)) * 100, 2))
    input_data_summary['Available'] = 100 - input_data_summary['Missing/Bad']

    # Creating Stacked Bar plot using data
    fig = go.Figure(data=[go.Bar(name='Available', x=input_data_summary.index,
                                 y=input_data_summary['Available'],
                                 marker_color='#D9D9D9'       #'#FFA500'  ##'#3CB371'
                                 ),
                          go.Bar(name='Missing/Outlier',
                                 x=input_data_summary.index,
                                 y=input_data_summary['Missing/Bad'],
                                 marker_color='#333333'      ##'#F5F5F5'  ###FF6A6A' ##abe5f0'
                                 )
                          ],
                    layout=go.Layout(
                        title="Input Level Data Quality Analysis",
                        xaxis=dict(title="Inputs"), yaxis=dict(title="Data %"),
                        template='plotly_white',
                        barmode="stack",
                        legend=dict(orientation="h")))

    return fig


def plot_data_analysis_graph(inverter_data, inverter_data_sanitized, inv_name, variable,ylabel, title):
    import plotly.express as px
    df = pd.DataFrame()
    inverter, mppt = inv_name.split('-')[0],inv_name.split('-')[1]
    input_name = inv_name + '-' + variable
    df['Pre Sanitation'] = inverter_data[inverter][mppt][variable]
    df['Post Sanitation'] = inverter_data_sanitized[input_name]

    fig = go.Figure()
    dash_obj1 = go.Scatter(x=df.index, y=df['Pre Sanitation'], name = 'Pre Sanitation', line = dict(color='#333333',dash='dash'))
    dash_obj2 = go.Scatter(x=df.index, y=df['Post Sanitation'], name = 'Post Sanitation', line = dict(color='#D9D9D9'))
    fig.update_layout(title= title,
                      xaxis_title='Datetime',
                      yaxis_title=ylabel,
                      template='plotly_white', 
                      legend=dict(orientation="h"))
    fig.add_trace(dash_obj1)
    fig.add_trace(dash_obj2)
    return fig


def meteo_data_graph(meteo_data):

    df = pd.DataFrame()
    df['Irr'] = meteo_data['Inv01']["M1"]['G']
    df['Tmod'] = meteo_data['Inv01']['M1']['Tamb']
    df = df[df['Irr'] > 10]

    sns.set_style('white')
    sns.set_palette("Blues_r")
    fig4 = sns.jointplot(x='Tmod', y='Irr', data=df, kind='hex', height=8.5)
    plt.xlabel('Module Temperature (in degrees)', weight='bold', fontsize=12)
    plt.ylabel('Irradiance (W/m2)', weight='bold', fontsize=12)
    #     fig4.show()

    return fig4


def boxplots(df_in):
    from plotly.subplots import make_subplots
    df = df_in['Inv01']['M1'].copy()
    fig5 = make_subplots(rows=1, cols=2)
    fig5.add_trace(go.Box(y=df['G'], name='Irradiance',
                    marker_color = 'indianred'),row=1, col=1)
    fig5.add_trace(go.Box(y=df['Tmod'], name = 'Module Temperature',
                    marker_color = 'lightseagreen'),row=1, col=2)
    fig5.update_layout(template='plotly_white',autosize=False,
                  width=950, height=500)
    return fig5

