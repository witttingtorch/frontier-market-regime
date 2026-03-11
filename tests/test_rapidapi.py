import requests
import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv('RAPIDAPI_KEY')

url = "https://nairobi-stock-exchange-nse.p.rapidapi.com/stocks"

headers = {
    "X-RapidAPI-Key": key,
    "X-RapidAPI-Host": "nairobi-stock-exchange-nse.p.rapidapi.com"
}

response = requests.get(url, headers=headers)
print(f"Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✓ Success! Found {len(data)} stocks")
    print(f"First stock: {data[0]['name'] if data else 'None'}")
else:
    print(f"✗ Error: {response.text}")
