import ads
import bibtexparser
from get_dev_key import get_dev_key


ads.config.token = get_dev_key()

with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh)

total_cites = 0
total_firstauthor_cites = 0

for entry in bib_database.entries:
    if 'doi' in entry:
        paper = ads.SearchQuery(doi=entry['doi'], fl=['citation_count', 'author', 'year', 'id', 'bibcode'])
        pfx = "Loaded from doi {0}".format(entry['doi'])
    elif 'adsurl' in entry:
        adsurl = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None
        paper = ads.SearchQuery(bibcode=adsurl, fl=['citation_count', 'author', 'year', 'id', 'bibcode'])
        pfx = "Loaded from adsurl {0}".format(adsurl)
    else:
        print("Skipped {0} because it has no DOI or ADSURL".format(entry['title']))
        continue

    paper.execute()

    ratelimits = paper.response.get_ratelimits()
    if int(ratelimits['remaining']) < 1:
        raise ValueError("Rate limit of ADS queries exceeded.")

    if len(paper.articles) == 0:
        print("ERROR: Skipping {0} because it wasn't found.".format(entry['title']))
        continue
    #print(paper.articles, paper.articles[0])
    print(pfx, paper.articles[0].bibcode, paper.articles[0].citation_count)
    assert len(paper.articles) == 1
    entry['citations'] = "{0}".format(paper.articles[0].citation_count)

    total_cites += paper.articles[0].citation_count
    if "ginsburg" in paper.articles[0].author[0].lower():
        total_firstauthor_cites += paper.articles[0].citation_count

with open('cv_cites.bib','w') as fh:
    bibtexparser.dump(bib_database, fh)

with open('ncites.tex', 'w') as fh:
    fh.write("\input{hindex.tex}")
    #fh.write("\\newcommand{{\\ncitestotal}}{{{0}}}\n".format(total_cites))
    #fh.write("\\newcommand{{\\nfirstcitestotal}}{{{0}}}\n".format(total_firstauthor_cites))
