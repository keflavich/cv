import ads
import datetime
from astropy.utils.console import ProgressBar
from get_dev_key import get_dev_key

print("Today is {0}".format(datetime.datetime.now().strftime("%D")))
thisyear = datetime.datetime.now().year

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

coauthors = [auth for art in papers if (int(art.year) >= thisyear-4)
             for auth in art.author[:3]]

print("Unique coauthors since {0}: {1}".format(thisyear-4, len(set(coauthors))))

lastfirst = [name.split(',') for name in coauthors if ',' in name]
lastfirst = [lf[:2] for lf in lastfirst]
unique_lastfirst = {last: first for last,first in lastfirst}

for last, first in unique_lastfirst.items():
    print(", ".join([last,first]))
