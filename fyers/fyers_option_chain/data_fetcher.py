from fyers_apiv3 import fyersModel
import logging

class FyersAPI:
    def __init__(self, client_id, access_token):
        self.fyers = fyersModel.FyersModel(
            client_id=client_id,
            token=access_token,
            is_async=False
        )

    def fetch_option_chain_data(self, symbol, strikecount, expiry=None):
        # 1) Fetch list of expiries without empty timestamp
        payload = {"symbol": symbol, "strikecount": strikecount}
        resp0 = self.fyers.optionchain(data=payload)
        if resp0.get('code') != 200 or not resp0['data'].get('expiryData'):
            logging.error("FyersAPI: failed to fetch expiry list")
            return None

        # 2) Choose expiry
        expiry_ts = expiry or resp0['data']['expiryData'][0]['expiry']
        logging.info(f"Using expiry timestamp: {expiry_ts}")

        # 3) Fetch chain for chosen expiry
        payload['timestamp'] = expiry_ts
        resp = self.fyers.optionchain(data=payload)
        if resp.get('code') != 200:
            logging.error(f"FyersAPI: error fetching chain for expiry {expiry_ts}: {resp.get('message')}")
            return None
        return resp['data']
