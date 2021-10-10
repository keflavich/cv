import bibtexparser
import json
from urllib.parse import urlencode, unquote
from get_dev_key import get_dev_key
import requests

token = get_dev_key()

parser = bibtexparser.bparser.BibTexParser(common_strings=True)

with open('cv.bib','r') as fh:
    txt = fh.read()
    bib_database = parser.parse(txt)

adsurls = [entry['adsurl'].split("/")[-1].replace("%26","&") for entry in
           bib_database.entries if 'adsurl' in entry]


headers = {'Authorization': 'Bearer ' + token}

library_id = 'CFJYpXQMRTqHEAe0jOL3VQ'
library_url = f'https://api.adsabs.harvard.edu/v1/biblib/libraries/{library_id}'

S = requests.Session()
qq = {'rows':500}
response = S.get(library_url, headers=headers, params=qq)
response.raise_for_status()
js = response.json()
print(len(js['documents']), qq)

all_docs = js['documents']


# curl -H "Content-Type: big-query/csv" {token_header} {base_url}/bigquery?{urlparams} -X POST -d {payload}
headers['Content-Type'] = 'big-query/csv'
search_url = "https://api.adsabs.harvard.edu/v1/search/bigquery"
params = {'q': '*:*', 'fl': 'bibcode', 'fq': 'property:refereed', 'rows': 500}
data = 'bibcode\n' + '\n'.join(js['documents'])
response = S.post(search_url, data=data, params=params, headers=headers)
response.raise_for_status()

bibcodes = [xx['bibcode'] for xx in response.json()['response']['docs']]
refereed_docs = bibcodes


new_pubs = list(set(refereed_docs) - set(adsurls))


headers = {'Authorization': 'Bearer ' + token, "Content-type": "application/json"}
bibtexurl = "https://api.adsabs.harvard.edu/v1/export/bibtex"

with open('cv.bib', 'a') as fh:
    response = S.post(bibtexurl, headers=headers, data= json.dumps({"bibcode": new_pubs}))
    response.raise_for_status()
    fh.write(response.json()['export'])
