import dash
from funcs import clean_currency
import pandas as pd
import numpy as np
from dash import dcc, html
import plotly.express as px
from dash.dependencies import Output, Input

# Load original data
df = pd.read_csv('data/transactions.csv')

# Cleaning original data
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Removes Unnamed columns
df['Amount'] = df['Amount'].apply(clean_currency).astype('float')
df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%y')

external_stylesheets = [
    {
        "href": "https://fonts.googleapis.com/css2?"
                "family=Lato:wght@400;700&display=swap",
        "rel": "stylesheet",
    },
]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server
app.title = "Bank Statement Analytics: Understand Your Personal Finances!"

# Create new df with only category and amount columns
cat_amount = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])  # Remove cols
cat_amount = cat_amount.groupby(cat_amount['Category'])['Amount'].sum().to_frame().reset_index()

# Create new df with only two tags:
new_df = df.drop(columns=["Description", "Address", "City/State", "Zip Code", "Country", ])  # Remove cols
new_df['Type'] = np.where(df['Category'].isin(
    ['Car Insurance', 'Car Loan', 'Car Maintenance', 'Electric Bill', 'Gas', 'Gas Bill', 'Groceries',
     'Health Care', 'Housing', 'Internet Bill']), True, False)

new_df['Type'] = new_df['Type'].replace({True: "Necessities", False: "Non-essentials"})

new_df = new_df.groupby(new_df['Type'])['Amount'].sum().to_frame().reset_index()

colors = {'Necessities': '#17B897', 'Non-essentials': '#ff7f0e'}

fig = px.pie(new_df, values='Amount', names='Type', color='Type',
             color_discrete_map=colors, title='Expense Breakdown')

app = dash.Dash(__name__)

app.layout = html.Div(
    children=[
        # HEADER INFORMATION
        html.Div(
            children=[
                html.P(children="🏦", className="header-emoji"),
                html.H1(
                    children="Bank Statement Analytics", className="header-title"
                ),
                html.P(
                    children="Analyze purchase history and behavior",
                    className="header-description",
                ),
            ],
            className="header",
        ),
        # UPLOAD .CSV OR .XLSX FILE
        html.Div(
            children=[
                html.Div(children="", className="menu-title"),
                dcc.Upload(
                    id='upload-data',
                    children=html.Div([
                        'Upload .csv or .xlsx files'
                    ]),
                    style={
                        'width': '15%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                        'margin': '-140px auto 40px auto',
                        'background-color': '#FFFFFF'
                    },
                    # Allow multiple files to be uploaded
                    multiple=True
                ),
                html.Div(id='output-data-upload'),
            ],
            className="upload",
        ),
        html.Div(
            children=[
                # INPUT DROP DOWN FOR TOP RANKED EXPENSES
                html.Div(
                    children=[
                        html.Div(children="Top-Ranked Expenses", className="menu-title"),
                        dcc.Dropdown(
                            id="top_n",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=10,
                            clearable=False,
                            className="dropdown",
                        ),
                    ]
                ),
                # INPUT DROP DOWN FOR BOTTOM RANKED EXPENSES
                html.Div(
                    children=[
                        html.Div(children="Bottom-Ranked Expenses", className="menu-title"),
                        dcc.Dropdown(
                            id="bottom_n",
                            options=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                            value=10,
                            clearable=False,
                            className="dropdown",
                        ),
                    ],
                ),
                # INPUT DATE RANGE
                html.Div(
                    children=[
                        html.Div(
                            children="Date Range", className="menu-title"
                        ),
                        dcc.DatePickerRange(
                            id="date-range",
                            min_date_allowed=df.Date.min().date(),
                            max_date_allowed=df.Date.max().date(),
                            start_date=df.Date.min().date(),
                            end_date=df.Date.max().date(),
                        ),
                    ]
                ),
            ],
            className="menu",
        ),
        html.Div(
            children=[
                # TIME SERIES CHART
                html.Div(
                    children=dcc.Graph(
                        id="line-chart",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                # TOP RANKED EXPENSES BAR CHART
                html.Div(
                    children=dcc.Graph(
                        id="bar-chart-1",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                # BOTTOM RANKED EXPENSES BAR CHART
                html.Div(
                    children=dcc.Graph(
                        id="bar-chart-2",
                        config={"displayModeBar": False},
                    ),
                    className="card",
                ),
                # EXPENSE BREAKDOWN PIE CHART
                html.Div(
                    children=[
                        html.Div(children="", className="menu-title"),
                        dcc.Graph(
                            id='pie-chart',
                            figure=fig,
                            className="card",
                        ),
                    ],
                )
            ],
            className="wrapper",
        ),
    ]
)


@app.callback(
    [Output("line-chart", "figure"), Output("bar-chart-1", "figure"), Output("bar-chart-2", "figure")],
    [

        Input("top_n", "value"),
        Input("bottom_n", "value"),
        Input("date-range", "start_date"),
        Input("date-range", "end_date"),
    ],
)
def update_charts(top_rankings, bottom_rankings, start_date, end_date):
    # nLargest and nSmallest
    cat_amount_top_n = cat_amount.sort_values('Amount', ascending=False).head(top_rankings)  # Top N
    cat_amount_bottom_n = cat_amount.sort_values('Amount', ascending=True).head(bottom_rankings)  # Bottom N

    mask = (
            (df['Date'] >= start_date)
            & (df['Date'] <= end_date)
    )
    dff = df.loc[mask, :]
    line_chart_figure = {
        "data": [
            {
                "x": dff["Date"],
                "y": dff["Amount"],
                "type": "lines",
                "hover-template": "$%{y:.2f}<extra></extra>",
            },
        ],
        "layout": {
            "title": {
                "text": "Transaction Time Series",
                "x": 0.05,
                "xanchor": "left",
            },
            "xaxis": {"fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True, "gridcolor": '#afafae'},
            "colorway": ["#17B897"],
        },
    }

    bar_chart_figure_1 = {
        "data": [
            {
                "x": cat_amount_top_n["Category"],
                "y": cat_amount_top_n["Amount"],
                "type": "bar",
            },
        ],
        "layout": {
            "title": {"text": "Top Expense Categories", "x": 0.05, "xanchor": "left"},
            "xaxis": {"title": "Category", "fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True, "gridcolor": '#afafae'},
            "colorway": ["#17B897"],
        },
    }
    bar_chart_figure_2 = {
        "data": [
            {
                "x": cat_amount_bottom_n["Category"],
                "y": cat_amount_bottom_n["Amount"],
                "type": "bar",
            },
        ],
        "layout": {
            "title": {"text": "Bottom Expense Categories", "x": 0.05, "xanchor": "left"},
            "xaxis": {"title": "Category", "fixedrange": True},
            "yaxis": {"tickprefix": "$", "fixedrange": True, "gridcolor": '#afafae'},
            "colorway": ["#17B897"],
        },
    }
    return line_chart_figure, bar_chart_figure_1, bar_chart_figure_2


if __name__ == "__main__":
    app.run_server(debug=True)
