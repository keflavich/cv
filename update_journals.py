import ads
import bibtexparser
from get_dev_key import get_dev_key

ads.config.token = get_dev_key()

with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh)


for entry in bib_database.entries:
    if 'doi' in entry and 'journal' not in entry:
        print("Attempting to determine Journal for {0}: {1}".format(entry['doi'],
                                                                    entry['ID'])
             )
        paper = ads.SearchQuery(doi=entry['doi'])
        paper.execute()
        print(paper.articles, paper.articles[0])
        assert len(paper.articles) == 1
        article = paper.articles[0]
        entry_bibtex = bibtexparser.loads(article.bibtex).entries[0]
        for key in ('journal', 'pages', 'eid', 'month', 'year', 'adsurl',
                    'volume'):
            if key in entry_bibtex:
                entry[key] = entry_bibtex[key]
                print("Updated {0} to {1}".format(key, entry[key]))
    elif 'journal' in entry:
        print("Entry {0} is already complete".format(entry['ID']))
    else:
        print("Could not search for entry: {0}".format(entry))

with open('cv.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)
