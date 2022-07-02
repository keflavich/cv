import ads
import bibtexparser
from get_dev_key import get_dev_key


parser = bibtexparser.bparser.BibTexParser(common_strings=True)

ads.config.token = get_dev_key()

with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

firstauthor_entries = []
nonfirstauthor_entries = []

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
        raise
        continue
    #print(paper.articles, paper.articles[0])
    print(pfx, paper.articles[0].bibcode, paper.articles[0].citation_count)
    if len(paper.articles) > 1:
        arts = [art for art in paper.articles if 'tmp' not in art.bibcode]
        if len(arts) == 1:
            art = arts[0]
        else:
            for ii in range(len(paper.articles)):
                print(f"Article {ii} id: {paper.articles[ii].id} author: {paper.articles[ii].author}")
            raise ValueError("Found multiple articles.")
    else:
        art = paper.articles[0]
    entry['citations'] = "{0}".format(art.citation_count)

    total_cites += art.citation_count
    if "ginsburg" in art.author[0].lower():
        total_firstauthor_cites += art.citation_count
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
    fh.write("\input{hindex.tex}")
    #fh.write("\\newcommand{{\\ncitestotal}}{{{0}}}\n".format(total_cites))
    #fh.write("\\newcommand{{\\nfirstcitestotal}}{{{0}}}\n".format(total_firstauthor_cites))
