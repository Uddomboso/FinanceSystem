import requests

base_url = "https://api.exchangerate.host"

def convert(amount, from_curr, to_curr):
    try:
        url = f"{base_url}/convert"
        params = {
            "from": from_curr,
            "to": to_curr,
            "amount": amount
        }
        r = requests.get(url, params=params)
        data = r.json()
        return round(data["result"], 2)
    except:
        return None

def get_rates(base="USD"):
    try:
        url = f"{base_url}/latest"
        r = requests.get(url, params={"base": base})
        data = r.json()
        return data["rates"]
    except:
        return {}
