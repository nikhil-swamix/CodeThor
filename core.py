import os, json
from pathlib import Path
from utils import scan_files, getmtime, make_filetag, dict_to_xml, scraper

# from utils.scraper import db
from utils.embedder import OllamaEmbedder, VoyageAIEmbeddingFunction, MixedbreadAIEmbeddingFunction
from chromadb import PersistentClient, Collection, QueryResult
from uaiclient import Client

from typing import Any, List

# from chromadb.utils.embedding_functions import


def get_or_create_collection(collection_name, model_name="voyage-code-2"):
    global crdb
    if "voyage" in collection_name:
        emfn = VoyageAIEmbeddingFunction(model_name=model_name)
    collection = crdb.get_or_create_collection(
        name=collection_name,
        embedding_function=VoyageAIEmbeddingFunction(model_name=model_name),
        # embedding_function=MixedbreadAIEmbeddingFunction(),
        # embedding_function=OllamaEmbedder(),
    )
    return collection


def add_files(collection: Collection, files: list, debug=2):
    from datetime import datetime as dt

    file_dicts: List[dict] = [{"path": f, "mtime": getmtime(f)} for f in files]
    upsertables = {
        "ids": [],
        "documents": [],
        "metadatas": [],
    }

    for f in file_dicts:
        q = collection.get(f["path"])
        exists = bool(q["ids"])
        updated = False

        if exists and q["metadatas"]:
            updated = True if (q["metadatas"][0]['mtime'] != f["mtime"]) else False
        if debug >= 2:
            print(f"file : {f['path']} Exists={exists}\tUpdated={updated}")

        if not exists or updated:
            if debug >= 1:
                print(f"Adding {f['path']}")
            c = open(f["path"], "r").read()
            content = c if c else "<empty_file>"
            upsertables["ids"].append(f["path"])
            upsertables["documents"].append(content)
            upsertables["metadatas"].append({"path": f["path"], "mtime": f["mtime"]})

    if upsertables["ids"]:
        print("ChangedFiles:", upsertables["ids"]) if debug >= 2 else ""
        collection.upsert(**upsertables)


def sync_summary(base_c: Collection, summary_c: Collection, max_workers=6, debug=0):
    """Generates summaries for files in a given collection using AI client, if they are new or modified."""
    from concurrent.futures import ThreadPoolExecutor

    def summarize(path: str, col: Collection):
        print(f"Summarizing {path}")
        client: Client = Client("deepseek", "deepseek-coder")
        content = open(path, "r").read()
        r = client.chat(
            [{"user": f"please read the file\n{content}"}],
            system=f"you are expert coder, keep only vital info, and summarize the file. not more than 200 words. add the file path at the end as below \n {path}",
        )
        col.upsert([path], documents=[r], metadatas=[{"path": path, "mtime": getmtime(path)}])

    q: Any = base_c.get(limit=1000, include=["metadatas"])
    pool = ThreadPoolExecutor(max_workers)
    awaiter = []
    for i, m in zip(q["ids"], q["metadatas"]):
        # check if exists
        exists: bool = bool(summary_c.get(i)['ids'])
        updated = False
        if exists:
            # print(summary_c.get(i))
            updated = True if (summary_c.get(i, include=['metadatas'])['metadatas'][0]['mtime'] != m["mtime"]) else False  # type: ignore

        if not exists or updated:
            awaiter.append(pool.submit(summarize, i, summary_c))

        if debug >= 2:
            if updated or not exists:
                print(f"summarizing/adding {i}")

    pool.shutdown()


def db_reality_check(files=[], colls: list[Collection] = [], debug=0):
    for c in colls:
        allitems = c.get(limit=1000, include=[])
        for i in allitems["ids"]:
            if i not in files:
                print(f"Deleting {i} from {c.name}")
                c.delete([i])


def empty_collection(c: Collection | List[Collection]):
    if not isinstance(c, list):
        c = [c]
        for cc in c:
            cc.delete(cc.get(limit=1000)['ids'])


def rerank(collection: Collection, q, enhance_llm=False, nctx_files=5, debug=0) -> QueryResult:
    rel = collection.query(
        query_texts=(q),
        n_results=nctx_files,
    )
    if debug >= 1:
        print("Reranked:", rel["ids"])

    if not enhance_llm:
        return rel
    else:
        rel_files = "\n\n".join([make_filetag(f, attrs={"type": "reference/context"}) for f in rel["ids"][0]])
        p = f"""
        <INSTRUCTION>you will act as a vector search engine and file relevance analyzer. NO OTHER OUTPUT , just as a json line array without markdown ```. supress any other output no explanations anywhere, strict! </INSTRUCTION>
        Query: query will be a string asked by user, please do not make any assumptions or hallucinations.
        OUTPUT FORMAT: [\"file1\", \"file2\",...]
        <CONTEXT>{rel_files} </CONTEXT>
        """.replace(
            "\t", ""
        )

        resp = Client("deepinfra", "microsoft/WizardLM-2-8x22B").chat(
            system=p,
            messages=[{"user": f" give me 2 most relevant files to my query\n {q}"}],
        )
        try:
            return json.loads(resp)
        except:
            raise Exception(f"FAIL:Json Parse Error\n{resp}")


def resolve_codebase(q: str, c: Collection, enhance_llm=False, nctx_files=5, debug=1) -> str:
    rel: QueryResult = rerank(c, q, enhance_llm, nctx_files=nctx_files, debug=debug)
    context = "\n".join([make_filetag(f, attrs={"type": "reference/context"}) for f in rel["ids"][0]])
    enhanced_q = {
        "INSTRUCTIONS": [
            "You are an expert coder and fullstack engineer working with sveltekit and intelligence is at expert level.",
            "Please read the Context and give me the response to my query",
            # "You can predict what the user may do next after the current query.",
            # "In the ending, append 3 possible questions which the user may ask next.",
            "follow SOLID and GOAL principles",
            "minimal commenting, clean code",
            "Failing to follow above instructions will have deadly consequences",
        ],
        "Query": q,
    }
    enhanced_q = dict_to_xml(enhanced_q)
    print(enhanced_q) if debug >= 1 else None
    resp = Client("deepseek", "deepseek-chat").chat(
        system=f""""CONTEXT": {context}""",
        messages=[{"user": f"{enhanced_q}"}],
        temperature=0.2,
    )
    return resp


if __name__ == "__main__":
    # PATH = rf"{os.getcwd()}"

    PATH = r"D:\GitHub\FREELANCE\Client-Prateek\Hospix"
    os.chdir(PATH)
    crdb = PersistentClient("./.ai/db")
    PROJECT_NAME = "-".join(Path(PATH).parts[-2:])
    e_model_name = "voyage-code-2"
    COLL = f"{PROJECT_NAME}_{e_model_name}"
    COLL_SUMMARY = f"summary-{COLL}"
    SVELTE_PROJECT_PATTERNS = [r"**/*.svelte", r"**/*.ts", r"**/*.js", r"**/*.json"]
    print(PATH, COLL, COLL_SUMMARY)

    # --------------------
    base_c = get_or_create_collection(COLL, model_name=e_model_name)
    # empty_collection(base_c)
    file_targets = scan_files(SVELTE_PROJECT_PATTERNS, [r'android.*'])
    add_files(base_c, file_targets, debug=1)

    # summary_c = get_or_create_collection(_COLL_SUMMARY)
    # sync_summary(base_c, summary_c)
    # db_reality_check(files=scan_files(), colls=[base_c, summary_c])
    QUERY = """
    home.svelte: 
    how to add a X button for searchbar and clear it when clicked
    """
    resp = resolve_codebase(
        q=QUERY,
        c=base_c,
        nctx_files=8,
    )
    open("out.md", "w").write(resp)
