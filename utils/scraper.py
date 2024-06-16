import peewee as pw
from .webtools import markdownify, get_page
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re


import peewee as pw

class ScraperDatabase:
    def __init__(self, db_name):
        self.db = pw.SqliteDatabase(db_name)

        class BaseModel(pw.Model):
            class Meta:
                database = self.db

        class ExplorerIndex(BaseModel):
            url = pw.CharField(unique=True, index=True)
            is_scraped = pw.BooleanField(default=False)

        class WebPage(BaseModel):
            url = pw.ForeignKeyField(ExplorerIndex, backref='webpages')
            md = pw.TextField()

        self.ExplorerIndex = ExplorerIndex
        self.WebPage = WebPage

        self.db.connect()
        self.db.create_tables([ExplorerIndex, WebPage])

# Example usage:
# scraper_db = ScraperDatabase('../db/my_database.db')


class Scraper:

    def __init__(self, base, ignores=[]):
        self.base = base
        self.ignores = ignores
        self.session = requests.Session()
        self.pool = ThreadPoolExecutor(max_workers=4)
        self.db = db
        db.connect()
        db.create_tables([ExplorerIndex, WebPage])

    def normalize_url(self, url):
        if url.startswith("/"):
            domain_with_proto = "/".join(self.base.split("/")[:3])
            url = domain_with_proto + url
            # print(domain_with_proto,url)

        if "#" in url:
            url = url.split("#")[0]

        # if not url.startswith("/"):
        #     url = self.base + url
        return url

    def is_pattern_matched(self, url: str):
        if self.ignores:
            for ignore in self.ignores:
                # print(f"Skipping {ignore} {re.match(ignore, url)} | {url}")
                if re.match(ignore, url):
                    return False
        return re.match(self.base, url)

    def find_links(self, html: str):
        soup = BeautifulSoup(html, 'html.parser')
        links = [self.normalize_url(l['href']) for l in soup.find_all('a') if l.get('href')]
        links = filter(lambda x: self.is_pattern_matched(x) if x else False, links)
        return sorted([*set(links)])

    def process_url(self, url):
        html = get_page(url)
        links = self.find_links(html)
        for link in links:
            try:
                ExplorerIndex.create(url=link)
            except pw.IntegrityError:
                pass
        # count
        print(ExplorerIndex.select().count())

    def save_to_db(self, explorer_index, md_content):
        WebPage.create(url=explorer_index, md=md_content)
        explorer_index.is_scraped = True
        explorer_index.save()

    def run(self):
        for i in ExplorerIndex.select().where(ExplorerIndex.is_scraped == False):
            self.process_url(i.url)


        self.db.close()


if __name__ == '__main__':

    scraper = Scraper("https://capacitorjs.com/docs/", ignores=[r".+/v[0-9]+", r".+/updating.+"])
    # scraper.process_url("https://capacitorjs.com/docs/")
    scraper.run()
    # for u in scraper.find_links("https://capacitorjs.com/docs/"):
    #     print(u)
    #     # ...
    # scraper.run()
