from kiteconnect import KiteConnect
import os

def get_kite_client():
    api_key = os.getenv("KITE_API_KEY")
    access_token = os.getenv("KITE_ACCESS_TOKEN")
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(access_token)
    return kite
