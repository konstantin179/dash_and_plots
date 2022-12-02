from dash import Dash, html, dcc, Input, Output, dash_table
import plotly.express as px
import pandas as pd
import requests
import os
from dotenv import load_dotenv
from postgres import DB, db_connection_string


load_dotenv()
# params = {"Accept": "application/json",
#           "api_id": os.getenv("API_ID"),
#           "brand_id": os.getenv("BRAND_ID"),
#           "category_id": os.getenv("CATEGORY_ID"), }
# url = os.getenv("API_URL")
# req = requests.get(url, params=params)
# data = req.json()
# print(data)
# df = pd.DataFrame.from_dict(data)
column_names = ["api_id", "api_name", "category_id", "category_name",
                "brand_id", "brand_name", "product_id", "product_name"]
query = f"""SELECT {', '.join(column_names)}
              FROM product_data;"""
with DB(db_connection_string) as db:
    df = db.psql_to_dataframe(query, column_names)
print("Dataframe downloaded")
# Replace None values with "".
df = df.fillna(value="")

app = Dash(__name__)
seller_names = sorted(df["api_name"].unique())
colors = {
    'background': '#F5F5F5',
    'text': '#000',
}
font = {"family": "Inter",
        "size": 14,
        "color": "#000",
}


app.layout = html.Div([
    html.Div([
        html.Div(children=[
            html.Span(
                'Период', 
                className='period-string__text', 
            ),
            dcc.DatePickerRange(
                id='date_picker',
                className='date__selector',
                start_date_placeholder_text="ДД.ММ.ГГГГ",
                end_date_placeholder_text="ДД.ММ.ГГГГ",
                display_format="DD.MM.YYYY",
                month_format="MMMM YYYY",
                first_day_of_week=1,
                clearable=True,
                show_outside_days=True,
                ),
            ],
        ),
        html.Div(children=[
            html.Span('Магазин'),
            dcc.Dropdown(options=seller_names,
                        value=seller_names[0],
                        id='seller_name_dropdown',
                        placeholder=''
                        ),
            ], className='shop_selector selector_wrapper'
        ),
        html.Div(children=[
            html.Span('Категории'),
            dcc.Dropdown(id='category_dropdown', multi=True, placeholder=''),
            ], className='category_selector selector_wrapper'
        ),
        html.Div(children=[
            html.Span('Бренд'),
            dcc.Dropdown(id='brand_dropdown', multi=True, placeholder=''),
            ], className='brand_selector selector_wrapper'
        ),
        html.Div(children=[
            html.Span('Товар'),
            dcc.Dropdown(id='product_dropdown', multi=True, placeholder='', style={'display': 'block', 'visabillity': 'visible'}),
            ], className='product_selector selector_wrapper'
        ),
        html.Div(children=[
            html.Button('Применить',className='use_selector_btn'),
            html.Div(children=[
                html.Span('', className='excel_btn')
            ],className='excel_btn_container')
        ], className='selector_btns_wrapper'
        ),
        # dcc.Graph(id='Graph1'),
        # dcc.Graph(id='line_plot1'),
        # dcc.Graph(id='line_plot2'),
    ], 
    className='period__block',
    )
], 
className='period-string__content',
)


# fig = px.bar(long_df, x="nation", y="count", color="medal", title="Long-Form Input")


@app.callback(
    Output('category_dropdown', 'options'),
    Output('category_dropdown', 'value'),
    Input('seller_name_dropdown', 'value'))
def category_dropdown_options(seller_name):
    category_names = sorted(df.loc[df["api_name"] == seller_name]["category_name"].unique())
    options = ["Выбрать все"] + category_names
    return options, []


@app.callback(
    Output('brand_dropdown', 'options'),
    Output('brand_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'))
def brand_dropdown_options(category_names, all_category_names):
    if not (category_names and all_category_names):
        return [], []
    if "Выбрать все" in category_names:
        all_category_names.remove("Выбрать все")
        brands = sorted(df.loc[df["category_name"].isin(all_category_names)]["brand_name"].unique())
    else:
        brands = sorted(df.loc[df["category_name"].isin(category_names)]["brand_name"].unique())
    options = ["Выбрать все"] + brands
    return options, []


@app.callback(
    Output('product_dropdown', 'options'),
    Output('product_dropdown', 'value'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'))
def product_dropdown_options(brands, all_brands):
    if not (brands and all_brands):
        return [], []
    if "Выбрать все" in brands:
        all_brands.remove("Выбрать все")
        products = sorted(df.loc[df["brand_name"].isin(all_brands)]["product_name"].unique())
    else:
        products = sorted(df.loc[df["brand_name"].isin(brands)]["product_name"].unique())
    options = ["Выбрать все"] + products
    return options, []


# @app.callback(
#     Output("Graph1", "figure"),
#     Input("dropdown_columns", "value"))
# def update_table_columns(column_name):
#     fig = px.line(df, x='wk', y=column_name, title=f'{column_name} by week')
#     # fig.update_layout(
#     #     plot_bgcolor=colors['background'],
#     #     paper_bgcolor=colors['background'],
#     #     font=font
#     # )
#     # fig.update_xaxes(zerolinewidth=1, zerolinecolor='#8c8c8c', showgrid=True, gridwidth=1, gridcolor='#8c8c8c')
#     # fig.update_yaxes(zerolinecolor='#8c8c8c', showgrid=True, gridwidth=1, gridcolor='#8c8c8c')
#     return fig

# @app.callback(
#     Output('table_out', 'children'),
#     Input('table', 'active_cell'))
# def output_active_cell_info(active_cell):
#     if active_cell:
#         cell_data = df.iloc[active_cell['row']][active_cell['column_id']]
#         return f"Data: \"{cell_data}\" from table cell: {active_cell}"
#     return "Click the table"
#
#
# @app.callback(
#     Output("line_plot", "figure"),
#     Input("dropdown_columns", "value"))
# def update_table_columns(column_name):
#     fig = px.line(df, x='wk', y=column_name, title=f'{column_name} by week')
#     fig.update_layout(
#         plot_bgcolor=colors['background'],
#         paper_bgcolor=colors['background'],
#         font=font
#     )
#     fig.update_xaxes(zerolinewidth=1, zerolinecolor='#8c8c8c', showgrid=True, gridwidth=1, gridcolor='#8c8c8c')
#     fig.update_yaxes(zerolinecolor='#8c8c8c', showgrid=True, gridwidth=1, gridcolor='#8c8c8c')
#     return fig


if __name__ == '__main__':
    app.run_server(debug=False)
