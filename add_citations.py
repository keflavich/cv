import ads
import bibtexparser
from get_dev_key import get_dev_key


ads.config.token = get_dev_key()

with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh)


for entry in bib_database.entries:
    if 'doi' in entry:
        paper = ads.SearchQuery(doi=entry['doi'])
        paper.execute()
        print(paper.articles, paper.articles[0])
        assert len(paper.articles) == 1
        entry['citations'] = "{0}".format(paper.articles[0].citation_count)

with open('cv_cites.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)
