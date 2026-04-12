import os
import sys

from dhan_api import get_historical_data

access_token = os.environ.get("DHAN_ACCESS_TOKEN", "dummy")
client_id = os.environ.get("DHAN_CLIENT_ID", "dummy")

# Let's test what Dhan actually returns
print("Testing historical fetch for 54878 (24650 CE)...")
res1 = get_historical_data(access_token, client_id, "54878", "NSE_FNO", days=12, interval="D")
print("Result NSE_FNO 'D':", res1)

res2 = get_historical_data(access_token, client_id, "54878", "NSE_FNO", days=12, interval="1")
print("Result NSE_FNO '1':", res2)

res3 = get_historical_data(access_token, client_id, "54878", "IDX_I", days=12, interval="D")
print("Result IDX_I 'D':", res3)
