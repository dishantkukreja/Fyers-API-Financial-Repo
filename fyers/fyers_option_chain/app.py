# app.py
import dash
from dash import dcc, html, Output, Input, State, callback_context, no_update
import dash as _dash  # for no_update
import plotly.graph_objects as go
from datetime import datetime
from data_fetcher import FyersAPI

# ──────────────────────────────────────────────────────────────────────────────
# Fyers API setup
# ──────────────────────────────────────────────────────────────────────────────
client_id    = "K731S35ZOK"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbjlRbHk5MF9JcElIQmVCMlZ4bHNRa0RUNS1wYXY0dVNVWEJiZzVSdGFVT2VwVnRmR1dxNHpyYm85MzVmNm1xcXg0SmxjT0c2a2JlYW1FNmZ2X3pxWmVlelQ3RmZIanI1eldydjhCRTRUVzRtNGVLMD0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ0MTU4NjAwLCJpYXQiOjE3NDQxMTE5ODYsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NDExMTk4Niwic3ViIjoiYWNjZXNzX3Rva2VuIn0.R71xOYk7wFd8MnqT42dHj1493tfxtSCz98vyLU8kY4E"
fyers_api    = FyersAPI(client_id, access_token)

DEFAULT_SYMBOL = "NSE:NIFTYBANK-INDEX"

# ──────────────────────────────────────────────────────────────────────────────
# Data store helpers
# ──────────────────────────────────────────────────────────────────────────────
def create_initial_data():
    return {
        'current_symbol': DEFAULT_SYMBOL,
        'symbols_data': {
            DEFAULT_SYMBOL: {
                'x_data': [],          # timestamps
                'chain_history': []    # list of optionsChain snapshots
            }
        }
    }

def reset_symbol_data(data, symbol):
    data['symbols_data'][symbol] = {
        'x_data': [],
        'chain_history': []
    }
    data['current_symbol'] = symbol
    return data

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

def fetch_and_append_data(data, symbol, strikecount, expiry):
    """
    Fetches the full optionsChain and appends it (plus timestamp)
    to our in‑memory history.
    """
    symbol_data = data['symbols_data'].setdefault(symbol, {
        'x_data': [], 'chain_history': []
    })

    resp = fyers_api.fetch_option_chain_data(
        symbol=symbol,
        strikecount=strikecount,
        expiry=expiry
    )
    if resp and 'optionsChain' in resp:
        now_iso = datetime.now().isoformat()
        symbol_data['x_data'].append(now_iso)
        symbol_data['chain_history'].append(resp['optionsChain'])
        data['symbols_data'][symbol] = symbol_data

    return data

# ──────────────────────────────────────────────────────────────────────────────
# Plot generators (unchanged)
# ──────────────────────────────────────────────────────────────────────────────
def generate_oi_figure(plot_data, symbol, window: int = None):
    x_all    = [parse_datetime(dt) for dt in plot_data['x_data']]
    call_all = plot_data['call_oi_data']
    put_all  = plot_data['put_oi_data']

    if window:
        x    = x_all[-window:]
        call = call_all[-window:]
        put  = put_all[-window:]
    else:
        x, call, put = x_all, call_all, put_all

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=call, mode='lines', name='Call OI',
        line=dict(color='blue', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Call OI: %{y:,}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=x, y=put, mode='lines', name='Put OI',
        line=dict(color='red', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Put OI: %{y:,}<extra></extra>"
    ))
    fig.update_layout(
        title=f"Real‑time Open Interest (OI) for {symbol}",
        template='plotly_white',
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible':False}),
        yaxis=dict(title="Open Interest", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

def generate_change_figure(plot_data, symbol, window: int = None):
    x_all      = [parse_datetime(dt) for dt in plot_data['x_data_change']]
    call_all   = plot_data['call_oi_change_data']
    put_all    = plot_data['put_oi_change_data']

    if window:
        x    = x_all[-window:]
        call = call_all[-window:]
        put  = put_all[-window:]
    else:
        x, call, put = x_all, call_all, put_all

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=call, mode='lines', name='Δ Call OI',
        line=dict(color='blue', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Call OI: %{y:,}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=x, y=put, mode='lines', name='Δ Put OI',
        line=dict(color='red', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Put OI: %{y:,}<extra></extra>"
    ))
    fig.update_layout(
        title=f"Real‑time Δ Open Interest (OI) for {symbol}",
        template='plotly_white',
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible':False}),
        yaxis=dict(title="Change in OI", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# Dash App & Layout
# ──────────────────────────────────────────────────────────────────────────────
app = dash.Dash(__name__)
app.title = "Real-time OI Data"

app.layout = html.Div([
    html.H1("Real‑time Open Interest (OI) Data", style={'textAlign':'center','marginBottom':'30px'}),

    # Row 1: Symbol | Strike Count | Expiry
    html.Div([
        html.Div([
            html.Label("Enter Symbol", style={'fontWeight':'bold'}),
            dcc.Input(id='symbol-input', type='text', value=DEFAULT_SYMBOL,
                      style={'width':'200px','padding':'6px'})
        ]),
        html.Div([
            html.Label("Strike Count", style={'fontWeight':'bold'}),
            dcc.Dropdown(
                id='strikecount-dropdown',
                options=[{'label':str(x),'value':x} for x in [1,5,8,10,15,20,25,30,35]],
                value=10, clearable=False,
                style={'width':'120px'}
            )
        ]),
        html.Div([
            html.Label("Expiry", style={'fontWeight':'bold'}),
            dcc.Dropdown(id='expiry-dropdown', options=[], value=None,
                         clearable=False, style={'width':'150px'})
        ])
    ], style={
        'display':'flex','justifyContent':'center','gap':'40px','marginBottom':'25px'
    }),

    # Row 2: Strike Range Slider | Date | Submit
    html.Div([
        html.Div([
            html.Label("Strike Range", style={'fontWeight':'bold','marginBottom':'10px'}),
            dcc.RangeSlider(
                id='strike-range-slider',
                min=0, max=0, step=1, marks={}, value=[0,0],
                tooltip={'placement':'bottom','always_visible':True},
                allowCross=False, pushable=1, updatemode='mouseup'
            )
        ], style={'flex':'1 1 400px'}),

        html.Div([
            html.Label("Select Date", style={'fontWeight':'bold'}),
            dcc.DatePickerSingle(
                id='date-picker',
                date=datetime.now().date(),
                display_format='YYYY-MM-DD',
                style={'padding':'6px'}
            )
        ]),

        html.Button("Submit", id='submit-symbol', n_clicks=0,
                    style={'padding':'8px 24px','fontSize':'16px'})
    ], style={
        'display':'flex','alignItems':'center','gap':'40px','marginBottom':'40px'
    }),

    dcc.Graph(id='oi-graph'),
    dcc.Graph(id='change-graph'),

    dcc.Interval(id='interval-component', interval=3*1000, n_intervals=0),
    dcc.Store(id='data-store', data=create_initial_data())
])

# ──────────────────────────────────────────────────────────────────────────────
# Callbacks
# ──────────────────────────────────────────────────────────────────────────────

# 1) Expiry options
@app.callback(
    Output('expiry-dropdown','options'),
    Output('expiry-dropdown','value'),
    Input('submit-symbol','n_clicks'),
    State('symbol-input','value'),
    State('strikecount-dropdown','value')
)
def update_expiry_options(nc, symbol, strikecount):
    resp = fyers_api.fetch_option_chain_data(symbol=symbol, strikecount=strikecount)
    if resp and 'expiryData' in resp:
        opts = [{'label':e['date'],'value':e['expiry']} for e in resp['expiryData']]
        return opts, (opts[0]['value'] if opts else None)
    return [], None

# 2) Populate RangeSlider when expiry changes
@app.callback(
    Output('strike-range-slider','min'),
    Output('strike-range-slider','max'),
    Output('strike-range-slider','marks'),
    Output('strike-range-slider','value'),
    Input('expiry-dropdown','value'),
    State('symbol-input','value'),
    State('strikecount-dropdown','value')
)
def update_strike_slider(expiry, symbol, strikecount):
    resp = fyers_api.fetch_option_chain_data(symbol=symbol, strikecount=strikecount, expiry=expiry)
    if not resp or 'optionsChain' not in resp:
        return no_update, no_update, no_update, no_update

    strikes = sorted({opt.get('strike_price',0) for opt in resp['optionsChain']})
    if not strikes:
        return no_update, no_update, no_update, no_update

    marks = {s: str(s) for s in strikes}
    return strikes[0], strikes[-1], marks, [strikes[0], strikes[-1]]

# 3) Fetch & store raw chain_history
@app.callback(
    Output('data-store','data'),
    Input('interval-component','n_intervals'),
    Input('submit-symbol','n_clicks'),
    State('data-store','data'),
    State('symbol-input','value'),
    State('strikecount-dropdown','value'),
    State('expiry-dropdown','value')
)
def update_data_store(n_int, n_clicks, data, symbol, strikecount, expiry):
    ctx = callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('submit-symbol'):
        data = reset_symbol_data(data, symbol)
    current = data.get('current_symbol', DEFAULT_SYMBOL)
    return fetch_and_append_data(data, current, strikecount, expiry)

# 4) Recompute & plot total OI
@app.callback(
    Output('oi-graph','figure'),
    Input('data-store','data'),
    Input('date-picker','date'),
    Input('strike-range-slider','value')
)
def update_oi_graph(data, sel_date, strike_range):
    low, high = strike_range
    sym = data['current_symbol']
    sd  = data['symbols_data'][sym]
    x_list = sd['x_data']

    call_ts, put_ts = [], []
    for chain in sd['chain_history']:
        c = sum(opt.get('oi',0)
                for opt in chain
                if opt.get('option_type')=='CE' and low <= opt.get('strike_price',0) <= high)
        p = sum(opt.get('oi',0)
                for opt in chain
                if opt.get('option_type')=='PE' and low <= opt.get('strike_price',0) <= high)
        call_ts.append(c)
        put_ts.append(p)

    if sel_date:
        x_f, call_f = filter_data_by_date(x_list, call_ts, sel_date)
        _,    put_f  = filter_data_by_date(x_list, put_ts, sel_date)
        pd = {'x_data':[dt.isoformat() for dt in x_f],
              'call_oi_data':call_f, 'put_oi_data':put_f}
    else:
        pd = {'x_data':x_list, 'call_oi_data':call_ts, 'put_oi_data':put_ts}

    return generate_oi_figure(pd, sym)

# 5) Recompute & plot ΔOI
@app.callback(
    Output('change-graph','figure'),
    Input('data-store','data'),
    Input('date-picker','date'),
    Input('strike-range-slider','value')
)
def update_change_graph(data, sel_date, strike_range):
    low, high = strike_range
    sym = data['current_symbol']
    sd  = data['symbols_data'][sym]
    x_list = sd['x_data']

    call_chg_ts, put_chg_ts = [], []
    for chain in sd['chain_history']:
        cchg = sum(opt.get('oich',0)
                   for opt in chain
                   if opt.get('option_type')=='CE' and low <= opt.get('strike_price',0) <= high)
        pchg = sum(opt.get('oich',0)
                   for opt in chain
                   if opt.get('option_type')=='PE' and low <= opt.get('strike_price',0) <= high)
        call_chg_ts.append(cchg)
        put_chg_ts.append(pchg)

    if sel_date:
        x_f, call_f = filter_data_by_date(x_list, call_chg_ts, sel_date)
        _,    put_f  = filter_data_by_date(x_list, put_chg_ts, sel_date)
        pd = {'x_data_change':[dt.isoformat() for dt in x_f],
              'call_oi_change_data':call_f,
              'put_oi_change_data':put_f}
    else:
        pd = {'x_data_change':x_list,
              'call_oi_change_data':call_chg_ts,
              'put_oi_change_data':put_chg_ts}

    return generate_change_figure(pd, sym)

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)