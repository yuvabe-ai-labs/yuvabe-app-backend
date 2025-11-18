import requests

url = "https://api.quotable.io/quotes?limit=3"

response = requests.get(url, verify=False)

if response.status_code == 200:
    data = response.json()
    print(data)
else:
    print(f"Failed to retrieve data: {response.status_code}")
