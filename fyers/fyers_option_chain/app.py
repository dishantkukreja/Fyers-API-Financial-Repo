# app.py
import dash
from dash import dcc, html, Output, Input, State, no_update
import plotly.graph_objects as go
from datetime import datetime
from data_fetcher import FyersAPI
import pandas as pd
import json
from graphs.db_manager import init_db, store_option_chain_data, get_data_from_db
from graphs.config_manager import get_all_configured_symbols, update_symbol_config, init_config_table
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s')

# In-memory cache: symbol -> list of {'timestamp','chain'}
history_cache = {}
MAX_CACHE_SIZE = 500  # max points to keep in memory per symbol

# Load stock master CSV
df_stocks = pd.read_csv(r'Fyers-API-Financial-Repo/fyers/fyers_option_chain/matched_stocks.csv')
stock_options = [
    {'label': row.Stock_name, 'value': row.fyers_symbol}
    for _, row in df_stocks.iterrows()
]

# Fyers API setup
client_id    = "K731S35ZOK"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb0NHVXltcDM0VmkwVExVdWVMalM5WllDSmVPVml6ekJodE1KTnQ5ZVdoR0lPaUVIdWVOVzZQd2xlQ0VyNUF0T1NMZGxzN1EtTFF1TVRSYkRWSktRMnRjWEJ1eFpfWHM5YTJhRHFJTG04bE5UOXVaUT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ1NDU0NjAwLCJpYXQiOjE3NDUzODA2NTgsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NTM4MDY1OCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.Mmi8lfx91WOfXwhZe40c1IvWiPD2DcWW06M3mWYgnoM"
fyers_api    = FyersAPI(client_id, access_token)

# Defaults
DEFAULT_SYMBOL = "NSE:HDFCBANK-EQ"
DEFAULT_STRIKECOUNT = 10

# Initialize DB, config, and load historic data
def initialize():
    init_db()
    init_config_table()
    # Ensure default symbol configured
    init_cfg = fyers_api.fetch_option_chain_data(DEFAULT_SYMBOL, DEFAULT_STRIKECOUNT)
    if init_cfg and init_cfg.get('expiryData'):
        default_expiry = init_cfg['expiryData'][0]['expiry']
        update_symbol_config(DEFAULT_SYMBOL, DEFAULT_STRIKECOUNT, default_expiry)
    # Load persisted history from DB for all configured symbols
    for sym in get_all_configured_symbols():
        rows = get_data_from_db(sym)
        # Keep only recent MAX_CACHE_SIZE points in memory
        history_cache[sym] = rows[-MAX_CACHE_SIZE:]
initialize()

# Helpers
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

# Plot Generators
def generate_oi_figure(plot_data, symbol):
    fig = go.Figure([
        go.Scatter(x=plot_data['x'], y=plot_data['call'], mode='lines', name='Call OI',
                   hovertemplate="Time: %{x|%H:%M:%S}<br>Call OI: %{y:,}<extra></extra>"),
        go.Scatter(x=plot_data['x'], y=plot_data['put'], mode='lines', name='Put OI',
                   hovertemplate="Time: %{x|%H:%M:%S}<br>Put OI: %{y:,}<extra></extra>")
    ])
    fig.update_layout(
        title=f"Real‑time Open Interest (OI) for {symbol}",
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible': False}),
        yaxis=dict(title="Open Interest", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

def generate_change_figure(plot_data, symbol):
    fig = go.Figure([
        go.Scatter(x=plot_data['x'], y=plot_data['call_chg'], mode='lines', name='Δ Call OI',
                   hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Call OI: %{y:,}<extra></extra>"),
        go.Scatter(x=plot_data['x'], y=plot_data['put_chg'], mode='lines', name='Δ Put OI',
                   hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Put OI: %{y:,}<extra></extra>")
    ])
    fig.update_layout(
        title=f"Real‑time Δ Open Interest (OI) for {symbol}",
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible': False}),
        yaxis=dict(title="Change in OI", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

# Dash App & Layout
app = dash.Dash(__name__)
app.title = "Real-time OI Data"
app.layout = html.Div([
    html.H1("Real‑time Open Interest (OI) Data", style={'textAlign':'center','marginBottom':'20px'}),
    html.Div([
        html.Div([html.Label("Stock"),
                  dcc.Dropdown(id='stock-dropdown', options=stock_options, value=DEFAULT_SYMBOL,
                               clearable=False, searchable=True, style={'width':'250px'})]),
        html.Div([html.Label("Strike Count"),
                  dcc.Dropdown(id='strikecount-dropdown', options=[{'label':i,'value':i} for i in [1,5,8,10,15,20,25]],
                               value=DEFAULT_STRIKECOUNT, clearable=False, style={'width':'120px'})]),
        html.Div([html.Label("Expiry"),
                  dcc.Dropdown(id='expiry-dropdown', options=[], value=None, clearable=False, style={'width':'150px'})])
    ], style={'display':'flex','gap':'30px','justifyContent':'center','marginBottom':'20px'}),
    html.Div([
        html.Div([html.Label("Strike Range"),
                  dcc.RangeSlider(id='strike-range-slider', min=0, max=0, step=None, marks={}, value=[0,0],
                                  tooltip={'always_visible':True,'placement':'bottom'}, allowCross=False, pushable=1)],
                  style={'flex':'1','marginRight':'20px'}),
        html.Div([html.Label("Select Date"),
                  dcc.DatePickerSingle(id='date-picker', date=datetime.now().date(),
                                      display_format='YYYY-MM-DD')])
    ], style={'display':'flex','alignItems':'center','gap':'20px','marginBottom':'30px'}),
    dcc.Graph(id='oi-graph'),
    dcc.Graph(id='change-graph'),
    dcc.Interval(id='interval-component', interval=3000, n_intervals=0),
    html.Div(id='dummy-div', style={'display':'none'})
])

# Callbacks
@app.callback(
    Output('stock-dropdown','options'),
    Input('stock-dropdown','search_value')
)
def update_stock_options(search_value):
    opts = stock_options
    if search_value:
        opts = [o for o in stock_options if o['label'].lower().startswith(search_value.lower())]
    return opts

@app.callback(
    [Output('expiry-dropdown','options'), Output('expiry-dropdown','value')],
    [Input('stock-dropdown','value'), Input('strikecount-dropdown','value')]
)
def update_expiry_dropdown(symbol, strikecount):
    data = fyers_api.fetch_option_chain_data(symbol, strikecount)
    if not data or 'expiryData' not in data:
        return [], None
    choices = [{'label':e['date'],'value':e['expiry']} for e in data['expiryData']]
    return choices, choices[0]['value']

@app.callback(
    [Output('strike-range-slider','min'), Output('strike-range-slider','max'),
     Output('strike-range-slider','marks'), Output('strike-range-slider','value')],
    [Input('expiry-dropdown','value'), Input('stock-dropdown','value'), Input('strikecount-dropdown','value')]
)
def update_strike_slider(expiry, symbol, strikecount):
    data = fyers_api.fetch_option_chain_data(symbol, strikecount, expiry)
    if not data or 'optionsChain' not in data:
        return no_update, no_update, no_update, no_update
    strikes = sorted({opt['strike_price'] for opt in data['optionsChain'] if opt.get('strike_price',0)>0})
    marks = {s: str(s) for s in strikes}
    return strikes[0], strikes[-1], marks, [strikes[0], strikes[-1]]

@app.callback(
    Output('dummy-div','children'),
    [Input('interval-component','n_intervals'),
     Input('stock-dropdown','value'), Input('strikecount-dropdown','value'), Input('expiry-dropdown','value')]
)
def fetch_and_store(n, symbol, strikecount, expiry):
    # always set a timestamp to return
    timestamp = datetime.now().isoformat()
    if not symbol:
        return no_update
    update_symbol_config(symbol, strikecount, expiry)
    data = fyers_api.fetch_option_chain_data(symbol, strikecount, expiry)
    if data and 'optionsChain' in data:
        history_cache.setdefault(symbol, []).append({'timestamp':timestamp,'chain':data['optionsChain']})
        if len(history_cache[symbol]) > MAX_CACHE_SIZE:
            history_cache[symbol].pop(0)
        store_option_chain_data(symbol, timestamp, json.dumps(data['optionsChain']), strikecount, expiry)
    return timestamp

@app.callback(
    Output('oi-graph','figure'),
    [Input('stock-dropdown','value'), Input('strike-range-slider','value'),
     Input('date-picker','date'), Input('dummy-div','children')]
)
def update_oi_graph(symbol, strike_range, sel_date, _):
    if symbol not in history_cache:
        history_cache[symbol] = get_data_from_db(symbol)[-MAX_CACHE_SIZE:]
    low, high = strike_range
    entries = history_cache[symbol]
    x, call, put = [], [], []
    for e in entries:
        ts, chain = e['timestamp'], e['chain']
        c = sum(o.get('oi',0) for o in chain if o['option_type']=='CE' and low<=o['strike_price']<=high)
        p = sum(o.get('oi',0) for o in chain if o['option_type']=='PE' and low<=o['strike_price']<=high)
        x.append(ts); call.append(c); put.append(p)
    if sel_date:
        x_dt, call = filter_data(x, call, sel_date)
        _, put = filter_data(x, put, sel_date)
        x = x_dt
    else:
        x = [parse_datetime(ts) for ts in x]
    return generate_oi_figure({'x':x,'call':call,'put':put}, symbol)

@app.callback(
    Output('change-graph','figure'),
    [Input('stock-dropdown','value'), Input('strike-range-slider','value'),
     Input('date-picker','date'), Input('dummy-div','children')]
)
def update_change_graph(symbol, strike_range, sel_date, _):
    if symbol not in history_cache:
        history_cache[symbol] = get_data_from_db(symbol)[-MAX_CACHE_SIZE:]
    low, high = strike_range
    entries = history_cache[symbol]
    x, cchg, pchg = [], [], []
    for e in entries:
        ts, chain = e['timestamp'], e['chain']
        cc = sum(o.get('oich',0) for o in chain if o['option_type']=='CE' and low<=o['strike_price']<=high)
        pc = sum(o.get('oich',0) for o in chain if o['option_type']=='PE' and low<=o['strike_price']<=high)
        x.append(ts); cchg.append(cc); pchg.append(pc)
    if sel_date:
        x_dt, cchg = filter_data(x, cchg, sel_date)
        _, pchg = filter_data(x, pchg, sel_date)
        x = x_dt
    else:
        x = [parse_datetime(ts) for ts in x]
    return generate_change_figure({'x':x,'call_chg':cchg,'put_chg':pchg}, symbol)

if __name__ == '__main__':
    app.run(debug=True)