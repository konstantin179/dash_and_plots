from dash import Dash, html, dcc, Input, Output, dash_table
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import requests
from postgres import DB, db_connection_string
from datetime import date, timedelta

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
#         }
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
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
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
    dcc.Store(id='revenue_bar_store'),
    html.Div(
        dcc.Graph(id='revenue_bar'),
    ),
    dcc.Store(id='impressions_to_cart_conversion_store'),
    dcc.Store(id='cart_to_order_conversion_store'),
    dcc.Store(id='impressions_to_order_conversion_store'),
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
              "sku_name_list": sku_name_list}
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
            req.raise_for_status()
            data = req.json()
            # print(data)
            titles_n_values[title] = list(data.values())[0]
        except requests.exceptions.RequestException as e:
            print(f"Request error to /api/v1/dashboard/{title}: " + str(e))
            titles_n_values[title] = ""
    values = [f"{value}" for value in titles_n_values.values()]
    return values


def get_graph_params(time_unit, start_date, end_date, seller_name, category_names,
                     all_category_names, brand_names, all_brand_names):
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
    params = {"period": time_unit,
              "api_id_list": api_id_list,
              "brand_name_list": brand_name_list,
              "category_name_list": category_name_list,
              "date_from": start_date,
              "date_to": end_date}
    return params


@app.callback(
    Output('revenue_bar_store', 'data'),
    Input('d_w_m_selection', 'value'),
    Input('date_picker', 'start_date'),
    Input('date_picker', 'end_date'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def revenue_bar_plot(time_unit, start_date, end_date, seller_name, category_names,
                     all_category_names, brand_names, all_brand_names):
    if not (category_names and all_category_names and brand_names and all_brand_names):
        raise PreventUpdate
    params = get_graph_params(time_unit, start_date, end_date, seller_name, category_names,
                              all_category_names, brand_names, all_brand_names)
    print("params:", params)
    try:
        print(f"try to get data to revenue_bar_plot")
        req = requests.post(f"http://62.84.124.35:5051/api/v1/graphs/revenue", json=params)
        req.raise_for_status()
        data = req.json()
        if data['result'] == 'No data available':
            print(f"Response from /api/v1/graphs/revenue with params={params}: No data available")
            raise PreventUpdate
        dff = pd.DataFrame(data=data)
        return dff.to_json(date_format='iso', orient='split')
    except requests.exceptions.RequestException as e:
        print(f"Request error to /api/v1/graphs/revenue: " + str(e))
        raise PreventUpdate


@app.callback(
    Output('revenue_bar', 'figure'),
    Input('revenue_bar_store', 'data'))
def update_revenue_bar(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    dff = pd.read_json(jsonified_data, orient='split')
    fig = px.bar(dff, x="date", y="result", title="Динамика суммы заказов")
    return fig


@app.callback(
    Output('impressions_to_cart_conversion_store', 'data'),
    Input('d_w_m_selection', 'value'),
    Input('date_picker', 'start_date'),
    Input('date_picker', 'end_date'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def impressions_to_cart_conversion_plot(time_unit, start_date, end_date, seller_name, category_names,
                                        all_category_names, brand_names, all_brand_names):
    if not (category_names and all_category_names and brand_names and all_brand_names):
        raise PreventUpdate
    params = get_graph_params(time_unit, start_date, end_date, seller_name, category_names,
                              all_category_names, brand_names, all_brand_names)
    try:
        print(f"try to get data to impressions_to_cart_conversion")
        req = requests.post(f"http://62.84.124.35:5051/api/v1/graphs/impressions_to_cart_conversion", json=params)
        req.raise_for_status()
        data = req.json()
        if data['result'] == 'No data available':
            print(f"Response from /api/v1/graphs/impressions_to_cart_conversion with params={params}:",
                  f"No data available")
            raise PreventUpdate
        dff = pd.DataFrame(data=data)
        return dff.to_json(date_format='iso', orient='split')
    except requests.exceptions.RequestException as e:
        print(f"Request error to /api/v1/graphs/impressions_to_cart_conversion: " + str(e))
        raise PreventUpdate


@app.callback(
    Output('impressions_to_cart_conversion', 'figure'),
    Input('impressions_to_cart_conversion_store', 'data'))
def update_impressions_to_cart_conversion(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    dff = pd.read_json(jsonified_data, orient='split')
    fig = px.line(dff, x="date", y="result", title="Конверсия из показа в корзину, %")
    return fig


@app.callback(
    Output('cart_to_order_conversion_store', 'data'),
    Input('d_w_m_selection', 'value'),
    Input('date_picker', 'start_date'),
    Input('date_picker', 'end_date'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def cart_to_order_conversion_plot(time_unit, start_date, end_date, seller_name, category_names,
                                  all_category_names, brand_names, all_brand_names):
    if not (category_names and all_category_names and brand_names and all_brand_names):
        raise PreventUpdate
    params = get_graph_params(time_unit, start_date, end_date, seller_name, category_names,
                              all_category_names, brand_names, all_brand_names)
    try:
        print(f"try to get data to cart_to_order_conversion")
        req = requests.post(f"http://62.84.124.35:5051/api/v1/graphs/cart_to_order_conversion", json=params)
        req.raise_for_status()
        data = req.json()
        if data['result'] == 'No data available':
            print(f"Response from /api/v1/graphs/cart_to_order_conversion with params={params}:",
                  f"No data available")
            raise PreventUpdate
        dff = pd.DataFrame(data=data)
        return dff.to_json(date_format='iso', orient='split')
    except requests.exceptions.RequestException as e:
        print(f"Request error to /api/v1/graphs/cart_to_order_conversion: " + str(e))
        raise PreventUpdate


@app.callback(
    Output('cart_to_order_conversion', 'figure'),
    Input('cart_to_order_conversion_store', 'data'))
def update_cart_to_order_conversion(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    dff = pd.read_json(jsonified_data, orient='split')
    fig = px.line(dff, x="date", y="result", title="Конверсия из корзины в заказ, %")
    return fig


@app.callback(
    Output('impressions_to_order_conversion_store', 'data'),
    Input('d_w_m_selection', 'value'),
    Input('date_picker', 'start_date'),
    Input('date_picker', 'end_date'),
    Input('seller_name_dropdown', 'value'),
    Input('category_dropdown', 'value'),
    Input('category_dropdown', 'options'),
    Input('brand_dropdown', 'value'),
    Input('brand_dropdown', 'options'), )
def impressions_to_order_conversion_plot(time_unit, start_date, end_date, seller_name, category_names,
                                         all_category_names, brand_names, all_brand_names):
    if not (category_names and all_category_names and brand_names and all_brand_names):
        raise PreventUpdate
    params = get_graph_params(time_unit, start_date, end_date, seller_name, category_names,
                              all_category_names, brand_names, all_brand_names)
    try:
        print(f"try to get data to impressions_to_order_conversion")
        req = requests.post(f"http://62.84.124.35:5051/api/v1/graphs/impressions_to_order_conversion", json=params)
        req.raise_for_status()
        data = req.json()
        if data['result'] == 'No data available':
            print(f"Response from /api/v1/graphs/impressions_to_order_conversion with params={params}:",
                  f"No data available")
            raise PreventUpdate
        dff = pd.DataFrame(data=data)
        return dff.to_json(date_format='iso', orient='split')
    except requests.exceptions.RequestException as e:
        print(f"Request error to /api/v1/graphs/impressions_to_order_conversion: " + str(e))
        raise PreventUpdate


@app.callback(
    Output('impressions_to_order_conversion', 'figure'),
    Input('impressions_to_order_conversion_store', 'data'))
def update_impressions_to_order_conversion(jsonified_data):
    if jsonified_data is None:
        raise PreventUpdate
    dff = pd.read_json(jsonified_data, orient='split')
    fig = px.line(dff, x="date", y="result", title="Конверсия из показа в заказ, %")
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


if __name__ == '__main__':
    app.run_server(debug=True)
