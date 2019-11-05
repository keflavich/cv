import ads
import bibtexparser
from get_dev_key import get_dev_key

ads.config.token = get_dev_key()

parser = bibtexparser.bparser.BibTexParser(common_strings=True)

with open('cv.bib','r') as fh:
    txt = fh.read()
    bib_database = parser.parse(txt)


for entry in bib_database.entries:

    if "{Ginsburg}" in entry['author'] and 'myname' not in entry['author']:
        entry['author'] = entry['author'].replace("{Ginsburg}", "{\\myname{Ginsburg}}")


    if 'doi' in entry and 'journal' not in entry:
        print("Attempting to determine Journal for {0}: {1}".format(entry['doi'],
                                                                    entry['ID'])
             )
        paper = ads.SearchQuery(doi=entry['doi'], fl=['bibtex', 'journal',
                                                      'pages', 'eid', 'month',
                                                      'year', 'adsurl',
                                                      'first_author', 'author',
                                                      'bibcode', 'articles',
                                                      'volume', 'doi'])
    elif 'journal' in entry:
        if 'doi' not in entry:
            if 'eprint' in entry:
                print("Found eprint for {0}".format(entry['eprint']))
                arxivid = entry['eprint'].split("v")[0]
                paper = ads.SearchQuery(arXiv=arxivid, fl=['bibtex', 'journal',
                                                           'pages', 'eid', 'month',
                                                           'articles', 'year',
                                                           'first_author', 'author', 'bibcode',
                                                           'adsurl', 'volume'])
            elif 'eid' in entry:
                print("Found eid for {0}".format(entry['eid']))
                arxivid = entry['eid'].split(":")[1].split("v")[0]
                paper = ads.SearchQuery(arXiv=arxivid, fl=['bibtex', 'journal',
                                                           'pages', 'eid', 'month',
                                                           'articles', 'year',
                                                           'first_author', 'author', 'bibcode',
                                                           'adsurl', 'volume'])
            elif 'adsurl' in entry:
                adsurl = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None
                print("Loading journal from ADS URL {0}".format(adsurl))
                paper = ads.SearchQuery(bibcode=adsurl,
                                        fl=['bibtex', 'journal', 'pages', 'eid',
                                            'month', 'year', 'adsurl', 'first_author',
                                            'author', 'bibcode', 'articles', 'volume',
                                            'doi'])
            else:
                print("Trying to ID article from title {0}".format(entry['title']))
                paper = ads.SearchQuery(title=entry['title'].strip('{}'),
                                        fl=['bibtex', 'journal', 'pages', 'eid',
                                            'month', 'year', 'adsurl', 'first_author',
                                            'author', 'bibcode', 'articles', 'volume',
                                            'doi'])
        else:
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
    else:
        print("Could not search for entry: {0} because there is no journal or doi"
              .format(entry))
        continue
    paper.execute()

    ratelimits = paper.response.get_ratelimits()
    if int(ratelimits['remaining']) < 1:
        raise ValueError("Rate limit of ADS queries exceeded.")

    print(paper.articles, [p.bibcode for p in paper.articles], [p.adsurl for p in paper.articles if hasattr(p,'adsurl')])
    if len(paper.articles) == 0:
        print("ERROR: Skipped {0}".format(entry['title']))
        raise
        continue
    print("first article", paper.articles[0],)
    assert len(paper.articles) == 1
    article = paper.articles[0]
    try:
        parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        entry_bibtex = parser.parse(article.bibtex).entries[0]
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
