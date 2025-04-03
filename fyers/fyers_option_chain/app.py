from data_fetcher import FyersAPI
from graph_updater import RealTimeGraph
import time
import logging

def main():
    logging.info("Starting real-time OI data fetch and graph update")

    # Fyers API configuration
    client_id = "K731S35ZOK"
    APP_KEY = '5E8EIXGMF9-100'
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbjdpNUZvSGpSYkkwRTVLMHlCZ0Z6ZUlOMzBJWWx5NkU5bHJab3dVVng4ZkF5X1A2RlBCenpnb0RxSkRLcVlNaDJwRVBPYlpab0E2YUhkM2ExQm9ub2k4YkNvcnRMRWFyVWtuc0JqNU5sWDBwRUZVQT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQzNzI2NjAwLCJpYXQiOjE3NDM2NjI2NjEsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0MzY2MjY2MSwic3ViIjoiYWNjZXNzX3Rva2VuIn0.fmkd39J7qcL6ABEO5pirpEr00fFHqDc56-rimHlUXEo"

    # Initialize Fyers API and Graph
    fyers_api = FyersAPI(client_id, access_token)
    real_time_graph = RealTimeGraph()

    # Start real-time graph update
    real_time_graph.animate(fyers_api)

if __name__ == '__main__':
    main()
