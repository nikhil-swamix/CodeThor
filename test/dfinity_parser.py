from concurrent.futures import ThreadPoolExecutor
from selectolax.parser import HTMLParser
import requests
import json, time
import chromadb

client = chromadb.PersistentClient("chroma.db")

collection = client.get_or_create_collection("dfinity_forum")


def parse_post(slug, id, persist=True):
    try:
        url = f"https://forum.dfinity.org/t/{slug}/{id}.rss"
        if collection.get(ids=[id])["ids"]:
            print("ALREADY PARSED", id)
            return False
        print("PARSING", url)
        resp = requests.get(url)
        tree = HTMLParser(resp.text)
        desc = tree.css_first("description").text()
        title = tree.css_first("title").text()
        link = tree.css_first("link").text()
        r = {"id": id, "title": title, "description": desc, "link": link, "slug": slug}
        if persist:
            persist_data(r)
        return r
    except Exception as e:
        print("parse post", e)


def persist_data(data):
    print("PERSISTING", data["id"], "COUNT:", collection.count())
    collection.add(documents=[data["description"]], ids=[data["id"]])


def id_explorer(page=0):
    global BREAKSIGNAL, POOL
    if BREAKSIGNAL:
        return tuple()
    URL = f"https://forum.dfinity.org/latest.json?no_definitions=true&page={page}"
    resp = requests.get(URL)
    print(
        "EXPLORED",
        resp.status_code,
        URL,
    )
    if not resp.json().get("topic_list").get("topics"):
        print("END", resp.json())
        BREAKSIGNAL = True
    # topic_list.topics[id]
    return tuple((topic['slug'], str(topic["id"])) for topic in resp.json()["topic_list"]["topics"])


def loop():
    for page in range(20, 230):
        if not BREAKSIGNAL:
            ids = id_explorer(page)
            r2 = []
            for slug, id in ids:
                r2.append(POOL.submit(parse_post, slug, id))
                time.sleep(0.1)
            [r.result() for r in r2]
    POOL.shutdown()
    # print(master_set)


def makelinks(ids):
    return [f"https://forum.dfinity.org/t/{id}" for id in ids]


def bot_sync(bid,source):
    auth = """Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxNSwidXNlcm5hbWUiOiJuaWtoaWxzd2FtaTEiLCJpc19hZG1pbiI6ZmFsc2UsImlhdCI6MTcwNTE5MTEwOCwiZXhwIjoxNzA1Nzk1OTA4fQ.6f1FhVkKtF2Z0gfsenG_yMbhUa6CAAPOWGZrOFyMthM"""
    payload = {
        "type": "website",
        "content": source,
        "model": "gpt-3.5-turbo-dbase",
        "embedding": "openai",
    }
    url = f"https://ai.resolver.app/api/v1/bot/{bid}/source"
    res = requests.post(url, json=payload, headers={"Authorization": auth})
    print(res.json())


if __name__ == "__main__":
    BREAKSIGNAL = False
    POOL = ThreadPoolExecutor(3)
    # bot_sync(bot)
    # loop()

    # SYNC LOCAL CHROMA TO APP/BOT
    for doc in collection.get()["ids"]:
        bot = "clrcpyjlj0001ilteivw3s3br"
        source = f"https://forum.dfinity.org/t/{doc}"
        bot_sync(bot, source)
        
        # print(doc)

    # symlinks = makelinks(collection.query(query_texts=["New Node Provider Proposals "], n_results=3)["ids"][0])
    # print(
    #     symlinks
    # )  # RESULTS ['https://forum.dfinity.org/t/22214', 'https://forum.dfinity.org/t/16550', 'https://forum.dfinity.org/t/19291']
