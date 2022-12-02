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
# colors = {
#     'background': '#F5F5F5',
#     'text': '#000',
# }
# font = {"family": "Inter",
#         "size": 14,
#         "color": "#000",
# }
app.layout = html.Div([
    html.Div(children=[
        html.Label('Даты'),
        dcc.DatePickerRange(
            id='date_picker',
            start_date_placeholder_text="ДД.ММ.ГГГГ",
            end_date_placeholder_text="ДД.ММ.ГГГГ",
            display_format="DD.MM.YYYY",
            month_format="MMMM YYYY",
            first_day_of_week=1,
            clearable=True,
            show_outside_days=True,
        ),
    ]
    ),
    html.Div(children=[
        html.Label('Продавец'),
        dcc.Dropdown(options=seller_names,
                     value=seller_names[0],
                     id='seller_name_dropdown', ),
    ],
    ),
    html.Div(children=[
        html.Label('Категории'),
        dcc.Dropdown(id='category_dropdown', multi=True, ),
    ],
    ),
    html.Div(children=[
        html.Label('Бренд'),
        dcc.Dropdown(id='brand_dropdown', multi=True, ),
    ],
    ),
    html.Div(children=[
        html.Label('Товар'),
        dcc.Dropdown(id='product_dropdown', multi=True, ),
    ],
    ),
    html.Label('Выбор день, неделя или месяц'),
    dcc.RadioItems(options=[{'label': 'День', 'value': 'day'},
                            {'label': 'Неделя', 'value': 'week'},
                            {'label': 'Месяц', 'value': 'month'},
                            ],
                   value='day',
                   id="d_w_m_selection",
                   inline=True,
                   ),

    html.Label('Сумма заказов, руб.'),
    html.Div([
        html.Label('Последние 7 дней'),
        html.Div(id='revenue_seven_days'),
        html.Label('Предыдущие 7 дней'),
        html.Div(id='revenue_pre_seven_days'),
    ],
    ),
    html.Label('Количество заказов, шт.'),
    html.Div([
        html.Label('Последние 7 дней'),
        html.Div(id='order_units_seven_days'),
        html.Label('Предыдущие 7 дней'),
        html.Div(id='order_units_pre_seven_days'),
    ],
    ),
    html.Label('AIV, руб.'),
    html.Div([
        html.Label('Последние 7 дней'),
        html.Div(id='aiv_seven_days'),
        html.Label('Предыдущие 7 дней'),
        html.Div(id='aiv_pre_seven_days'),
    ],
    ),

    dcc.Graph(id='revenue_bar'),
    html.Div(children=[
        dcc.Graph(id='impressions_to_cart_conversion'),
        dcc.Graph(id='cart_to_order_conversion'),
        dcc.Graph(id='impressions_to_order_conversion'),
    ],
    ),

])


def get_params_lists(seller_name, category_names, all_category_names,
                     brand_names, all_brand_names, sku_names, all_sku_names):
    api_id = df.loc[df["api_name"] == seller_name]["api_id"].iloc[0]
    api_id_list = [api_id, ]
    if "Выбрать все" in category_names:
        all_category_names.remove("Выбрать все")
        category_name_list = all_category_names
    else:
        category_name_list = category_names
    if "Выбрать все" in brand_names:
        all_brand_names.remove("Выбрать все")
        brand_name_list = all_brand_names
    else:
        brand_name_list = brand_names
    if "Выбрать все" in sku_names:
        all_sku_names.remove("Выбрать все")
        sku_name_list = all_sku_names
    else:
        sku_name_list = sku_names
    params = {"api_id_list": api_id_list,
              "brand_name_list": brand_name_list,
              "category_name_list": category_name_list,
              "sku_name_list": sku_name_list,
              }
    return params


@app.callback(
    Output('revenue_seven_days', 'children'),
    Output('revenue_pre_seven_days', 'children'),
    Output('order_units_seven_days', 'children'),
    Output('order_units_pre_seven_days', 'children'),
    Output('aiv_seven_days', 'children'),
    Output('aiv_pre_seven_days', 'children'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'),
    Input('product_dropdown', 'value'),
    Input('product_dropdown', 'options'), )
def values_seven_n_pre_seven_days(seller_name, category_names, all_category_names,
                                  brand_names, all_brand_names, sku_names, all_sku_names):
    if not (category_names and all_category_names and brand_names
            and all_brand_names and sku_names and all_sku_names):
        return "", "", "", "", "", ""
    params = get_params_lists(seller_name, category_names, all_category_names,
                              brand_names, all_brand_names, sku_names, all_sku_names)
    # print(params)
    titles = ['revenue_seven_days', 'revenue_pre_seven_days', 'order_units_seven_days',
              'order_units_pre_seven_days', 'aiv_seven_days', 'aiv_pre_seven_days']
    titles_n_values = {}
    for title in titles:
        try:
            # print(f"try to get data to {title}")
            req = requests.post(f"http://62.84.124.35:5051/api/v1/dashboard/{title}", json=params)
            data = req.json()
            # print(data)
            if req.status_code == 422:
                titles_n_values[title] = ""
            else:
                titles_n_values[title] = list(data.values())[0]
        except requests.exceptions.RequestException as e:
            print(f"Request error to /api/v1/dashboard/{title}: " + str(e))
            titles_n_values[title] = ""
    values = [f"{value}" for value in titles_n_values.values()]
    return values


@app.callback(
    Output('revenue_bar', 'figure'),
    Input('d_w_m_selection', 'value'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def revenue_bar_plot(d_w_m, seller_name, category_names, all_category_names, brand_names, all_brand_names):
    # if not (category_names and all_category_names and brand_names and all_brand_names):
    #     return None
    # params_lists = get_params_lists(seller_name, category_names, all_category_names,
    #                                 brand_names, all_brand_names, [], [])
    # params = {"api_id": params_lists['api_id_list'][0],
    #           "brand_id": params_lists['brand_name_list'][0],
    #           "category_id": params_lists['category_name_list'][0],
    #           }
    # print("params:", params)
    # try:
    #     print(f"try to get data to revenue_bar_plot")
    #     req = requests.get(f"http://62.84.124.35:5051/api/v1/day/graphs/revenue_rub", params=params)
    #     print(req.status_code)
    #     print(req.content)
    #     data = req.json()
    #     print(data)
    #     if req.status_code == 422:
    #         dff = pd.DataFrame.from_dict(data)
    #     else:
    #         return None
    # except requests.exceptions.RequestException as e:
    #     print(f"Request error to /api/v1/{d_w_m}/graphs/revenue_rub: " + str(e))
    #     return None
    dff = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
    fig = px.bar(dff, x="col1", y="col2", title="Динамика суммы заказов")
    return fig


@app.callback(
    Output('impressions_to_cart_conversion', 'figure'),
    Input('d_w_m_selection', 'value'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def revenue_bar_plot(d_w_m, seller_name, category_names, all_category_names, brand_names, all_brand_names):
    dff = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
    fig = px.line(dff, x="col1", y="col2", title="Конверсия из показа в корзину, %")
    return fig


@app.callback(
    Output('cart_to_order_conversion', 'figure'),
    Input('d_w_m_selection', 'value'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def revenue_bar_plot(d_w_m, seller_name, category_names, all_category_names, brand_names, all_brand_names):
    dff = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
    fig = px.line(dff, x="col1", y="col2", title="Конверсия из корзины в заказ, %")
    return fig


@app.callback(
    Output('impressions_to_order_conversion', 'figure'),
    Input('d_w_m_selection', 'value'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def revenue_bar_plot(d_w_m, seller_name, category_names, all_category_names, brand_names, all_brand_names):
    dff = pd.DataFrame(data={'col1': [1, 2], 'col2': [3, 4]})
    fig = px.line(dff, x="col1", y="col2", title="Конверсия из показа в заказ, %")
    return fig


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
    app.run_server(debug=True)
