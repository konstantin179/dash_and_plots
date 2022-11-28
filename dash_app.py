from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import dash_pivottable
# import requests
# import os
# from dotenv import load_dotenv


# load_dotenv()
# headers = {"Accept": "application/json",
#           "Api-id": os.getenv("API_ID"),
#           "Brand-id": os.getenv("BRAND_ID"),
#           "Category-id": os.getenv("CATEGORY_ID"), }
# req = requests.get("http://62.84.124.35:5051/api/v1/week/functions/main_pg_fullgraph", headers=headers)
# data = req.json()
data = {'y': [2022, 2022, 2022, 2022, 2022, 2022, 2022, 2022, 2022, 2022, 2022, 2022, 2022, 2022],
        'wk': [34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47],
        'session_view': [0.0, 0.0, 47156.0, 46753.0, 5716.0, 10220.0, 20909.0, 23193.0, 17908.0,
                         12733.0, 19749.0, 24192.0, 21073.0, 9913.0],
        'hits_view': [0.0, 0.0, 98057.0, 93697.0, 7899.0, 13069.0, 30948.0, 34904.0, 25751.0, 16438.0,
                      25153.0, 30891.0, 27385.0, 12639.0],
        'adv_view_all': [0.0, 292.0, 12763.0, 34233.0, 765.0, 785.0, 3360.0, 3352.0, 2559.0,
                         0.0, 0.0, 0.0, 5.0, 0.0],
        'hits_tocart': [0.0, 0.0, 114.0, 66.0, 16.0, 12.0, 51.0, 45.0, 48.0, 44.0, 85.0, 62.0, 82.0, 19.0],
        'revenue': [0.0, 0.0, 14196.0, 13180.0, 6450.0, 3084.0, 11607.0, 15738.0, 12671.0, 8788.0,
                    12491.0, 25290.0, 13984.0, 6269.0],
        'ordered_units': [0.0, 0.0, 6.0, 13.0, 5.0, 2.0, 10.0, 12.0, 10.0, 6.0, 9.0, 20.0, 10.0, 3.0],
        'cancellations': [0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 1.0],
        'returns': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 2.0, 0.0, 0.0, 0.0, 0.0],
        'cpm': [0.0, 0.0, 76329.17785644531, 105793.49517822266, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        'cpo': [0.0, 0.0, 76.32917785644531, 105.79349517822266, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]}

df = pd.DataFrame.from_dict(data)

app = Dash(__name__)

colors = {
    'background': '#F5F5F5',
    'text': '#000',
}
font = {"family": "Inter",
        "size": 14,
        "color":  "#000",
}

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='Dash capabilities',
        style={'textAlign': 'center'},
    ),
    html.H2(children='Simple interactive table'),
    html.P(id='table_out'),
    dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df.columns],
        data=df.to_dict('records'),
        style_table={'height': 400},  # defaults to 500
        page_size=10,
        style_cell=dict(textAlign='left',
                        font=font,),
        style_header=dict(backgroundColor=colors['background']),
        style_data=dict(backgroundColor=colors['background']),

    ),
    html.H2(children='Line plot'),
    dcc.Dropdown(options=['session_view', 'hits_view', 'adv_view_all', 'hits_tocart', 'revenue',
                          'ordered_units', 'cancellations', 'returns', 'cpm', 'cpo'],
                 value='session_view',
                 id='dropdown_columns',
                 style=dict(font=font,),
    ),
    dcc.Graph(id='line_plot'),
    html.H2(children='Pivot table'),
    html.Div(
        dash_pivottable.PivotTable(
            data=[list(df.columns)] + df.values.tolist(),
            cols=["hits_view"],
            rows=["wk"],
            vals=["hits_tocart"],
        ),
    ),
])


@app.callback(
    Output('table_out', 'children'),
    Input('table', 'active_cell'))
def output_active_cell_info(active_cell):
    if active_cell:
        cell_data = df.iloc[active_cell['row']][active_cell['column_id']]
        return f"Data: \"{cell_data}\" from table cell: {active_cell}"
    return "Click the table"


@app.callback(
    Output("line_plot", "figure"),
    Input("dropdown_columns", "value"))
def update_table_columns(column_name):
    fig = px.line(df, x='wk', y=column_name, title=f'{column_name} by week')
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font=font
    )
    fig.update_xaxes(zerolinewidth=1, zerolinecolor='#8c8c8c', showgrid=True, gridwidth=1, gridcolor='#8c8c8c')
    fig.update_yaxes(zerolinecolor='#8c8c8c', showgrid=True, gridwidth=1, gridcolor='#8c8c8c')
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)
