import dash
from dash import dcc, html, Output, Input, State, callback_context
import plotly.graph_objs as go
from datetime import datetime, timedelta, time as dt_time
from plotly.subplots import make_subplots
import time

# Import your FyersAPI from data_fetcher
from data_fetcher import FyersAPI

# Fyers API configuration
client_id = "K731S35ZOK"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbjlNb0szZ1U1d2ctaUZXWEFrVHdEeml4MklWMHlHRjA1aUE2elFVWHpVcFRCRzAtdm5XQVNReVFhMXYxVEV4QjZ1R2lLeVZoZDYwV3ItWTIyRFo5MGQ1UUNScGliT1pvcDcySF9rb05zcGJ2R3dNND0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ0MTU4NjAwLCJpYXQiOjE3NDQwOTU3NTQsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NDA5NTc1NCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.9JoDxc2850ejEgleWjaqmge_PKbotHksLeybEiUOdV0"

fyers_api = FyersAPI(client_id, access_token)

DEFAULT_SYMBOL = "NSE:NIFTYBANK-INDEX"

def create_initial_data():
    """Creates the initial structure for the data store for both OI and OI change."""
    return {
        'current_symbol': DEFAULT_SYMBOL,
        'symbols_data': {
            DEFAULT_SYMBOL: {
                'x_data': [],
                'call_oi_data': [],
                'put_oi_data': [],
                'x_data_change': [],
                'call_oi_change_data': [],
                'put_oi_change_data': []
            }
        }
    }

def reset_symbol_data(data, symbol):
    """
    Resets the data store for the given symbol.
    If the symbol exists, preserves its historical data; otherwise, initializes empty records.
    """
    if symbol not in data['symbols_data']:
        data['symbols_data'][symbol] = {
            'x_data': [],
            'call_oi_data': [],
            'put_oi_data': [],
            'x_data_change': [],
            'call_oi_change_data': [],
            'put_oi_change_data': []
        }
    data['current_symbol'] = symbol
    return data

def fetch_and_append_data(data, symbol, strikecount, expiry):
    """
    Fetches the latest data for the given symbol using the provided strikecount and expiry,
    then appends both OI data and change in OI data to the respective lists.
    """
    symbol_data = data['symbols_data'].get(symbol, {
        'x_data': [],
        'call_oi_data': [],
        'put_oi_data': [],
        'x_data_change': [],
        'call_oi_change_data': [],
        'put_oi_change_data': []
    })
    # Pass strikecount and expiry to the API call
    api_response = fyers_api.fetch_option_chain_data(symbol=symbol, strikecount=strikecount, expiry=expiry)
    if api_response:
        callOi = api_response.get('callOi', 0)
        putOi = api_response.get('putOi', 0)
        print(f"call {callOi}")
        print(f"put {putOi}")
        now_dt = datetime.now()
        now_iso = now_dt.isoformat()
        symbol_data['x_data'].append(now_iso)
        symbol_data['call_oi_data'].append(callOi)
        symbol_data['put_oi_data'].append(putOi)

        # Calculate change in OI from optionsChain data
        call_oi_change = 0
        put_oi_change = 0
        for option in api_response.get('optionsChain', []):
            option_type = option.get('option_type')
            oi_change = option.get('oich', 0)
            if option_type == 'CE':
                call_oi_change += oi_change
            elif option_type == 'PE':
                put_oi_change += oi_change
        symbol_data['x_data_change'].append(now_iso)
        symbol_data['call_oi_change_data'].append(call_oi_change)
        symbol_data['put_oi_change_data'].append(put_oi_change)
    data['symbols_data'][symbol] = symbol_data
    return data


def parse_datetime(dt):
    """Converts an ISO datetime string back into a datetime object."""
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt)
        except Exception as e:
            return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt

def filter_data_by_date(x_list, y_list, selected_date):
    """
    Filters the x_list (ISO strings) and corresponding y_list so that only data points
    matching the selected_date (YYYY-MM-DD) remain.
    Returns (filtered_x_dt, filtered_y_list).
    """
    filtered_x = []
    filtered_y = []
    for x, y in zip(x_list, y_list):
        dt_obj = parse_datetime(x)
        if dt_obj.date().isoformat() == selected_date:
            filtered_x.append(dt_obj)
            filtered_y.append(y)
    return filtered_x, filtered_y


from plotly.subplots import make_subplots
import plotly.graph_objects as go

def generate_oi_figure(symbol_data, symbol, window: int = None):
    """
    Plots raw Call and Put OI on a single y-axis.
    By default it autoranges the y-axis to the data you pass in.
    If `window` is set, only the last `window` points are plotted.
    """
    # parse and slice
    x_all  = [parse_datetime(dt) for dt in symbol_data['x_data']]
    call_all = symbol_data['call_oi_data']
    put_all  = symbol_data['put_oi_data']

    if window:
        x = x_all[-window:]
        call = call_all[-window:]
        put  = put_all[-window:]
    else:
        x = x_all
        call = call_all
        put  = put_all

    # nudge any zeros up so log or linear autorange works cleanly
    call = [v if v != 0 else 0 for v in call]
    put  = [v if v != 0 else 0 for v in put]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=call,
        mode='lines',
        name='Call OI',
        line=dict(color='blue', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Call OI: %{y:,}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=x, y=put,
        mode='lines',
        name='Put OI',
        line=dict(color='red', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Put OI: %{y:,}<extra></extra>"
    ))

    fig.update_layout(
        title=f"Real‑time Open Interest (OI) for {symbol}",
        template='plotly_white',
        hovermode="x unified",
        xaxis=dict(
            showgrid=True, gridcolor='lightgrey',
            rangeslider=dict(visible=False),
            rangeselector=dict(visible=False)
        ),
        yaxis=dict(
            title="Open Interest",
            showgrid=True, gridcolor='lightgrey',
            autorange=True     # <— this lets the axis rescale on every redraw
        )
    )
    return fig


def generate_change_figure(symbol_data, symbol, window: int = None):
    """
    Plots raw Δ Call and Δ Put OI on a single y-axis, autoranged.
    Pass `window` to only draw the last N points.
    """
    x_all      = [parse_datetime(dt) for dt in symbol_data['x_data_change']]
    call_all   = symbol_data['call_oi_change_data']
    put_all    = symbol_data['put_oi_change_data']

    if window:
        x = x_all[-window:]
        call = call_all[-window:]
        put  = put_all[-window:]
    else:
        x = x_all
        call = call_all
        put  = put_all

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=call,
        mode='lines',
        name='Δ Call OI',
        line=dict(color='blue', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Call OI: %{y:,}<extra></extra>"
    ))

    fig.add_trace(go.Scatter(
        x=x, y=put,
        mode='lines',
        name='Δ Put OI',
        line=dict(color='red', width=2),
        hovertemplate="Time: %{x|%H:%M:%S}<br>Δ Put OI: %{y:,}<extra></extra>"
    ))

    fig.update_layout(
        title=f"Real‑time Δ Open Interest (OI) for {symbol}",
        template='plotly_white',
        hovermode="x unified",
        xaxis=dict(
            showgrid=True, gridcolor='lightgrey',
            rangeslider=dict(visible=False),
            rangeselector=dict(visible=False)
        ),
        yaxis=dict(
            title="Change in OI",
            showgrid=True, gridcolor='lightgrey',
            autorange=True
        )
    )
    return fig



# Create the Dash app layout
app = dash.Dash(__name__)
app.title = "Real-time OI Data"

app.layout = html.Div([
    html.H1("Real-time Open Interest (OI) Data", style={'textAlign': 'center'}),
    html.Div([
        html.Label("Enter Symbol:", style={'fontSize': '16px', 'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Input(
            id='symbol-input',
            type='text',
            value=DEFAULT_SYMBOL,
            style={'marginRight': '20px', 'padding': '5px', 'fontSize': '14px'}
        ),
        html.Label("Strike Count:", style={'fontSize': '16px', 'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='strikecount-dropdown',
            options=[{'label': str(x), 'value': x} for x in [1, 5, 8, 10, 15, 20, 25, 30, 35]],
            value=10,
            clearable=False,
            style={'width': '150px', 'display': 'inline-block', 'verticalAlign': 'middle', 'fontSize': '14px', 'marginRight': '20px'}
        ),
        html.Label("Expiry:", style={'fontSize': '16px', 'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.Dropdown(
            id='expiry-dropdown',
            options=[],  # Options will be updated dynamically
            value=None,
            clearable=False,
            style={'width': '200px', 'display': 'inline-block', 'verticalAlign': 'middle', 'fontSize': '14px', 'marginRight': '20px'}
        ),
        html.Label("Select Date:", style={'fontSize': '16px', 'fontWeight': 'bold', 'marginRight': '10px'}),
        dcc.DatePickerSingle(
            id='date-picker',
            date=datetime.now().date(),
            display_format='YYYY-MM-DD',
            style={'display': 'inline-block', 'verticalAlign': 'middle', 'marginRight': '20px'}
        ),
        html.Button("Submit", id="submit-symbol", n_clicks=0, style={'padding': '5px 15px', 'fontSize': '16px'})
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    dcc.Graph(id='oi-graph', animate=False),
    dcc.Graph(id='change-graph', animate=False),
    dcc.Interval(
        id='interval-component',
        interval=3*1000,  # 3 seconds
        n_intervals=0
    ),
    dcc.Store(id='data-store', data=create_initial_data())
])

# Callback to update the expiry dropdown options based on the symbol and strike count.
@app.callback(
    Output('expiry-dropdown', 'options'),
    Output('expiry-dropdown', 'value'),
    [Input('submit-symbol', 'n_clicks')],
    [State('symbol-input', 'value'),
     State('strikecount-dropdown', 'value')]
)
def update_expiry_options(n_clicks, symbol, strikecount):
    # Call the API once to get the expiryData.
    response = fyers_api.fetch_option_chain_data(symbol=symbol, strikecount=strikecount)
    if response and 'expiryData' in response:
        options = [{'label': exp['date'], 'value': exp['expiry']} for exp in response['expiryData']]
        # Default to the first expiry value.
        default_value = options[0]['value'] if options else None
        return options, default_value
    return [], None

# Combined callback to update the data-store.
@app.callback(
    Output('data-store', 'data'),
    [Input('interval-component', 'n_intervals'),
     Input('submit-symbol', 'n_clicks')],
    [State('data-store', 'data'),
     State('symbol-input', 'value'),
     State('strikecount-dropdown', 'value'),
     State('expiry-dropdown', 'value')]
)
def update_data_store(n_intervals, n_clicks, data, symbol, strikecount, expiry):
    ctx = callback_context
    if not ctx.triggered:
        trigger_id = None
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'submit-symbol':
        data = reset_symbol_data(data, symbol)
    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    data = fetch_and_append_data(data, current_symbol, strikecount, expiry)
    return data

# Callback to update the OI graph.
@app.callback(
    Output('oi-graph', 'figure'),
    [Input('data-store', 'data'),
     Input('date-picker', 'date')]
)
def update_oi_graph(data, selected_date):
    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    symbol_data = data['symbols_data'].get(current_symbol, {
        'x_data': [],
        'call_oi_data': [],
        'put_oi_data': []
    })
    if selected_date:
        x_filtered, call_filtered = filter_data_by_date(symbol_data['x_data'], symbol_data['call_oi_data'], selected_date)
        _, put_filtered = filter_data_by_date(symbol_data['x_data'], symbol_data['put_oi_data'], selected_date)
        filtered_symbol_data = {
            'x_data': [dt.isoformat() for dt in x_filtered],
            'call_oi_data': call_filtered,
            'put_oi_data': put_filtered
        }
        return generate_oi_figure(filtered_symbol_data, current_symbol)
    else:
        return generate_oi_figure(symbol_data, current_symbol)

# Callback to update the Change in OI graph.
@app.callback(
    Output('change-graph', 'figure'),
    [Input('data-store', 'data'),
     Input('date-picker', 'date')]
)
def update_change_graph(data, selected_date):
    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    symbol_data = data['symbols_data'].get(current_symbol, {
        'x_data_change': [],
        'call_oi_change_data': [],
        'put_oi_change_data': []
    })
    if selected_date:
        x_filtered, call_filtered = filter_data_by_date(symbol_data['x_data_change'], symbol_data['call_oi_change_data'], selected_date)
        _, put_filtered = filter_data_by_date(symbol_data['x_data_change'], symbol_data['put_oi_change_data'], selected_date)
        filtered_symbol_data = {
            'x_data_change': [dt.isoformat() for dt in x_filtered],
            'call_oi_change_data': call_filtered,
            'put_oi_change_data': put_filtered
        }
        return generate_change_figure(filtered_symbol_data, current_symbol)
    else:
        return generate_change_figure(symbol_data, current_symbol)

if __name__ == '__main__':
    app.run(debug=True)
