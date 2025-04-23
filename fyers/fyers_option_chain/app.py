# app.py
import dash
from dash import dcc, html, Output, Input, no_update
import plotly.graph_objects as go
from datetime import datetime
from data_fetcher import FyersAPI
import pandas as pd
import json
import logging

from graphs.db_manager import init_db, store_option_chain_data, get_data_from_db, reset_db
from graphs.config_manager import (
    init_config_table,
    get_all_configured_symbols,
    get_symbol_config,
    update_symbol_config
)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

# In-memory cache: symbol -> list of {'timestamp','chain'}
history_cache = {}
MAX_CACHE_SIZE = 500


# Load stock master CSV
df_stocks = pd.read_csv(r'Fyers-API-Financial-Repo/fyers/fyers_option_chain/matched_stocks.csv')
stock_options = [
    {'label': row.Stock_name, 'value': row.fyers_symbol}
    for _, row in df_stocks.iterrows()
]

# Fyers API setup
client_id    = "K731S35ZOK"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb0NKV2lXdEtLdVlGMjRFR0dhUXN5dHVWcEdPUG1fRnAzdk9tWjE0UENTbnlVdGlqU0YzMVpmVVRBUWNuQUZpWWpUVjFyVjBpaWh2RGo3aG1weDcxUWlBbEJBNGU3QU9Pa0FqS0RHNHRHWWJoLXEwND0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ1NDU0NjAwLCJpYXQiOjE3NDUzOTMwNTgsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NTM5MzA1OCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.7SJ77r9haSpq4-pZbXaGJwn4rj09vznrRE94N1hlgfI"
fyers_api    = FyersAPI(client_id, access_token)

# Defaults
# Defaults
DEFAULT_SYMBOL      = "NSE:HDFCBANK-EQ"
DEFAULT_STRIKECOUNT = 10

# ─── Track every symbol the user has activated ────────────────────────────────
tracked_symbols = set([DEFAULT_SYMBOL])
# ─── Initialization: DB, config table, seed first point ───────────────────────
def initialize():
    init_db()
    init_config_table()

    # 1) fetch chain for default symbol
    init_cfg = fyers_api.fetch_option_chain_data(
        DEFAULT_SYMBOL, DEFAULT_STRIKECOUNT
    )
    if not init_cfg or 'expiryData' not in init_cfg:
        logging.error("Could not load default symbol data.")
        return

    default_expiry = init_cfg['expiryData'][0]['expiry']
    update_symbol_config(DEFAULT_SYMBOL,
                         DEFAULT_STRIKECOUNT,
                         default_expiry)

    # 2) seed first data‐point into cache & DB
    if 'optionsChain' in init_cfg:
        ts = datetime.now().isoformat()
        history_cache.setdefault(DEFAULT_SYMBOL, []).append({
            'timestamp': ts,
            'chain':     init_cfg['optionsChain']
        })
        store_option_chain_data(
            DEFAULT_SYMBOL, ts,
            json.dumps(init_cfg['optionsChain']),
            DEFAULT_STRIKECOUNT, default_expiry
        )

    # 3) load any previously persisted symbols
    for sym in get_all_configured_symbols():
        rows = get_data_from_db(sym)
        history_cache[sym] = rows[-MAX_CACHE_SIZE:]

initialize()

# ─── Helpers ──────────────────────────────────────────────────────────────────
def parse_datetime(dt):
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt)
        except ValueError:
            return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.%f")
    return dt

def filter_data(x_list, y_list, selected_date):
    xf, yf = [], []
    for x, y in zip(x_list, y_list):
        dt = parse_datetime(x)
        if dt.date().isoformat() == selected_date:
            xf.append(dt)
            yf.append(y)
    return xf, yf

def generate_oi_figure(plot_data, symbol):
    fig = go.Figure([
        go.Scatter(
            x=plot_data['x'], y=plot_data['call'],
            mode='lines', name='Call OI',
            hovertemplate="Time: %{x|%H:%M:%S}<br>Call OI: %{y:,}"
        ),
        go.Scatter(
            x=plot_data['x'], y=plot_data['put'],
            mode='lines', name='Put OI',
            hovertemplate="Time: %{x|%H:%M:%S}<br>Put OI: %{y:,}"
        )
    ])
    fig.update_layout(
        title=f"Real-time Open Interest (OI) for {symbol}",
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey'),
        yaxis=dict(title="Open Interest",
                   showgrid=True, gridcolor='lightgrey')
    )
    return fig

def generate_change_figure(plot_data, symbol):
    fig = go.Figure([
        go.Scatter(
            x=plot_data['x'], y=plot_data['call_chg'],
            mode='lines', name='Δ Call OI',
            hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Call OI: %{y:,}"
        ),
        go.Scatter(
            x=plot_data['x'], y=plot_data['put_chg'],
            mode='lines', name='Δ Put OI',
            hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Put OI: %{y:,}"
        )
    ])
    fig.update_layout(
        title=f"Real-time Δ Open Interest (OI) for {symbol}",
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey'),
        yaxis=dict(title="Change in OI",
                   showgrid=True, gridcolor='lightgrey')
    )
    return fig

# ─── Dash App & Layout ───────────────────────────────────────────────────────
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Real-time OI Data"

app.layout = html.Div([
    # Title
    html.H1(
        "Real-time Open Interest (OI) Data",
        style={'textAlign': 'center', 'marginBottom': '20px'}
    ),

    # Controls row
    html.Div([
        html.Div([
            html.Label("Stock"),
            dcc.Dropdown(
                id='stock-dropdown',
                options=stock_options,
                value=DEFAULT_SYMBOL,
                clearable=False,
                searchable=True,
                style={'width': '250px'}
            )
        ]),
        html.Div([
            html.Label("Strike Count"),
            dcc.Dropdown(
                id='strikecount-dropdown',
                options=[{'label': i, 'value': i}
                         for i in [1, 5, 8, 10, 15, 20, 25]],
                value=DEFAULT_STRIKECOUNT,
                clearable=False,
                style={'width': '120px'}
            )
        ]),
        html.Div([
            html.Label("Expiry"),
            dcc.Dropdown(
                id='expiry-dropdown',
                options=[],
                value=None,
                clearable=False,
                style={'width': '150px'}
            )
        ]),
    ], style={
        'display': 'flex',
        'gap': '30px',
        'justifyContent': 'center',
        'marginBottom': '20px'
    }),

    # Strike‐range & date picker row
    html.Div([
        html.Div([
            html.Label("Strike Range"),
            dcc.RangeSlider(
                id='strike-range-slider',
                min=0, max=0, step=None, marks={}, value=[0, 0],
                tooltip={'always_visible': True, 'placement': 'bottom'},
                allowCross=False, pushable=1
            )
        ], style={'flex': '1', 'marginRight': '20px'}),
        html.Div([
            html.Label("Select Date"),
            dcc.DatePickerSingle(
                id='date-picker',
                date=datetime.now().date(),
                display_format='YYYY-MM-DD'
            )
        ]),
    ], style={
        'display': 'flex',
        'alignItems': 'center',
        'gap': '20px',
        'marginBottom': '30px'
    }),

    # Full‐screen overlay spinner (hidden by default)
    html.Div(
        dcc.Loading(
            id="overlay-spinner",
            type="circle",
            children=html.Div(id="overlay-content")
        ),
        id="overlay",
        style={
            "position": "fixed",
            "top": 0, "left": 0,
            "width": "100%", "height": "100%",
            "backgroundColor": "rgba(255,255,255,0.7)",
            "display": "none",
            "alignItems": "center",
            "justifyContent": "center",
            "zIndex": 9999
        }
    ),

    # Graphs
    dcc.Graph(id='oi-graph'),
    dcc.Graph(id='change-graph'),

    # Interval + hidden divs for callbacks
    dcc.Interval(id='interval-component', interval=3000, n_intervals=0),
    html.Div(id='config-dummy', style={'display': 'none'}),
    html.Div(id='fetch-dummy',  style={'display': 'none'}),
])
# ─── Callbacks ────────────────────────────────────────────────────────────────

@app.callback(
    Output('stock-dropdown','options'),
    Input('stock-dropdown','search_value')
)
def update_stock_options(search_value):
    opts = stock_options
    if search_value:
        opts = [o for o in stock_options
                if o['label'].lower().startswith(search_value.lower())]
    return opts

@app.callback(
    [Output('expiry-dropdown','options'),
     Output('expiry-dropdown','value')],
    [Input('stock-dropdown','value'),
     Input('strikecount-dropdown','value')]
)
def update_expiry_dropdown(symbol, strikecount):
    data = fyers_api.fetch_option_chain_data(symbol, strikecount)
    if not data or 'expiryData' not in data:
        return [], None
    choices = [{'label': e['date'], 'value': e['expiry']}
               for e in data['expiryData']]
    return choices, choices[0]['value']

@app.callback(
    [Output('strike-range-slider','min'),
     Output('strike-range-slider','max'),
     Output('strike-range-slider','marks'),
     Output('strike-range-slider','value')],
    [Input('expiry-dropdown','value'),
     Input('stock-dropdown','value'),
     Input('strikecount-dropdown','value')]
)
def update_strike_slider(expiry, symbol, strikecount):
    data = fyers_api.fetch_option_chain_data(symbol,
                                             strikecount,
                                             expiry)
    if not data or 'optionsChain' not in data:
        return no_update, no_update, no_update, no_update
    strikes = sorted({
        opt['strike_price']
        for opt in data['optionsChain']
        if opt.get('strike_price', 0) > 0
    })
    marks = {s: str(s) for s in strikes}
    return strikes[0], strikes[-1], marks, [strikes[0], strikes[-1]]

@app.callback(
    Output('fetch-dummy','children'),
     Input('interval-component','n_intervals'),
    #   Input('stock-dropdown','value'),
    #   Input('strikecount-dropdown','value'),
    #   Input('expiry-dropdown','value') ]
)
def fetch_and_store(n):
     """
     Every tick, fetch for every symbol we've ever activated,
     so their history_cache keeps growing in the background.
     """
     timestamp = datetime.now().isoformat()
# -    for symbol in get_all_configured_symbols():
     for symbol in tracked_symbols:
         cfg = get_symbol_config(symbol)
         if not cfg:
             continue
         try:
             data = fyers_api.fetch_option_chain_data(
                 symbol, cfg['strikecount'], cfg['expiry']
             )
         except Exception:
             logging.exception(f"Fetch failed for {symbol}")
             continue
         if not data or 'optionsChain' not in data:
             continue

         # append & trim
         history_cache.setdefault(symbol, []).append({
             'timestamp': timestamp,
             'chain':     data['optionsChain']
         })
         if len(history_cache[symbol]) > MAX_CACHE_SIZE:
             history_cache[symbol].pop(0)

         # persist
         store_option_chain_data(
             symbol, timestamp,
             json.dumps(data['optionsChain']),
             cfg['strikecount'], cfg['expiry']
         )

         logging.debug(f"[fetch_and_store] {symbol} → "
                       f"{len(history_cache[symbol])} points")

     return ""  # dummy output

@app.callback(
    Output('config-dummy','children'),
    [Input('stock-dropdown','value'),
     Input('strikecount-dropdown','value'),
     Input('expiry-dropdown','value')]
)
def update_config(symbol, strikecount, expiry):
    update_symbol_config(symbol, strikecount, expiry)
    tracked_symbols.add(symbol)
    return ""  # dummy output

@app.callback(
    Output('oi-graph','figure'),
    [
     Input('stock-dropdown','value'),
     Input('strike-range-slider','value'),
     Input('date-picker','date'),
     Input('interval-component','n_intervals'),
    ]
)
def update_oi_graph(symbol, strike_range, sel_date, n):
    cache = history_cache.get(symbol, [])
    logging.debug(f"[update_oi_graph] n={n} symbol={symbol}"
                  f" cache_points={len(cache)}")

    if sel_date:
        # filter per‐day
        xs, ys_call = filter_data(
            [e['timestamp'] for e in cache],
            [sum(opt['oi'] for opt in e['chain']
                 if opt['option_type']=='CE'
                 and strike_range[0] <= opt['strike_price'] <= strike_range[1])
             for e in cache],
            sel_date
        )
        _, ys_put = filter_data(
            [e['timestamp'] for e in cache],
            [sum(opt['oi'] for opt in e['chain']
                 if opt['option_type']=='PE'
                 and strike_range[0] <= opt['strike_price'] <= strike_range[1])
             for e in cache],
            sel_date
        )
        xs = [parse_datetime(x) for x in xs]
        plot_data = {'x': xs, 'call': ys_call, 'put': ys_put}
    else:
        # all‐time
        xs = [parse_datetime(e['timestamp']) for e in cache]
        ys_call = [
            sum(opt['oi'] for opt in e['chain']
                if opt['option_type']=='CE'
                and strike_range[0] <= opt['strike_price'] <= strike_range[1])
            for e in cache
        ]
        ys_put = [
            sum(opt['oi'] for opt in e['chain']
                if opt['option_type']=='PE'
                and strike_range[0] <= opt['strike_price'] <= strike_range[1])
            for e in cache
        ]
        plot_data = {'x': xs, 'call': ys_call, 'put': ys_put}

    return generate_oi_figure(plot_data, symbol)

@app.callback(
    Output('change-graph','figure'),
    [
     Input('stock-dropdown','value'),
     Input('strike-range-slider','value'),
     Input('date-picker','date'),
     Input('interval-component','n_intervals'),
    ]
)
def update_change_graph(symbol, strike_range, sel_date, n):
    cache = history_cache.get(symbol, [])
    logging.debug(f"[update_change_graph] n={n} symbol={symbol}"
                  f" cache_points={len(cache)}")

    if sel_date:
        xs, ys_call = filter_data(
            [e['timestamp'] for e in cache],
            [sum(opt.get('oich',0) for opt in e['chain']
                 if opt['option_type']=='CE'
                 and strike_range[0] <= opt['strike_price'] <= strike_range[1])
             for e in cache],
            sel_date
        )
        _, ys_put = filter_data(
            [e['timestamp'] for e in cache],
            [sum(opt.get('oich',0) for opt in e['chain']
                 if opt['option_type']=='PE'
                 and strike_range[0] <= opt['strike_price'] <= strike_range[1])
             for e in cache],
            sel_date
        )
        xs = [parse_datetime(x) for x in xs]
        plot_data = {'x': xs, 'call_chg': ys_call, 'put_chg': ys_put}
    else:
        xs = [parse_datetime(e['timestamp']) for e in cache]
        ys_call = [
            sum(opt.get('oich',0) for opt in e['chain']
                if opt['option_type']=='CE'
                and strike_range[0] <= opt['strike_price'] <= strike_range[1])
            for e in cache
        ]
        ys_put = [
            sum(opt.get('oich',0) for opt in e['chain']
                if opt['option_type']=='PE'
                and strike_range[0] <= opt['strike_price'] <= strike_range[1])
            for e in cache
        ]
        plot_data = {'x': xs, 'call_chg': ys_call, 'put_chg': ys_put}

    return generate_change_figure(plot_data, symbol)

if __name__ == '__main__':
    app.run(debug=True)