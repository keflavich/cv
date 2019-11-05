import ads
import datetime
from astropy.utils.console import ProgressBar
from get_dev_key import get_dev_key

print("Today is {0}".format(datetime.datetime.now().strftime("%D")))
thisyear = datetime.datetime.now().year

number_of_years = 4
number_of_coauthors = 3 # top 3...

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
          (int(art.year) > 2005)]

print("Found {0} papers matching Ginsburg, A, refereed, astronomy, article".format(len(papers)))

years = [art.year for art in papers]
papers = [y for _,y in sorted(zip(years, papers), key=lambda x:x[0])]

coauthors = [auth for art in papers if (int(art.year) >= thisyear-number_of_years)
             for auth in art.author[:number_of_coauthors]]
coauthor_affils = [(auth,aff) for art in papers if (int(art.year) >= thisyear-number_of_years)
                   for auth,aff in zip(art.author[:number_of_coauthors],
                                       art.aff[:number_of_coauthors])]
coauthor_affils = dict(coauthor_affils)


print("Unique coauthors since {0}: {1}".format(thisyear-number_of_years, len(set(coauthors))))

fullnames = [name for name in coauthors if ',' in name]
lastfirst = [name.split(',') for name in coauthors if ',' in name]
lastfirst = [lf[:2] for lf in lastfirst]
unique_lastfirst = {last: first for last,first in lastfirst}
last_to_affil = {last: coauthor_affils[name] for (last,first),name in zip(lastfirst, fullnames)}

for last, first in unique_lastfirst.items():
    print(", ".join([last,first]) + "\t" + last_to_affil[last])
