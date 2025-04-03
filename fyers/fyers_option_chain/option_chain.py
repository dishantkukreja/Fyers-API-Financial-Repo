import requests
import matplotlib.pyplot as plt
import pandas as pd

# # Your API Key, App Key, and Access Token
client_id = "K731S35ZOK"
APP_KEY = '5E8EIXGMF9-100'
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCbjdpNUZvSGpSYkkwRTVLMHlCZ0Z6ZUlOMzBJWWx5NkU5bHJab3dVVng4ZkF5X1A2RlBCenpnb0RxSkRLcVlNaDJwRVBPYlpab0E2YUhkM2ExQm9ub2k4YkNvcnRMRWFyVWtuc0JqNU5sWDBwRUZVQT0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFM0ODAwNyIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzQzNzI2NjAwLCJpYXQiOjE3NDM2NjI2NjEsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc0MzY2MjY2MSwic3ViIjoiYWNjZXNzX3Rva2VuIn0.fmkd39J7qcL6ABEO5pirpEr00fFHqDc56-rimHlUXEo"

from fyers_apiv3 import fyersModel


fyers = fyersModel.FyersModel(client_id=client_id, token=access_token,is_async=False, log_path="")
data = {
    "symbol":"NSE:TCS-EQ",
    "strikecount":1,
    "timestamp": ""
}
response = fyers.optionchain(data=data);
print(response)
