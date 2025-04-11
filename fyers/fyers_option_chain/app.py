# app.py
import dash
from dash import dcc, html, Output, Input, State, callback_context, no_update
import plotly.graph_objects as go
from datetime import datetime
from data_fetcher import FyersAPI
import pandas as pd
import sqlite3
import json

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
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbi1PUFpxUXdIVFloYlBLM191Z1dsWHFKdGFkazZuRm1Qay11SzItWnRtcW51aWpFZHVGeXYtcmVyOEwyU1RNaVdhdlFSdWtJWWFibkVLOTRmWjBoRGsxbEtUSWVrTmFWaWVxTGE5dURZa2RlQ2RkRT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ0NDE3ODAwLCJpYXQiOjE3NDQzNjQ1MDUsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NDM2NDUwNSwic3ViIjoiYWNjZXNzX3Rva2VuIn0.18U3uGyCYpOPmiuQr4MK1TBr-dHDyG0YuNUwwl0waG0"
fyers_api    = FyersAPI(client_id, access_token)

DEFAULT_SYMBOL = "NSE:NIFTYBANK-INDEX"
DEFAULT_STRIKECOUNT = 10  # Used for initial fetch if needed

# Record the app’s start time to use as the “backdate” for the first snapshot
APP_START_TIME = datetime.now().isoformat()

# ──────────────────────────────────────────────────────────────────────────────
# SQLite Database Helpers
# ──────────────────────────────────────────────────────────────────────────────
DB_FILENAME = "option_chain.db"

def init_db():
    """Initializes the SQLite database and creates the table if necessary."""
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS option_chain_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            timestamp TEXT,
            option_chain TEXT,
            strikecount INTEGER,
            expiry TEXT
        )
    ''')
    conn.commit()
    conn.close()

def reset_db():
    """Clear any existing records so that each app run starts fresh."""
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute("DELETE FROM option_chain_data")
    conn.commit()
    conn.close()

def store_option_chain_data(symbol, timestamp, option_chain, strikecount, expiry):
    """
    Inserts a new record into the database.
    The option_chain is stored as a JSON string.
    """
    conn = sqlite3.connect(DB_FILENAME)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO option_chain_data (symbol, timestamp, option_chain, strikecount, expiry)
        VALUES (?, ?, ?, ?, ?)
    ''', (symbol, timestamp, json.dumps(option_chain), strikecount, expiry))
    conn.commit()
    conn.close()

def get_data_from_db(symbol):
    """
    Retrieves all records from the DB for the given symbol.
    Returns a dict with keys:
       'x_data': list of timestamps (as ISO strings)
       'chain_history': list of option chain data (as Python objects)
    """
    conn = sqlite3.connect(DB_FILENAME)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('''
        SELECT timestamp, option_chain FROM option_chain_data
        WHERE symbol = ?
        ORDER BY timestamp ASC
    ''', (symbol,))
    rows = cur.fetchall()
    conn.close()

    x_data = []
    chain_history = []
    for row in rows:
        x_data.append(row["timestamp"])
        try:
            chain = json.loads(row["option_chain"])
        except Exception:
            chain = []
        chain_history.append(chain)
    return {'x_data': x_data, 'chain_history': chain_history}

# Initialize (and clear) the database at app startup.
init_db()
reset_db()

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
symbol_config = {}  # New dictionary to keep each symbol's configuration

@app.callback(
    Output('dummy-div', 'children'),
    Input('interval-component', 'n_intervals'),
    Input('submit-symbol', 'n_clicks'),
    State('stock-dropdown', 'value'),
    State('strikecount-dropdown', 'value'),
    State('expiry-dropdown', 'value')
)
def fetch_and_store(n_int, n_clicks, active_symbol, strikecount, expiry):
    global activated_symbols, update_index, symbol_config
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    # Update the configuration for the currently active symbol.
    symbol_config[active_symbol] = (strikecount, expiry)

    # Retrieve any previously stored data for the active symbol.
    db_data = get_data_from_db(active_symbol)
    
    # --- Handle "Submit" trigger for new/updated active symbol ---
    if trigger_id == 'submit-symbol':
        if active_symbol not in activated_symbols:
            activated_symbols.append(active_symbol)
        if not db_data['x_data']:
            # For a new symbol, immediately fetch and backdate the first snapshot.
            resp = fyers_api.fetch_option_chain_data(
                symbol=active_symbol,
                strikecount=strikecount,
                expiry=expiry
            )
            if resp and 'optionsChain' in resp:
                store_option_chain_data(active_symbol, APP_START_TIME, resp['optionsChain'], strikecount, expiry)
        else:
            # If the configuration changed while active, fetch an immediate update.
            resp = fyers_api.fetch_option_chain_data(
                symbol=active_symbol,
                strikecount=strikecount,
                expiry=expiry
            )
            if resp and 'optionsChain' in resp:
                now_iso = datetime.now().isoformat()
                store_option_chain_data(active_symbol, now_iso, resp['optionsChain'], strikecount, expiry)
    
    # --- Always update data for the currently active symbol ---
    resp = fyers_api.fetch_option_chain_data(
        symbol=active_symbol,
        strikecount=strikecount,
        expiry=expiry
    )
    if resp and 'optionsChain' in resp:
        now_iso = datetime.now().isoformat()
        store_option_chain_data(active_symbol, now_iso, resp['optionsChain'], strikecount, expiry)
    
    # --- Round-Robin update for inactive (activated) symbols ---
    other_symbols = [s for s in activated_symbols if s != active_symbol]
    if other_symbols:
        symbol_to_update = other_symbols[update_index % len(other_symbols)]
        update_index += 1
        
        # Retrieve the stored configuration from our global dictionary.
        config = symbol_config.get(symbol_to_update)
        if config:
            used_strike, used_expiry = config
            resp_other = fyers_api.fetch_option_chain_data(
                symbol=symbol_to_update,
                strikecount=used_strike,
                expiry=used_expiry
            )
            if resp_other and 'optionsChain' in resp_other:
                now_iso = datetime.now().isoformat()
                store_option_chain_data(symbol_to_update, now_iso, resp_other['optionsChain'], used_strike, used_expiry)
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
