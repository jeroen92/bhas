#!/usr/bin/env python

import requests 
import json

r = requests.get("https://stat.ripe.net/data/geoloc/data.json?resource=1103")
for location in json.loads(r.text)['data']['locations']:
    print location['country']
