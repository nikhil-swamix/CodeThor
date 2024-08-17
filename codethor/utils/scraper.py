import peewee as pw
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import re
from markdownify import markdownify as md


def get_main_container(nodetree: str):
    from selectolax.parser import HTMLParser

    """Find parent of h1 and return nodetree, accepts html string"""
    if isinstance(nodetree, str):
        nodetree = HTMLParser(nodetree)
    default = nodetree.css_first('body,main,article')
    h = nodetree.css_first('h1,h2,h3')
    if h is not None:
        return h.parent.html if h.parent is not None else default.html

    return nodetree.html


def create_browser():
    from playwright.sync_api import Browser
    from playwright.sync_api import sync_playwright

    return sync_playwright().start().webkit.launch()


def get_page(url, fast: bool = True, browser: None = None, sleep=0.2):
    import time
    import requests

    if fast:
        return requests.get(url).text
    else:
        if not browser:
            raise Exception("Browser instance not provided example `sync_playwright().start().webkit.launch()`")
        page = browser.new_page()
        page.goto(url)
        page.wait_for_load_state("load")
        time.sleep(sleep)
        return page.content()


def markdownify(url, fast: bool = True, browser=None, sleep=0.2):
    """main method of module"""
    from html2text import html2text

    contents = get_main_container(get_page(url, fast=fast, browser=browser, sleep=sleep))
    if not contents:
        raise Exception("Page has parsing errors contents=", contents)
    return html2text(contents)


import os


def generate_file_tree(start_path, indent='  '):
    ignores = [".git", "__pycache__", "venv", "node_modules", "build", ".svelte-kit"]
    tree = ''
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in ignores]
        level = root.replace(start_path, '').count(os.sep)
        tree += f'{indent * level}{os.path.basename(root)}/\n'
        sub_indent = indent * (level + 1)
        for file in files:
            if any(ignore in file for ignore in ignores):
                continue
            tree += f'{sub_indent}{file}\n'
    return tree


class ScraperDatabase:
    def __init__(self, db_name):
        self.db = pw.SqliteDatabase(db_name)

        class BaseModel(pw.Model):
            class Meta:
                database = self.db

        class URLIndex(BaseModel):
            url = pw.CharField(unique=True, index=True)
            scraped = pw.BooleanField(default=False)

        class WebPage(BaseModel):
            url = pw.ForeignKeyField(URLIndex, backref='webpages')
            content = pw.TextField()

        self.URLIndex = URLIndex
        self.WebPage = WebPage

        self.db.connect()
        self.db.create_tables([URLIndex, WebPage])


class WebScraper:
    def __init__(self, base_url, ignore_patterns=None):
        self.base_url = base_url
        self.ignore_patterns = ignore_patterns or []
        self.session = requests.Session()
        self.pool = ThreadPoolExecutor(max_workers=4)
        self.db = ScraperDatabase('scraper.db')

    def normalize_url(self, url):
        if url.startswith('/'):
            url = f"{'/'.join(self.base_url.split('/')[:3])}{url}"
        return url.split('#')[0] if '#' in url else url

    def should_ignore(self, url):
        return any(re.match(pattern, url) for pattern in self.ignore_patterns)

    def fetch_html(self, url):
        response = self.session.get(url)
        response.raise_for_status()
        return response.text

    def extract_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        links = {
            self.normalize_url(a['href'])
            for a in soup.find_all('a', href=True)
            if self.base_url in self.normalize_url(a['href']) and not self.should_ignore(a['href'])
        }
        return sorted(links)

    def process_url(self, url):
        html = self.fetch_html(url)
        links = self.extract_links(html)
        for link in links:
            with self.db.db.atomic():
                self.db.URLIndex.get_or_create(url=link)
        print(self.db.URLIndex.select().count())

    def save_content(self, url_index, content):
        markdown_content = md(content)
        with self.db.db.atomic():
            self.db.WebPage.create(url=url_index, content=markdown_content)
            url_index.scraped = True
            url_index.save()

    def run(self):
        unscraped_urls = self.db.URLIndex.select().where(self.db.URLIndex.scraped == False)

        if unscraped_urls.count() == 0:
            # If there are no unscraped URLs, scrape the first URL
            first_url = self.base_url
            with self.db.db.atomic():
                url_index, created = self.db.URLIndex.get_or_create(url=first_url)
            self.process_url(first_url)
        else:
            for url_index in unscraped_urls:
                self.process_url(url_index.url)

        self.db.db.close()


def should_scrape(url, matcher):
    import re

    if not re.match(matcher, url):
        return False
    return True


if __name__ == '__main__':
    # scraper = WebScraper("https://docs.pytest.org/en/stable/explanation/flaky.html")
    # scraper.run()
    seed = "https://playwright.dev/python/docs/intro"
    matcher = r"https://playwright.dev/python/*"
    print(should_scrape(seed, matcher))