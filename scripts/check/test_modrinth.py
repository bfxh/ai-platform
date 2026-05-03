import urllib.request, json

test_mods = ['twilightforest', 'twilight-forest', 'apotheosis', 'catalog']
for m in test_mods:
    try:
        url = 'https://api.modrinth.com/v2/project/' + m
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        print(m + ': ' + data['title'])
    except Exception as e:
        print(m + ': ERROR - ' + str(e))
