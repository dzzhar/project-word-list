import requests

api_key = "06d718b5-f5c6-4508-9808-f119f7ddec2a"
word = "potato"
url = f"https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}"

resp = requests.get(url)
definitions = resp.json()

for definition in definitions:
    print(definition)
