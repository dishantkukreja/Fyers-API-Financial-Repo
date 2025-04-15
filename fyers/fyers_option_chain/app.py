# app.py
import dash
from dash import dcc, html, Output, Input, State, callback_context, no_update
import plotly.graph_objects as go
from datetime import datetime
from data_fetcher import FyersAPI
import pandas as pd
import sqlite3
import json
from graphs.db_manager import init_db, reset_db, store_option_chain_data, get_data_from_db
from graphs.config_manager import get_all_configured_symbols, update_symbol_config, get_symbol_config,init_config_table

# ──────────────────────────────────────────────────────────────────────────────
# Load stock master CSV
# ──────────────────────────────────────────────────────────────────────────────
df_stocks = pd.read_csv(r'Fyers-API-Financial-Repo\fyers\fyers_option_chain\NSE_CM.csv')
stock_options = [
    {'label': row.Stock_name, 'value': row.fyers_symbol}
    for _, row in df_stocks.iterrows()
]

# ──────────────────────────────────────────────────────────────────────────────
# Fyers API setup
# ──────────────────────────────────────────────────────────────────────────────
client_id    = "K731S35ZOK"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbl9kMmNMbkhWRVpfSXlnRVBubXdQMkxxcG1KWlU0ckw4SXBlbHZCNXBhSFhaUFJjOHNRdmtnRlV1S2lFMjUxT3l5bWpacXFZV3dMbU5fVmxFa0c3VzZqcHVUeUQxUjNnMEw5eFg2am5sT2FDOWpsQT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ0NzYzNDAwLCJpYXQiOjE3NDQ2OTA1ODgsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NDY5MDU4OCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.-yI0oZaHuqec91nutc83sisBftmYx-VxAfCujlGJ6UE"
fyers_api    = FyersAPI(client_id, access_token)

DEFAULT_SYMBOL = "NSE:NIFTYBANK-INDEX"
DEFAULT_STRIKECOUNT = 10  # Used for initial fetch if needed

# Record the app’s start time to use as the “backdate” for the first snapshot
APP_START_TIME = datetime.now().isoformat()

# Initialize (and clear) the database at app startup.
init_db()
# reset_db()
init_config_table()

# ──────────────────────────────────────────────────────────────────────────────
# Data‑helper Functions (aggregation and date filtering remain unchanged)
# ──────────────────────────────────────────────────────────────────────────────
def parse_datetime(dt):
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt)
        except ValueError:
            return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%f")
    return dt

def filter_data_by_date(x_list, y_list, selected_date):
    filtered_x, filtered_y = [], []
    for x, y in zip(x_list, y_list):
        dt = parse_datetime(x)
        if dt.date().isoformat() == selected_date:
            filtered_x.append(dt)
            filtered_y.append(y)
    return filtered_x, filtered_y

# ──────────────────────────────────────────────────────────────────────────────
# Plot Generators (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
def generate_oi_figure(plot_data, symbol, window: int = None):
    x_all    = [parse_datetime(dt) for dt in plot_data['x_data']]
    call_all = plot_data['call_oi_data']
    put_all  = plot_data['put_oi_data']

    if window:
        x, call, put = x_all[-window:], call_all[-window:], put_all[-window:]
    else:
        x, call, put = x_all, call_all, put_all

    fig = go.Figure([
        go.Scatter(
            x=x, y=call, mode='lines', name='Call OI',
            line=dict(color='blue', width=2),
            hovertemplate="Time: %{x|%H:%M:%S}<br>Call OI: %{y:,}<extra></extra>"
        ),
        go.Scatter(
            x=x, y=put, mode='lines', name='Put OI',
            line=dict(color='red', width=2),
            hovertemplate="Time: %{x|%H:%M:%S}<br>Put OI: %{y:,}<extra></extra>"
        )
    ])
    fig.update_layout(
        title=f"Real‑time Open Interest (OI) for {symbol}",
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible': False}),
        yaxis=dict(title="Open Interest", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

def generate_change_figure(plot_data, symbol, window: int = None):
    x_all      = [parse_datetime(dt) for dt in plot_data['x_data_change']]
    call_all   = plot_data['call_oi_change_data']
    put_all    = plot_data['put_oi_change_data']

    if window:
        x, call, put = x_all[-window:], call_all[-window:], put_all[-window:]
    else:
        x, call, put = x_all, call_all, put_all

    fig = go.Figure([
        go.Scatter(
            x=x, y=call, mode='lines', name='Δ Call OI',
            line=dict(color='blue', width=2),
            hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Call OI: %{y:,}<extra></extra>"
        ),
        go.Scatter(
            x=x, y=put, mode='lines', name='Δ Put OI',
            line=dict(color='red', width=2),
            hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Put OI: %{y:,}<extra></extra>"
        )
    ])
    fig.update_layout(
        title=f"Real‑time Δ Open Interest (OI) for {symbol}",
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible': False}),
        yaxis=dict(title="Change in OI", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# Dash App & Layout
# ──────────────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
app.title = "Real-time OI Data"

app.layout = html.Div([
    html.H1("Real‑time Open Interest (OI) Data",
            style={'textAlign': 'center', 'marginBottom': '30px'}),
    
    # Row 1: Stock selector, Strike Count, Expiry
    html.Div([
        html.Div([
            html.Label("Stock", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='stock-dropdown',
                options=stock_options,
                value=DEFAULT_SYMBOL,
                clearable=False,
                placeholder="Type to search…",
                searchable=True,
                style={'width': '250px'}
            )
        ]),
        html.Div([
            html.Label("Strike Count", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='strikecount-dropdown',
                options=[{'label': str(x), 'value': x} for x in [1, 5, 8, 10, 15, 20, 25, 30, 35]],
                value=DEFAULT_STRIKECOUNT,
                clearable=False,
                style={'width': '120px'}
            )
        ]),
        html.Div([
            html.Label("Expiry", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='expiry-dropdown',
                options=[],
                value=None,
                clearable=False,
                style={'width': '150px'}
            )
        ])
    ], style={'display': 'flex', 'justifyContent': 'center', 'gap': '40px', 'marginBottom': '25px'}),

    # Row 2: Strike Range Slider | Date | Submit
    html.Div([
        html.Div([
            html.Label("Strike Range", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
            dcc.RangeSlider(
                id='strike-range-slider',
                min=0, max=0, step=1, marks={}, value=[0, 0],
                tooltip={'placement': 'bottom', 'always_visible': True},
                allowCross=False, pushable=1, updatemode='mouseup'
            )
        ], style={'flex': '1 1 400px'}),

        html.Div([
            html.Label("Select Date", style={'fontWeight': 'bold'}),
            dcc.DatePickerSingle(
                id='date-picker',
                date=datetime.now().date(),
                display_format='YYYY-MM-DD',
                style={'padding': '6px'}
            )
        ]),

        html.Button("Submit", id='submit-symbol', n_clicks=0,
                    style={'padding': '8px 24px', 'fontSize': '16px'})
    ], style={'display': 'flex', 'alignItems': 'center', 'gap': '40px', 'marginBottom': '40px'}),

    dcc.Graph(id='oi-graph'),
    dcc.Graph(id='change-graph'),

    dcc.Interval(id='interval-component', interval=3*1000, n_intervals=0),

    # Hidden div to trigger data fetch and store (no longer using dcc.Store)
    html.Div(id='dummy-div', style={'display': 'none'})
])

# ──────────────────────────────────────────────────────────────────────────────
# Callbacks
# ──────────────────────────────────────────────────────────────────────────────

# Typeahead for stock-dropdown: filter options on prefix match
@app.callback(
    Output('stock-dropdown', 'options'),
    Input('stock-dropdown', 'search_value')
)
def update_stock_options(search_value):
    if not search_value:
        return stock_options
    sv = search_value.lower()
    return [opt for opt in stock_options if opt['label'].lower().startswith(sv)]

# 1) Populate Expiry dropdown when stock or strike count changes
@app.callback(
    Output('expiry-dropdown', 'options'),
    Output('expiry-dropdown', 'value'),
    Input('submit-symbol', 'n_clicks'),
    State('stock-dropdown', 'value'),
    State('strikecount-dropdown', 'value')
)
def update_expiry_options(nc, fyers_symbol, strikecount):
    resp = fyers_api.fetch_option_chain_data(symbol=fyers_symbol, strikecount=strikecount)
    if resp and 'expiryData' in resp:
        opts = [{'label': e['date'], 'value': e['expiry']} for e in resp['expiryData']]
        return opts, (opts[0]['value'] if opts else None)
    return [], None

# 2) Populate RangeSlider when expiry changes
@app.callback(
    Output('strike-range-slider', 'min'),
    Output('strike-range-slider', 'max'),
    Output('strike-range-slider', 'marks'),
    Output('strike-range-slider', 'value'),
    Input('expiry-dropdown', 'value'),
    State('stock-dropdown', 'value'),
    State('strikecount-dropdown', 'value')
)
def update_strike_slider(expiry, fyers_symbol, strikecount):
    resp = fyers_api.fetch_option_chain_data(
        symbol=fyers_symbol, strikecount=strikecount, expiry=expiry
    )
    if not resp or 'optionsChain' not in resp:
        return no_update, no_update, no_update, no_update

    # only keep positive strike prices
    strikes = sorted({
        opt.get('strike_price', 0)
        for opt in resp['optionsChain']
        if opt.get('strike_price', 0) > 0
    })
    if not strikes:
        return no_update, no_update, no_update, no_update

    marks = {s: str(s) for s in strikes}
    return strikes[0], strikes[-1], marks, [strikes[0], strikes[-1]]

# 3) Fetch data from the API and store it persistently in the local DB.
#    This callback triggers on the interval and the submit button.
#  Global variables to keep track of activated symbols and round-robin index.
# Global variables: activated symbols, round-robin counter, and configuration store.
activated_symbols = []
update_index = 0
# symbol_config = {}  # New dictionary to keep each symbol's configuration

@app.callback(
    Output('dummy-div', 'children'),
    Input('interval-component', 'n_intervals'),
    Input('submit-symbol', 'n_clicks'),
    State('stock-dropdown', 'value'),
    State('strikecount-dropdown', 'value'),
    State('expiry-dropdown', 'value')
)
def fetch_and_store(n_int, n_clicks, active_symbol, strikecount, expiry):
    # First, update (or insert) the active symbol's configuration into the DB.
    update_symbol_config(active_symbol, strikecount, expiry)
    
    # Get all configured symbols from the DB.
    symbols_to_update = get_all_configured_symbols()
    
    for symbol in symbols_to_update:
        # Fetch the configuration for each symbol.
        config = get_symbol_config(symbol)
        if config:
            # Fetch option chain data using the stored configuration.
            resp = fyers_api.fetch_option_chain_data(
                symbol=symbol,
                strikecount=config['strikecount'],
                expiry=config['expiry']
            )
            if resp and 'optionsChain' in resp:
                now_iso = datetime.now().isoformat()
                store_option_chain_data(
                    symbol, now_iso, resp['optionsChain'],
                    config['strikecount'], config['expiry']
                )
    return ""

# 4) Recompute & plot total OI using data from the persistent DB.
@app.callback(
    Output('oi-graph', 'figure'),
    Input('stock-dropdown', 'value'),
    Input('date-picker', 'date'),
    Input('strike-range-slider', 'value'),
    Input('interval-component', 'n_intervals')  # to refresh graph on new data
)
def update_oi_graph(symbol, sel_date, strike_range, n_int):
    low, high = strike_range
    # Get historical data for the symbol from the database
    db_data = get_data_from_db(symbol)
    x_list = db_data['x_data']

    call_ts, put_ts = [], []
    for chain in db_data['chain_history']:
        c = sum(opt.get('oi', 0)
                for opt in chain
                if opt.get('option_type') == 'CE' and low <= opt.get('strike_price', 0) <= high)
        p = sum(opt.get('oi', 0)
                for opt in chain
                if opt.get('option_type') == 'PE' and low <= opt.get('strike_price', 0) <= high)
        call_ts.append(c)
        put_ts.append(p)

    if sel_date:
        x_f, call_f = filter_data_by_date(x_list, call_ts, sel_date)
        _, put_f = filter_data_by_date(x_list, put_ts, sel_date)
        plot_data = {
            'x_data': [dt.isoformat() for dt in x_f],
            'call_oi_data': call_f,
            'put_oi_data': put_f
        }
    else:
        plot_data = {'x_data': x_list, 'call_oi_data': call_ts, 'put_oi_data': put_ts}

    return generate_oi_figure(plot_data, symbol)

# 5) Recompute & plot ΔOI using data from the persistent DB.
@app.callback(
    Output('change-graph', 'figure'),
    Input('stock-dropdown', 'value'),
    Input('date-picker', 'date'),
    Input('strike-range-slider', 'value'),
    Input('interval-component', 'n_intervals')  # to refresh graph on new data
)
def update_change_graph(symbol, sel_date, strike_range, n_int):
    low, high = strike_range
    db_data = get_data_from_db(symbol)
    x_list = db_data['x_data']

    call_chg_ts, put_chg_ts = [], []
    for chain in db_data['chain_history']:
        cchg = sum(opt.get('oich', 0)
                   for opt in chain
                   if opt.get('option_type') == 'CE' and low <= opt.get('strike_price', 0) <= high)
        pchg = sum(opt.get('oich', 0)
                   for opt in chain
                   if opt.get('option_type') == 'PE' and low <= opt.get('strike_price', 0) <= high)
        call_chg_ts.append(cchg)
        put_chg_ts.append(pchg)

    if sel_date:
        x_f, call_f = filter_data_by_date(x_list, call_chg_ts, sel_date)
        _, put_f = filter_data_by_date(x_list, put_chg_ts, sel_date)
        plot_data = {
            'x_data_change': [dt.isoformat() for dt in x_f],
            'call_oi_change_data': call_f,
            'put_oi_change_data': put_f
        }
    else:
        plot_data = {
            'x_data_change': x_list,
            'call_oi_change_data': call_chg_ts,
            'put_oi_change_data': put_chg_ts
        }

    return generate_change_figure(plot_data, symbol)

if __name__ == '__main__':
    app.run(debug=True)
