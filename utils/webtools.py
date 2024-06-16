import time


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


if __name__ == '__main__':

    browser = create_browser()

    url = "https://ai.google.dev/gemini-api/docs/api-overview#chat"
    print(markdownify(url, fast=True, browser=browser))

    # browser.close()
    # print(BeautifulSoup(raw, "lxml"))
    # result = url_to_text(url, sanitize=[])
    # print(result)
    # get_page("https://github.com/mahseema/awesome-ai-tools?tab=readme-ov-file")
