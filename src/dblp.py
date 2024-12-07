# %%
import json
import requests

TEMPLATE = "https://dblp.org/search/publ/api?q=toc:db/conf/{conf}/{conf}{year}.bht:&h=1000&format={format}"
CONFERENCE = {
    "USENIX Security": "uss",
    "S&P": "sp",
    "CCS": "ccs",
    "NDSS": "ndss"
}


def get_json(conf, year):
    url = TEMPLATE.format(conf=conf, year=year, format="json")
    res = requests.get(url)
    if res.ok:
        try:
            data = json.loads(res.text)['result']['hits']['hit']
            return data
        except:
            return []
