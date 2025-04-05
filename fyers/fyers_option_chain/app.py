import dash
from dash import dcc, html, Output, Input, State, callback_context
import plotly.graph_objs as go
from datetime import datetime
import time

# Import your FyersAPI from data_fetcher
from data_fetcher import FyersAPI

# Fyers API configuration
client_id = "K731S35ZOK"
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbjhPS3czOEVUVnBVQ0NFM0VLd0RTcmJtWHFLVGh5N2dKZXpKMm9oXzBCN012T1hxbHVCX3VHeGhSTDNIVkRqSkhySGp3VldiMF9yRXZwZmxJYjQyMk9qcy1tYjJvU1ZBUWdIX2V2TG9wRmVvVzFjOD0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQzODk5NDAwLCJpYXQiOjE3NDM4Mzk5MjAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0MzgzOTkyMCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.xywVJQU-gN6qUaYHiiGqYRhT3b0mq1bePEzN3dfJs_Q"
fyers_api = FyersAPI(client_id, access_token)

DEFAULT_SYMBOL = "NSE:NIFTYBANK-INDEX"

def create_initial_data():
    """Creates the initial structure for the data store."""
    return {
        'current_symbol': DEFAULT_SYMBOL,
        'symbols_data': {
            DEFAULT_SYMBOL: {
                'x_data': [],
                'call_oi_data': [],
                'put_oi_data': []
            }
        }
    }

def reset_symbol_data(data, symbol):
    """
    Updates the data store when a new symbol is submitted.
    If symbol exists, preserves its historical data.
    Otherwise, initializes an empty record for the symbol.
    """
    if symbol not in data['symbols_data']:
        data['symbols_data'][symbol] = {
            'x_data': [],
            'call_oi_data': [],
            'put_oi_data': []
        }
    data['current_symbol'] = symbol
    return data

def fetch_and_append_data(data, symbol):
    """
    Fetches the latest data for the given symbol from the API,
    and appends it to the corresponding data lists.
    """
    symbol_data = data['symbols_data'].get(symbol, {
        'x_data': [],
        'call_oi_data': [],
        'put_oi_data': []
    })
    new_data = fyers_api.fetch_option_chain_data(symbol=symbol)
    if new_data:
        callOi = new_data.get('callOi', 0)
        putOi = new_data.get('putOi', 0)
        now = datetime.now().strftime("%H:%M:%S")
        symbol_data['x_data'].append(now)
        symbol_data['call_oi_data'].append(callOi)
        symbol_data['put_oi_data'].append(putOi)
    data['symbols_data'][symbol] = symbol_data
    return data

def generate_figure(symbol_data, symbol):
    """Generates a Plotly figure based on the given symbol data."""
    fig = go.Figure()

    # Trace for Call OI with hover text
    fig.add_trace(go.Scatter(
        x=symbol_data['x_data'],
        y=symbol_data['call_oi_data'],
        mode='lines+markers',
        name='Call OI',
        line=dict(color='blue'),
        marker=dict(size=8),
        hoverinfo='text',
        text=[f"Time: {t}<br>Call OI: {v:,}" for t, v in zip(symbol_data['x_data'], symbol_data['call_oi_data'])]
    ))

    # Trace for Put OI with hover text
    fig.add_trace(go.Scatter(
        x=symbol_data['x_data'],
        y=symbol_data['put_oi_data'],
        mode='lines+markers',
        name='Put OI',
        line=dict(color='red'),
        marker=dict(size=8),
        hoverinfo='text',
        text=[f"Time: {t}<br>Put OI: {v:,}" for t, v in zip(symbol_data['x_data'], symbol_data['put_oi_data'])]
    ))

    # Update layout with titles and axis labels
    fig.update_layout(
        title=f"Real-time Open Interest (OI) Data for {symbol}",
        xaxis_title="Time",
        yaxis_title="Open Interest (OI)",
        hovermode="closest"
    )
    return fig

# Create the Dash app
app = dash.Dash(__name__)
app.title = "Real-time OI Data"

# Layout with a symbol input, submit button, graph, interval, and a hidden store.
app.layout = html.Div([
    html.H1("Real-time Open Interest (OI) Data", style={'textAlign': 'center'}),
    html.Div([
        html.Label("Enter Symbol:"),
        dcc.Input(
            id='symbol-input',
            type='text',
            value=DEFAULT_SYMBOL,
            style={'marginRight': '10px'}
        ),
        html.Button("Submit", id="submit-symbol", n_clicks=0)
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    dcc.Graph(id='live-graph', animate=False),
    dcc.Interval(
        id='interval-component',
        interval=3*1000,  # 3 seconds
        n_intervals=0
    ),
    dcc.Store(id='data-store', data=create_initial_data())
])

# Combined callback to update the data-store.
@app.callback(
    Output('data-store', 'data'),
    [Input('interval-component', 'n_intervals'),
     Input('submit-symbol', 'n_clicks')],
    [State('data-store', 'data'),
     State('symbol-input', 'value')]
)
def update_data_store(n_intervals, n_clicks, data, symbol):
    ctx = callback_context
    if not ctx.triggered:
        trigger_id = None
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'submit-symbol':
        data = reset_symbol_data(data, symbol)

    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    data = fetch_and_append_data(data, current_symbol)
    return data

# Callback to update the graph based on the current symbol's data.
@app.callback(
    Output('live-graph', 'figure'),
    Input('data-store', 'data')
)
def update_graph(data):
    current_symbol = data.get('current_symbol', DEFAULT_SYMBOL)
    symbol_data = data['symbols_data'].get(current_symbol, {
        'x_data': [],
        'call_oi_data': [],
        'put_oi_data': []
    })
    fig = generate_figure(symbol_data, current_symbol)
    return fig

if __name__ == '__main__':
    app.run(debug=True)