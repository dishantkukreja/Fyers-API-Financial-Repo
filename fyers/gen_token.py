# Import the required module from the fyers_apiv3 package
from fyers_apiv3 import fyersModel

# Define your Fyers API credentials
client_id = "5E8EIXGMF9-100"
secret_key = "K731S35ZOK"
redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html" # Replace with your redirect URI
response_type = "code" 
grant_type = "authorization_code"  

# The authorization code received from Fyers after the user grants access
auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiI1RThFSVhHTUY5IiwidXVpZCI6IjQxYTQxMDhmMDQ1NjQxNjRhMzI0ZGZmMWE5YWZiNzFmIiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IlhTNDgwMDciLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJmMDkzM2FhMjY4NjJkNGFmMmRkNDk3NWE3MmNkZGI2OTNiNThhOTJkMzcyOWUyYmYzYjdiMGFkYyIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzQzNjkyNjIwLCJpYXQiOjE3NDM2NjI2MjAsImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc0MzY2MjYyMCwic3ViIjoiYXV0aF9jb2RlIn0.I2sSAwIFV63jU09cca-JAtykBX4tSPK1HIRhv5o4z70"

# Create a session object to handle the Fyers API authentication and token generation
session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key, 
    redirect_uri=redirect_uri, 
    response_type=response_type, 
    grant_type=grant_type
)

# Set the authorization code in the session object
session.set_token(auth_code)

# Generate the access token using the authorization code
response = session.generate_token()

# Print the response, which should contain the access token and other details
print(response)
