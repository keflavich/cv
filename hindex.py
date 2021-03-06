import ads
import datetime
from astropy.utils.console import ProgressBar
import bibtexparser
from get_dev_key import get_dev_key

parser = bibtexparser.bparser.BibTexParser(common_strings=True)

print("hindex")
print("Today is {0}".format(datetime.datetime.now().strftime("%D")))

ads.config.token = get_dev_key()

mypapers = ads.SearchQuery(author='Ginsburg, A', rows=900, fl=['id', 'bibcode',
                                                               'title',
                                                               'citation_count',
                                                               'property',
                                                               'database',
                                                               'first_author',
                                                               'first_author_norm',
                                                               'pubdate',
                                                               'identifier',
                                                               'author',
                                                               'year',
                                                               'pubdate', ])
mypapers.execute()

print("Found {0} papers matching Ginsburg, A".format(len(mypapers.articles)))

ncites_total = sum([art.citation_count for art in ProgressBar(mypapers.articles)
                    if art.property is not None])

#allpapers = [art for art in ProgressBar(mypapers.articles)
#             if ('astronomy' in art.database) and
#             (int(art.year) > 2005)]

papers = [art for art in ProgressBar(mypapers.articles)
          if art.property is not None and
          ('REFEREED' in art.property) and
          ('ARTICLE' in art.property) and
          ('astronomy' in art.database) and
          not any(('Erratum' in xx for xx in art.title)) and
          (int(art.year) > 2005)]

print("Found {0} papers matching Ginsburg, A, refereed, astronomy, article".format(len(papers)))

citations = sorted([art.citation_count for art in ProgressBar(papers)])

full_paper_info = [(art.first_author, art.first_author_norm,
                    art.pubdate, art.bibcode, art.id,
                    art.identifier,
                    art.author,
                    art.title, art.citation_count)
                   for art in ProgressBar(papers)]

print("Found {0} total citations to refereed articles.".format(sum(citations)))

h_index = 0
for ii, nc in enumerate(citations[::-1]):
    if ii+1 > nc:
        h_index = ii
        break

citedict = {"{3}: {0}, {1}{2}".format(art.title[0],
                                      art.first_author,
                                      art.pubdate,
                                      art.citation_count):
            art.citation_count for art in papers}
citelist = sorted(citedict, key=lambda x: citedict[x])

first_author = {key:val for key,val in citedict.items()
                if 'Ginsburg' in key}

print("Computed H-index {0}".format(h_index))
print()
print("Titles contributing to H-index: ")
print("\n".join([description for description,citation_count in citedict.items() if citation_count >= h_index]))


with open('hindex.tex', 'w') as fh:
    fh.write("\\usepackage{xspace}\n")
    fh.write("\\newcommand{{\\nrefereed}}{{{0}\\xspace}}\n".format(len(papers)))
    fh.write("\\newcommand{{\\ntotalpapers}}{{{0}\\xspace}}\n".format(len(mypapers.articles)))
    fh.write("\\newcommand{{\\ncites}}{{{0}\\xspace}} % refereed\n".format(sum(citations)))
    fh.write("\\newcommand{{\\ncitestotal}}{{{0}\\xspace}}\n".format(ncites_total))
    fh.write("\\newcommand{{\\hindex}}{{{0}\\xspace}}\n".format(h_index))
    fh.write("\\newcommand{{\\nfirst}}{{{0}\\xspace}}\n".format(len(first_author)))
    fh.write("\\newcommand{{\\ncitesfirst}}{{{0}\\xspace}}\n".format(sum(first_author.values())))




with open('cv.bib','r') as fh:
    bib_database = bibtexparser.load(fh, parser=parser)

print()
print("cv.bib matches: (blank means good)")
matches = {}
for entry in bib_database.entries:
    doi = entry.get('doi')
    bibcode = entry['adsurl'].split("/")[-1].replace("%26","&") if 'adsurl' in entry else None
    match = [art for art in papers if doi in art.identifier or bibcode in art.identifier]
    if len(match) == 0:
        print("No match for {0}, which is in cv.bib, in downloaded papers".format(entry.get('title')))
    elif len(match) > 1:
        print("Multiple matches for {0} among downloaded papers".format(entry.get('title')))
    else:
        matches[bibcode] = match[0]

print()
print("ADS search matches (blank means good):")

reverse_matches = {}
for art in papers:
    bibcode = art.bibcode

    entry['adsurl'].split("/")[-1] if 'adsurl' in entry else None
    match = [entry for entry in bib_database.entries
             if any(doi in entry.get('doi',[]) for doi in art.identifier) or
             bibcode in entry.get('adsurl', '').replace("%26","&")
            ]
    if len(match) == 0:
        print("No match for {0} in cv.bib: {1}".format(art.title, art.bibcode))
    elif len(match) > 1:
        print("Multiple matches for {0} in cv.bib.  doi: {1} bibcode: {2}".format(art.title, art.identifier, bibcode))
        raise ValueError("Multiple matches!")
    else:
        reverse_matches[bibcode] = match[0]
