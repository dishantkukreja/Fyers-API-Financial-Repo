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
access_token = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbjgxdEU1SHlYTmlBNHJIZkJPWUNXQ1VTQng3allmQ284ck53V0JKdk8zc1VKbG9FOW1WaDlnZC1Ra0pkWk1NNF9IdExYVDVZR2tGOVoxVWphQ0pyZ2I0azZUUkpZaTBkQ2RXb0Y2NGZ5Vl9jUG1YVT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQ0MDcyMjAwLCJpYXQiOjE3NDQwMDE4NjAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0NDAwMTg2MCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.SdFo2ptZKkOEWaMIeqC0BMRW3D_1kpLSlEqJtTpZEjo")
fyers_api = FyersAPI(client_id, access_token)

DEFAULT_SYMBOL = "NSE:NIFTYBANK-INDEX"

def create_initial_data():
    """Creates the initial structure for the data store for both OI and OI change."""
    return {
        'current_symbol': DEFAULT_SYMBOL,
        'symbols_data': {
            DEFAULT_SYMBOL: {
                # OI Data
                'x_data': [],
                'call_oi_data': [],
                'put_oi_data': [],
                # Change Data
                'x_data_change': [],
                'call_oi_change_data': [],
                'put_oi_change_data': []
            }
        }
    }

def reset_symbol_data(data, symbol):
    """
    Updates the data store when a new symbol is submitted.
    If the symbol exists, preserves its historical data;
    otherwise, initializes empty records for both OI and change data.
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

def fetch_and_append_data(data, symbol, strikecount):
    """
    Fetches the latest data for the given symbol from the API using the provided strikecount,
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
    # Pass strikecount to the API call
    api_response = fyers_api.fetch_option_chain_data(symbol=symbol, strikecount=strikecount)
    if api_response:
        # Update OI data
        callOi = api_response.get('callOi', 0)
        putOi = api_response.get('putOi', 0)
        print(f"call {callOi}")
        print(f"put {putOi}")
        # Store the current datetime as an ISO formatted string
        now_dt = datetime.now()
        now_iso = now_dt.isoformat()
        symbol_data['x_data'].append(now_iso)
        symbol_data['call_oi_data'].append(callOi)
        symbol_data['put_oi_data'].append(putOi)

        # Calculate change in OI using optionsChain data
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
        symbol_data['put_oi_change_data'].append(put_oi_change)  # Example: you can adjust this if needed.
    data['symbols_data'][symbol] = symbol_data
    return data

# def putOi_change_value(putOi):
#     """
#     Placeholder for Put OI change calculation.
#     Currently returns 0; adjust this function if you have a specific calculation.
#     """
#     return 0

def parse_datetime(dt):
    """
    Converts a stored datetime string back into a datetime object.
    If dt is already a datetime object, return it.
    """
    if isinstance(dt, str):
        try:
            return datetime.fromisoformat(dt)
        except Exception as e:
            # Fallback: adjust this format if needed.
            return datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
    return dt


def generate_oi_figure(symbol_data, symbol):
    """Generates a Plotly figure with two separate y-axes for OI data, 
       using smooth spline lines for a more visually appealing chart."""
    # Convert stored ISO strings to datetime objects
    x_dt = [parse_datetime(dt) for dt in symbol_data['x_data']]

    # Create a figure with 1 row, 1 column, but 2 separate y-axes
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Trace for Call OI (left axis)
    fig.add_trace(
        go.Scatter(
            x=x_dt,
            y=symbol_data['call_oi_data'],
            mode='lines',  # no markers
            name='Call OI',
            line=dict(
                color='blue',
                width=3,
                shape='spline',      # Use spline for smooth curves
                smoothing=1.3        # Adjust smoothing factor (0–1.3 typically)
            ),
            hoverinfo='text',
            text=[
                f"Time: {parse_datetime(dt).strftime('%H:%M:%S')}<br>Call OI: {v:,}"
                for dt, v in zip(symbol_data['x_data'], symbol_data['call_oi_data'])
            ]
        ),
        secondary_y=False  # left y-axis
    )

    # Trace for Put OI (right axis)
    fig.add_trace(
        go.Scatter(
            x=x_dt,
            y=symbol_data['put_oi_data'],
            mode='lines',
            name='Put OI',
            line=dict(
                color='red',
                width=3,
                shape='spline',
                smoothing=1.3
            ),
            hoverinfo='text',
            text=[
                f"Time: {parse_datetime(dt).strftime('%H:%M:%S')}<br>Put OI: {v:,}"
                for dt, v in zip(symbol_data['x_data'], symbol_data['put_oi_data'])
            ]
        ),
        secondary_y=True  # right y-axis
    )

    # Basic layout: remove range slider & range selector, set styling
    fig.update_layout(
        title=f"Real-time Open Interest (OI) Data for {symbol}",
        template='plotly_white',
        hovermode="x unified",
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            rangeslider=dict(visible=False),
            rangeselector=dict(visible=False)
        ),
        yaxis=dict(
            title="Call OI",
            showgrid=True,
            gridcolor='lightgrey'
        ),
        yaxis2=dict(
            title="Put OI",
            showgrid=False,
            overlaying='y',
            side='right'
        )
    )

    return fig


def generate_change_figure(symbol_data, symbol):
    """Generates a Plotly figure with two separate y-axes for Change in OI data,
       using smooth spline lines for a more visually appealing chart."""
    # Convert stored ISO strings in x_data_change to datetime objects
    x_dt = [parse_datetime(dt) for dt in symbol_data['x_data_change']]

    # Create a figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Trace for Change in Call OI (left y-axis)
    fig.add_trace(
        go.Scatter(
            x=x_dt,
            y=symbol_data['call_oi_change_data'],
            mode='lines',
            name='Change in Call OI',
            line=dict(
                color='blue',
                width=3,
                shape='spline',
                smoothing=1.3
            ),
            hoverinfo='text',
            text=[
                f"Time: {parse_datetime(dt).strftime('%H:%M:%S')}<br>Change in Call OI: {v:,}"
                for dt, v in zip(symbol_data['x_data_change'], symbol_data['call_oi_change_data'])
            ]
        ),
        secondary_y=False
    )
    
    # Trace for Change in Put OI (right y-axis)
    fig.add_trace(
        go.Scatter(
            x=x_dt,
            y=symbol_data['put_oi_change_data'],
            mode='lines',
            name='Change in Put OI',
            line=dict(
                color='red',
                width=3,
                shape='spline',
                smoothing=1.3
            ),
            hoverinfo='text',
            text=[
                f"Time: {parse_datetime(dt).strftime('%H:%M:%S')}<br>Change in Put OI: {v:,}"
                for dt, v in zip(symbol_data['x_data_change'], symbol_data['put_oi_change_data'])
            ]
        ),
        secondary_y=True
    )
    
    # Update layout to remove range slider/selector and set styling
    fig.update_layout(
        title=f"Real-time Change in Open Interest (OI) Data for {symbol}",
        template='plotly_white',
        hovermode="x unified",
        xaxis=dict(
            showgrid=True,
            gridcolor='lightgrey',
            rangeslider=dict(visible=False),
            rangeselector=dict(visible=False)
        ),
        yaxis=dict(
            title="Change in Call OI",
            showgrid=True,
            gridcolor='lightgrey'
        ),
        yaxis2=dict(
            title="Change in Put OI",
            showgrid=False,
            overlaying='y',
            side='right'
        )
    )
    
    return fig

# Create the Dash app
app = dash.Dash(__name__)
app.title = "Real-time OI Data"

# Layout: includes symbol input, strike count dropdown, submit button, two graphs, interval, and a hidden store.
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

# Combined callback to update the data-store for both OI and change data.
@app.callback(
    Output('data-store', 'data'),
    [Input('interval-component', 'n_intervals'),
     Input('submit-symbol', 'n_clicks')],
    [State('data-store', 'data'),
     State('symbol-input', 'value'),
     State('strikecount-dropdown', 'value')]
)
def update_data_store(n_intervals, n_clicks, data, symbol, strikecount):
    ctx = callback_context
    if not ctx.triggered:
        trigger_id = None
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'submit-symbol':
        data = reset_symbol_data(data, symbol)

    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    data = fetch_and_append_data(data, current_symbol, strikecount)
    return data

# Callback to update the OI graph.
@app.callback(
    Output('oi-graph', 'figure'),
    Input('data-store', 'data')
)
def update_oi_graph(data):
    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    symbol_data = data['symbols_data'].get(current_symbol, {
        'x_data': [],
        'call_oi_data': [],
        'put_oi_data': []
    })
    return generate_oi_figure(symbol_data, current_symbol)

# Callback to update the change in OI graph.
@app.callback(
    Output('change-graph', 'figure'),
    Input('data-store', 'data')
)
def update_change_graph(data):
    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    symbol_data = data['symbols_data'].get(current_symbol, {
        'x_data_change': [],
        'call_oi_change_data': [],
        'put_oi_change_data': []
    })
    return generate_change_figure(symbol_data, current_symbol)

if __name__ == '__main__':
    app.run(debug=True)
