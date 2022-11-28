from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import dash_pivottable
import requests
import os
from dotenv import load_dotenv


load_dotenv()
headers = {"Accept": "application/json",
          "Api-id": os.getenv("API_ID"),
          "Brand-id": os.getenv("BRAND_ID"),
          "Category-id": os.getenv("CATEGORY_ID"), }
url = os.getenv("API_URL")
req = requests.get(url, headers=headers)
data = req.json()
df = pd.DataFrame.from_dict(data)

app = Dash(__name__)

colors = {
    'background': '#F5F5F5',
    'text': '#000',
}
font = {"family": "Inter",
        "size": 14,
        "color": "#000",
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
                        font=font, ),
        style_header=dict(backgroundColor=colors['background']),
        style_data=dict(backgroundColor=colors['background']),

    ),
    html.H2(children='Line plot'),
    dcc.Dropdown(options=['session_view', 'hits_view', 'adv_view_all', 'hits_tocart', 'revenue',
                          'ordered_units', 'cancellations', 'returns', 'cpm', 'cpo'],
                 value='session_view',
                 id='dropdown_columns',
                 style=dict(font=font, ),
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
