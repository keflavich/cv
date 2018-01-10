import ads
import datetime
from astropy.utils.console import ProgressBar
from get_dev_key import get_dev_key

print("Today is {0}".format(datetime.datetime.now().strftime("%D")))

ads.config.token = get_dev_key()

mypapers = ads.SearchQuery(author='Ginsburg, A', rows=300)
mypapers.execute()

print("Found {0} papers matching Ginsburg, A".format(len(mypapers.articles)))

#allpapers = [art for art in ProgressBar(mypapers.articles)
#             if ('astronomy' in art.database) and
#             (int(art.year) > 2005)]

papers = [art for art in ProgressBar(mypapers.articles)
          if ('REFEREED' in art.property) and
          ('ARTICLE' in art.property) and
          ('astronomy' in art.database) and
          not any(('Erratum' in xx for xx in art.title)) and
          (int(art.year) > 2005)]

print("Found {0} papers matching Ginsburg, A, refereed, astronomy, article".format(len(papers)))

citations = sorted([art.citation_count for art in ProgressBar(papers)])

full_paper_info = [(art.first_author, art.first_author_norm,
                    art.pubdate, art.bibcode, art.id,
                    #art.identifier,
                    #art.author,
                    art.title, art.citation_count)
                   for art in ProgressBar(papers)]

print("Found {0} total citations to refereed articles.".format(sum(citations)))

h_index = 0
for ii, nc in enumerate(citations[::-1]):
    if ii+1 > nc:
        h_index = ii
        break

print("Computed H-index {0}".format(h_index))

with open('hindex.tex', 'w') as fh:
    fh.write("\\newcommand{{\\nrefereed}}{{{0}}}\n".format(len(papers)))
    fh.write("\\newcommand{{\\ntotalpapers}}{{{0}}}\n".format(len(mypapers.articles)))
    fh.write("\\newcommand{{\\ncites}}{{{0}}}\n".format(sum(citations)))
    fh.write("\\newcommand{{\\hindex}}{{{0}}}\n".format(h_index))
