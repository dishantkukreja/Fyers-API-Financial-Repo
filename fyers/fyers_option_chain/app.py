# app.py
import dash
from dash import dcc, html, Output, Input, State, callback_context
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
                'x_data': [], 'call_oi_data': [], 'put_oi_data': [],
                'x_data_change': [], 'call_oi_change_data': [], 'put_oi_change_data': []
            }
        }
    }

def reset_symbol_data(data, symbol):
    if symbol not in data['symbols_data']:
        data['symbols_data'][symbol] = {
            'x_data': [], 'call_oi_data': [], 'put_oi_data': [],
            'x_data_change': [], 'call_oi_change_data': [], 'put_oi_change_data': []
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

def fetch_and_append_data(data, symbol, strikecount, expiry, strike_range):
    """
    Fetches the option chain, then sums oi/oich for CE and PE
    only for strikes within strike_range = [low, high].
    """
    symbol_data = data['symbols_data'].get(symbol, {
        'x_data': [], 'call_oi_data': [], 'put_oi_data': [],
        'x_data_change': [], 'call_oi_change_data': [], 'put_oi_change_data': []
    })

    resp = fyers_api.fetch_option_chain_data(
        symbol=symbol,
        strikecount=strikecount,
        expiry=expiry
    )
    if resp and 'optionsChain' in resp:
        chain = resp['optionsChain']
        low, high = strike_range or (0, float('inf'))

        callOi = putOi = callOIch = putOIch = 0
        for opt in chain:
            sp = opt.get('strike_price', 0)
            if sp < low or sp > high:
                continue
            oi   = opt.get('oi', 0)
            oich = opt.get('oich', 0)
            if opt.get('option_type') == 'CE':
                callOi   += oi
                callOIch += oich
            elif opt.get('option_type') == 'PE':
                putOi    += oi
                putOIch  += oich

        now_iso = datetime.now().isoformat()
        symbol_data['x_data'].append(now_iso)
        symbol_data['call_oi_data'].append(callOi)
        symbol_data['put_oi_data'].append(putOi)

        symbol_data['x_data_change'].append(now_iso)
        symbol_data['call_oi_change_data'].append(callOIch)
        symbol_data['put_oi_change_data'].append(putOIch)

    data['symbols_data'][symbol] = symbol_data
    return data

# ──────────────────────────────────────────────────────────────────────────────
# Plot generators (unchanged from your last version)
# ──────────────────────────────────────────────────────────────────────────────
def generate_oi_figure(symbol_data, symbol, window: int = None):
    x_all  = [parse_datetime(dt) for dt in symbol_data['x_data']]
    call_all = symbol_data['call_oi_data']
    put_all  = symbol_data['put_oi_data']

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
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible':False}),
        yaxis=dict(title="Open Interest", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

def generate_change_figure(symbol_data, symbol, window: int = None):
    x_all      = [parse_datetime(dt) for dt in symbol_data['x_data_change']]
    call_all   = symbol_data['call_oi_change_data']
    put_all    = symbol_data['put_oi_change_data']

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
        template='plotly_white', hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor='lightgrey', rangeslider={'visible':False}),
        yaxis=dict(title="Change in OI", showgrid=True, gridcolor='lightgrey', autorange=True)
    )
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# Dash app & layout
# ──────────────────────────────────────────────────────────────────────────────


app = dash.Dash(__name__)
app.title = "Real-time OI Data"

app.layout = html.Div(
    style={
        'fontFamily': '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
        'padding': '20px',
        'maxWidth': '1000px',
        'margin': '0 auto'
    },
    children=[

        # Title
        html.H1(
            "Real‑time Open Interest (OI) Data",
            style={'textAlign': 'center', 'marginBottom': '30px'}
        ),

        # ─── Row 1: Symbol | Strike Count | Expiry ───
        html.Div(
            style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'flex-end',
                'marginBottom': '25px',
                'flexWrap': 'wrap',
                'gap': '20px'
            },
            children=[

                # Symbol
                html.Div([
                    html.Label("Enter Symbol", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Input(
                        id='symbol-input',
                        type='text',
                        value=DEFAULT_SYMBOL,
                        style={'width': '200px', 'padding': '6px'}
                    )
                ]),

                # Strike Count
                html.Div([
                    html.Label("Strike Count", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id='strikecount-dropdown',
                        options=[{'label': str(x), 'value': x} for x in [1,5,8,10,15,20,25,30,35]],
                        value=10,
                        clearable=False,
                        style={'width': '120px'}
                    )
                ]),

                # Expiry
                html.Div([
                    html.Label("Expiry", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.Dropdown(
                        id='expiry-dropdown',
                        options=[],
                        value=None,
                        clearable=False,
                        style={'width': '150px'}
                    )
                ]),
            ]
        ),

        # ─── Row 2: Strike Range Slider | Date | Submit ───
        html.Div(
            style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'alignItems': 'center',
                'marginBottom': '40px',
                'flexWrap': 'wrap',
                'gap': '20px'
            },
            children=[

                # Strike Range Slider
                html.Div([
                    html.Label("Strike Range", style={'fontWeight': 'bold', 'marginBottom': '10px'}),
                    dcc.RangeSlider(
                        id='strike-range-slider',
                        min=0,
                        max=0,
                        step=1,
                        marks={},
                        value=[0, 0],
                        tooltip={'placement': 'bottom', 'always_visible': True},
                        allowCross=False,
                        pushable=1,
                        updatemode='mouseup'
                    )
                ], style={'flex': '1 1 400px'}),

                # Select Date
                html.Div([
                    html.Label("Select Date", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                    dcc.DatePickerSingle(
                        id='date-picker',
                        date=datetime.now().date(),
                        display_format='YYYY-MM-DD',
                        style={'padding': '6px'}
                    )
                ]),

                # Submit Button
                html.Div([
                    html.Button(
                        "Submit",
                        id='submit-symbol',
                        n_clicks=0,
                        style={'padding': '8px 24px', 'fontSize': '16px'}
                    )
                ])
            ]
        ),

        # Graphs
        dcc.Graph(id='oi-graph'),
        dcc.Graph(id='change-graph'),

        # Interval & Store
        dcc.Interval(id='interval-component', interval=3*1000, n_intervals=0),
        dcc.Store(id='data-store', data=create_initial_data())
    ]
)


# ──────────────────────────────────────────────────────────────────────────────
# Callbacks
# ──────────────────────────────────────────────────────────────────────────────

# 1) Populate Expiry dropdown
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

# 2) NEW: Populate Strike Range slider
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
        return _dash.no_update, _dash.no_update, _dash.no_update, _dash.no_update

    strikes = sorted({opt['strike_price'] for opt in resp['optionsChain']})
    if not strikes:
        return _dash.no_update, _dash.no_update, _dash.no_update, _dash.no_update

    marks = {s: str(s) for s in strikes}
    return strikes[0], strikes[-1], marks, [strikes[0], strikes[-1]]

# 3) Update data‐store (now includes strike‐range)
@app.callback(
    Output('data-store','data'),
    Input('interval-component','n_intervals'),
    Input('submit-symbol','n_clicks'),
    Input('strike-range-slider','value'),
    State('data-store','data'),
    State('symbol-input','value'),
    State('strikecount-dropdown','value'),
    State('expiry-dropdown','value')
)
def update_data_store(n_int, n_clicks, strike_range, data, symbol, strikecount, expiry):
    ctx = callback_context
    if ctx.triggered and ctx.triggered[0]['prop_id'].startswith('submit-symbol'):
        data = reset_symbol_data(data, symbol)
    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    return fetch_and_append_data(data, current_symbol, strikecount, expiry, strike_range)

# 4) Render OI graph
@app.callback(
    Output('oi-graph','figure'),
    Input('data-store','data'),
    Input('date-picker','date')
)
def update_oi_graph(data, sel_date):
    sym = data.get('current_symbol', DEFAULT_SYMBOL)
    sd  = data['symbols_data'][sym]
    if sel_date:
        x_f, call_f = filter_data_by_date(sd['x_data'], sd['call_oi_data'], sel_date)
        _,    put_f  = filter_data_by_date(sd['x_data'], sd['put_oi_data'], sel_date)
        fd = {'x_data':[dt.isoformat() for dt in x_f], 'call_oi_data':call_f, 'put_oi_data':put_f}
        return generate_oi_figure(fd, sym)
    return generate_oi_figure(sd, sym)

# 5) Render ΔOI graph
@app.callback(
    Output('change-graph','figure'),
    Input('data-store','data'),
    Input('date-picker','date')
)
def update_change_graph(data, sel_date):
    sym = data.get('current_symbol', DEFAULT_SYMBOL)
    sd  = data['symbols_data'][sym]
    if sel_date:
        x_f, call_f = filter_data_by_date(sd['x_data_change'], sd['call_oi_change_data'], sel_date)
        _,    put_f  = filter_data_by_date(sd['x_data_change'], sd['put_oi_change_data'], sel_date)
        fd = {'x_data_change':[dt.isoformat() for dt in x_f],
              'call_oi_change_data':call_f, 'put_oi_change_data':put_f}
        return generate_change_figure(fd, sym)
    return generate_change_figure(sd, sym)

# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True)
