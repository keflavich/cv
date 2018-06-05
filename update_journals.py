import ads
import bibtexparser
from get_dev_key import get_dev_key

ads.config.token = get_dev_key()

parser = bibtexparser.bparser.BibTexParser(common_strings=True)

with open('cv.bib','r') as fh:
    txt = fh.read()
    bib_database = parser.parse(txt)


for entry in bib_database.entries:
    if 'doi' in entry and 'journal' not in entry:
        print("Attempting to determine Journal for {0}: {1}".format(entry['doi'],
                                                                    entry['ID'])
             )
        paper = ads.SearchQuery(doi=entry['doi'], fl=['bibtex', 'journal',
                                                      'pages', 'eid', 'month',
                                                      'year', 'adsurl',
                                                      'first_author', 'author',
                                                      'bibcode', 'articles',
                                                      'volume'])
        paper.execute()
    elif 'journal' in entry:
        print("Entry {0} is already complete".format(entry['ID']))
        continue
    elif 'eprint' in entry:
        print("Found eprint but no journal for {0}".format(entry['eprint']))
        arxivid = entry['eprint'].split("v")[0]
        paper = ads.SearchQuery(arXiv=arxivid, fl=['bibtex', 'journal',
                                                   'pages', 'eid', 'month',
                                                   'articles', 'year',
                                                   'first_author', 'author', 'bibcode',
                                                   'adsurl', 'volume'])
        paper.execute()
    else:
        print("Could not search for entry: {0} because there is no journal or doi"
              .format(entry))
        continue

    ratelimits = paper.response.get_ratelimits()
    if int(ratelimits['remaining']) < 1:
        raise ValueError("Rate limit of ADS queries exceeded.")

    print(paper.articles, paper.articles[0])
    assert len(paper.articles) == 1
    article = paper.articles[0]
    try:
        entry_bibtex = parser.parse(article.bibtex).entries[0]
    except Exception as ex:
        print("Failed to parse {0} because of {1}"
              .format(entry, ex))
        continue

    for key in ('journal', 'pages', 'eid', 'month', 'year', 'adsurl',
                'volume'):
        if key in entry_bibtex:
            entry[key] = entry_bibtex[key]
            print("Updated {0} to {1}".format(key, entry[key]))


with open('cv.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)
