import requests
import bibtexparser
from get_dev_key import get_dev_key

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

parser = bibtexparser.bparser.BibTexParser(common_strings=True)

with open('cv.bib','r') as fh:
    txt = fh.read()
    bib_database = parser.parse(txt)


students = ('Jeff', 'Budaiev', 'Bulatek', 'Richardson', 'Yoo', 'Gramze', 'Otter')
for entry in bib_database.entries:

    if "{Ginsburg}" in entry['author'] and 'myname' not in entry['author']:
        entry['author'] = entry['author'].replace("{Ginsburg}", "{\\myname{Ginsburg}}")
    if any(x in entry['author'] for x in students):
        for student in students:
            if 'student' not in entry['author']:
                entry['author'] = entry['author'].replace(f"{{{student}}}", f"{{\\student{{{student}}}}}")



    if 'doi' in entry and 'journal' not in entry:
        print("Attempting to determine Journal for {0}: {1}".format(entry['doi'],
                                                                    entry['ID'])
             )
        query_params = {'q': f'doi:{entry["doi"]}'}
        fields = ['bibtex', 'journal', 'pages', 'eid', 'month', 'year', 'adsurl',
                  'first_author', 'author', 'bibcode', 'volume', 'doi']
    elif 'journal' in entry:
        if 'doi' not in entry:
            if 'eprint' in entry:
                print("Found eprint for {0}".format(entry['eprint']))
                arxivid = entry['eprint'].split("v")[0]
                query_params = {'q': f'arXiv:{arxivid}'}
                fields = ['bibtex', 'journal', 'pages', 'eid', 'month', 'year',
                          'first_author', 'author', 'bibcode', 'adsurl', 'volume']
            elif 'eid' in entry:
                print("Found eid for {0}".format(entry['eid']))
                arxivid = entry['eid'].split(":")[1].split("v")[0]
                query_params = {'q': f'arXiv:{arxivid}'}
                fields = ['bibtex', 'journal', 'pages', 'eid', 'month', 'year',
                          'first_author', 'author', 'bibcode', 'adsurl', 'volume']
            elif 'adsurl' in entry:
                adsurl = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None
                print("Loading journal from ADS URL {0}".format(adsurl))
                query_params = {'q': f'bibcode:{adsurl}'}
                fields = ['bibtex', 'journal', 'pages', 'eid', 'month', 'year', 'adsurl',
                          'first_author', 'author', 'bibcode', 'volume', 'doi']
            else:
                print("Trying to ID article from title {0}".format(entry['title']))
                query_params = {'q': f'title:"{entry["title"].strip("{}")}"'}
                fields = ['bibtex', 'journal', 'pages', 'eid', 'month', 'year', 'adsurl',
                          'first_author', 'author', 'bibcode', 'volume', 'doi']
        else:
            print("Entry {0} is already complete".format(entry['ID']))
            continue
    elif 'eprint' in entry:
        print("Found eprint but no journal for {0}".format(entry['eprint']))
        arxivid = entry['eprint'].split("v")[0]
        query_params = {'q': f'arXiv:{arxivid}'}
        fields = ['bibtex', 'journal', 'pages', 'eid', 'month', 'year',
                  'first_author', 'author', 'bibcode', 'adsurl', 'volume']
    else:
        print("Could not search for entry: {0} because there is no journal or doi"
              .format(entry))
        continue

    # Make API request
    response = requests.get(f"{ADS_API_BASE_URL}/search/query",
                          headers={'Authorization': f'Bearer {ADS_API_TOKEN}'},
                          params={
                              'fl': ','.join(fields),
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

    print(docs, [p['bibcode'] for p in docs], [p.get('adsurl', '') for p in docs])
    if len(docs) == 0:
        print("ERROR: Skipped {0}".format(entry['title']))
        raise
        continue
    print("first article", docs[0])
    assert len(docs) == 1
    article = docs[0]
    try:
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        entry_bibtex = parser.parse(article['bibtex']).entries[0]
    except Exception as ex:
        print("Failed to parse {0} because of {1}"
              .format(entry, ex))
        continue

    for key in ('journal', 'pages', 'eid', 'month', 'year', 'adsurl',
                'volume', 'doi'):
        if key in entry_bibtex:
            if key in entry:
                old = entry[key]
            else:
                old = '[empty]'
            entry[key] = entry_bibtex[key]
            print("Updated {0} from {2} to {1}".format(key, entry[key], old))


with open('cv.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)
