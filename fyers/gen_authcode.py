# Import the required module from the fyers_apiv3 package
from fyers_apiv3 import fyersModel

# Replace these values with your actual API credentials
client_id = "5E8EIXGMF9-100"
secret_key = "K731S35ZOK"
redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
response_type = "code"  
state = "sample_state"

# Create a session model with the provided credentials
session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type
)

# Generate the auth code using the session model
response = session.generate_authcode()

# Print the auth code received in the response
print(response)

