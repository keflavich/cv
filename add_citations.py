import ads
import os
import bibtexparser
import re

def get_dev_key():

    ads_dev_key_filename = os.path.abspath(os.path.expanduser('~/.ads/dev_key'))

    if os.path.exists(ads_dev_key_filename):
        with open(ads_dev_key_filename, 'r') as fp:
            dev_key = fp.readline().rstrip()

        return dev_key

    if 'ADS_DEV_KEY' in os.environ:
        return os.environ['ADS_DEV_KEY']

    raise IOError("no ADS API key found in ~/.ads/dev_key")


ads.config.token = get_dev_key()

with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh)


for entry in bib_database.entries:
    paper = ads.SearchQuery(doi=entry['doi'])
    paper.execute()
    print(paper.articles, paper.articles[0])
    assert len(paper.articles) == 1
    entry['citations'] = paper.articles[0].citation_count

with open('cv_cites.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)
