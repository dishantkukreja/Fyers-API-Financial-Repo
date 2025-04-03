# data_fetcher.py
from fyers_apiv3 import fyersModel
import time
import logging

class FyersAPI:
    def __init__(self, client_id, access_token):
        self.client_id = client_id
        self.access_token = access_token
        self.fyers = fyersModel.FyersModel(client_id=self.client_id, token=self.access_token, is_async=False)

    def fetch_option_chain_data(self, symbol="NSE:NIFTY50-INDEX", strikecount=1):
        data = {
            "symbol": symbol,
            "strikecount": strikecount,
            "timestamp": ""
        }
        
        # Fetch option chain data to get expiry information
        response = self.fyers.optionchain(data=data)
        if response['code'] == 200:
            # Extract expiry data from the response
            expiry_dates = response['data']['expiryData']
            
            if expiry_dates:
                # Choose the first expiry date from the available expiry data
                expiry_timestamp = expiry_dates[0]['expiry']  # This is the valid expiry timestamp
                
                # Add the expiry timestamp to the request data
                data['expiry'] = expiry_timestamp
                logging.info(f"Using expiry timestamp: {expiry_timestamp}")
                
                # # Now re-fetch the option chain data with the expiry included
                # response = self.fyers.optionchain(data=data)
                
                return response['data']
            else:
                logging.error("No expiry data found in the response")
                return None
        else:
            logging.error(f"Error fetching data: {response['message']}")
            return None
