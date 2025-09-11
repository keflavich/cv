import requests
import bibtexparser
from get_dev_key import get_dev_key


parser = bibtexparser.bparser.BibTexParser(common_strings=True)

# ADS API configuration
ADS_API_BASE_URL = "https://api.adsabs.harvard.edu/v1"
ADS_API_TOKEN = get_dev_key()

def get_rate_limits(response_headers):
    """
    Extract rate limit information from response headers
    """
    return {
        'limit': response_headers.get('X-RateLimit-Limit', '0'),
        'remaining': response_headers.get('X-RateLimit-Remaining', '0'),
        'reset': response_headers.get('X-RateLimit-Reset', '0')
    }

with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

firstauthor_entries = []
nonfirstauthor_entries = []

total_cites = 0
total_firstauthor_cites = 0

for entry in bib_database.entries:
    if 'doi' in entry:
        query_params = {'q': f'doi:{entry["doi"]}'}
        pfx = "Loaded from doi {0}".format(entry['doi'])
    elif 'adsurl' in entry:
        adsurl = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None
        query_params = {'q': f'bibcode:{adsurl}'}
        pfx = "Loaded from adsurl {0}".format(adsurl)
    else:
        print("Skipped {0} because it has no DOI or ADSURL".format(entry['title']))
        continue

    # Make API request
    response = requests.get(f"{ADS_API_BASE_URL}/search/query",
                          headers={'Authorization': f'Bearer {ADS_API_TOKEN}'},
                          params={
                              'fl': 'citation_count,author,year,id,bibcode',
                              'rows': 10,
                              **query_params
                          })

    if response.status_code != 200:
        print(f"ERROR: API request failed with status {response.status_code}: {response.text}")
        continue

    ratelimits = get_rate_limits(response.headers)
    if int(ratelimits['remaining']) < 1:
        raise ValueError("Rate limit of ADS queries exceeded.")

    result = response.json()
    docs = result.get('response', {}).get('docs', [])

    if len(docs) == 0:
        print("ERROR: Skipping {0} because it wasn't found.".format(entry['title']))
        raise
        continue

    print(pfx, docs[0]['bibcode'], docs[0]['citation_count'])
    if len(docs) > 1:
        filtered_docs = [doc for doc in docs if 'tmp' not in doc['bibcode']]
        if len(filtered_docs) == 1:
            art = filtered_docs[0]
        else:
            for ii in range(len(docs)):
                print(f"Article {ii} id: {docs[ii]['id']} author: {docs[ii]['author']}")
            raise ValueError("Found multiple articles.")
    else:
        art = docs[0]
    entry['citations'] = "{0}".format(art['citation_count'])

    # special case for pyspeckit
    if 'doi' in entry and entry['doi'] == "10.3847/1538-3881/ac695a":
        ps_response = requests.get(f"{ADS_API_BASE_URL}/search/query",
                                  headers={'Authorization': f'Bearer {ADS_API_TOKEN}'},
                                  params={
                                      'q': 'bibcode:2011ascl.soft09001G',
                                      'fl': 'citation_count,author,year,id,bibcode',
                                      'rows': 1
                                  })
        if ps_response.status_code == 200:
            ps_result = ps_response.json()
            ps_docs = ps_result.get('response', {}).get('docs', [])
            if ps_docs:
                entry['citations'] = "{0}".format(ps_docs[0]['citation_count'])

    total_cites += art['citation_count']
    if "ginsburg" in art['author'][0].lower():
        total_firstauthor_cites += art['citation_count']
        firstauthor_entries.append(entry)
    else:
        nonfirstauthor_entries.append(entry)

firstauthor_database = bibtexparser.bibdatabase.BibDatabase()
firstauthor_database.entries = firstauthor_entries
nonfirstauthor_database = bibtexparser.bibdatabase.BibDatabase()
nonfirstauthor_database.entries = nonfirstauthor_entries

with open('cv_cites.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)

with open('cv_firstauthor_cites.bib','w') as fh:
    bibtexparser.dump(firstauthor_database, fh)

with open('cv_nonfirstauthor_cites.bib','w') as fh:
    bibtexparser.dump(nonfirstauthor_database, fh)

with open('ncites.tex', 'w') as fh:
    fh.write(r"\input{hindex.tex}")
    #fh.write("\\newcommand{{\\ncitestotal}}{{{0}}}\n".format(total_cites))
    #fh.write("\\newcommand{{\\nfirstcitestotal}}{{{0}}}\n".format(total_firstauthor_cites))
