import glob, os, hashlib, base64, re, json, chromadb, random

import anthropic, openai
from pprint import pprint
import chromadb.utils.embedding_functions as embedding_functions
from concurrent.futures import ThreadPoolExecutor
from functools import reduce

client = chromadb.PersistentClient(path="chroma.db")
chroma_collection = "codebase-e-large"
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"), model_name="text-embedding-3-large"
)

MODELS_O = ["gpt-3.5-turbo-0125", "gpt-4-0125-preview"]
CLIENT_O = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MODELS_A = ['claude-3-haiku-20240307', 'claude-3-sonnet-20240229', 'claude-3-opus-20240229']
CLIENT_A = anthropic.Anthropic()
CONF_A = {
    "model": MODELS_A[1],
}


def b64e(s):
    return base64.b64encode(s.encode()).decode("utf-8")


def b64d(s):
    return base64.b64decode(s.encode()).decode("utf-8")


def sha256(content):
    """Calculate the SHA-256 hash of the given content. and return hex"""
    return hashlib.sha256(content.encode()).hexdigest()


def make_sourcetree(path="../src", excludes=['pages']):
    """iter through root path, and create source tree in JSON format"""
    import pathlib
    from collections import defaultdict

    d = defaultdict(dict)
    with open("tree.json", "w") as out:
        for root, dirs, files in os.walk(path):
            splitted = pathlib.Path(root).parts
            if any(x in root for x in excludes):
                continue
            if files:
                d["/".join(splitted)] = files
                # print(splitted, files)
        # print(d)
        # use tabs
        out.write(json.dumps(d, indent="\t", separators=(",", ":")))


def get_files(directory='src', extensions=[".svelte", '.js', '.ts']):
    """Get a list of relevant file paths from the given directory that match the given file extensions. :returns A list of file paths."""
    file_paths = []
    for ext in extensions:
        file_paths.extend(glob.glob(f'{directory}/**/*{ext}', recursive=True))
    return file_paths


def attach_summary_ai(file_path, content):
    summary = (
        CLIENT_O.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[
                {
                    "role": "system",
                    "content": f""" you are a code review expert, summarize code descriptively TO A 10th GRADER. add 5-10 coherent keywords words related to code, for vector search relevance . all in one paragraph, no new lines""",
                },
                {"role": "user", "content": f"my sourcecode tree looks like this{open('tree.json').read()}"},
                {"role": "user", "content": content},
            ],
            n=1,
        )
        .choices[0]
        .message.content
    )
    print(f"AI-SUMMARIZED: {file_path}: {summary}")
    if file_path.endswith('.svelte'):
        content = f"<!-- SUMMARY for {file_path} | {summary} -->\n" + content

    if file_path.endswith('.js'):
        content = f"/* SUMMARY for {file_path} | {summary} */\n" + content

    return content


def index_code(files=[], smart=True, dump=True):
    """
    Merge code from a list of files into a single file named 'codebase.txt'.

    :param files: A list of file paths to merge.
    """
    if smart:
        files = get_files("../src")
    with open('codebase.txt', 'w+') as cfile:
        for file_path in files:
            if dump:
                with open(file_path, 'r') as file:
                    contents = file.read()
                    print(file_path)
                    cfile.write(f'\n[---------- {file_path} ----------]\n')
                    cfile.write(contents)
            else:
                fcontents = open(file_path).read()
                pass
                # db.insert({'hash': sha256(fcontents) }, doc_id=b64e(file_path))


def chromaworker(file_path, collection, excludes=[], summary_includes=[]):
    try:
        if any(x in file_path for x in excludes):
            return
        contents = open(file_path, 'r').read()
        chash = sha256(contents)
        fid = b64e(file_path)
        metadatas = [{"hash": chash, "path": file_path}]
        docexists = collection.get(ids=[file_path])
        condition_add = not bool(docexists['ids'])
        condition_update = bool(docexists['ids'] and docexists['metadatas'][0]['hash'] != chash)
        if len(contents) <= 1:
            # print(f"Skipping:Empty: {file_path}")
            return

        if condition_add or condition_update:
            # print("CHIT", condition_add, condition_update)
            contents = contents.replace('  ', ' ')
            if summary_includes and any(file_path.endswith(x) for x in summary_includes):
                contents = attach_summary_ai(file_path, contents)
            kwargs = {'documents': [contents], 'ids': [file_path], 'metadatas': metadatas}
            if condition_add:
                # print(f"Adding {file_path}")
                collection.add(**kwargs)

            if condition_update:
                # print(f"Updating {file_path}")
                collection.update(**kwargs)
    except Exception as e:
        print(f"FAILED: {file_path} BCZ: {e}")


def chromify(excludes=['pages', 'components'], summary_includes=['.svelte', '.js', '.ts']):
    """
    - readme files are excluded from creating due to summary_includes
    """
    collection = client.create_collection(chroma_collection, get_or_create=True, embedding_function=openai_ef)
    files = get_files(directory='../src') + get_files(directory='./documentation/modular', extensions=[".md"])
    POOL = ThreadPoolExecutor(max_workers=5)
    for file_path in files:
        POOL.submit(chromaworker, file_path, collection, excludes=excludes, summary_includes=summary_includes)
        # chromaworker(file_path, collection,excludes=excludes, summary_includes=summary_includes)

    POOL.shutdown(wait=True)


def insert_block(file_path, content):
    return f"[\n---------- START FILE : {file_path} ----------]\n{content}\n EOF\n"


def raw_search(query, collection=chroma_collection, n=3):
    collection = client.get_or_create_collection(name=collection, embedding_function=openai_ef)
    q = collection.query(query_texts=[query], n_results=n)
    pprint(f"SYM FILES:")
    pprint(q['ids'][0])
    return q['ids'][0]


def vsearch(
    query,
    collection=chroma_collection,
    results=3,
    includes=[
        "../README.md",
        "./tree.json",
        # "./ai-output.md",
    ],
    match=[],
    contains=[],
):
    query = "\n".join(query) if isinstance(query, list) else query
    collection = client.get_or_create_collection(name=collection, embedding_function=openai_ef)
    q = collection.query(
        query_texts=query,
        n_results=results,
        # include=["data"], # where={"metadata_field": "is_equal_to_this"}, # optional filter # where_document={"$contains": contains[0]},  # optional filter
        include=["documents", "metadatas", "distances"],
    )
    # print(q['distances'][0])
    zippand = [*zip(q['ids'][0], q['documents'][0])]

    r = ""
    for i, c in zippand:
        if match and not any([m in i for m in match]):
            continue
        print("INCLUDING:", i)
        # remove js comments using regex
        c = re.sub(r'//.*?\n', '', c)
        c = c.replace('\t', ' ')
        for _ in range(3):
            c = c.replace('  ', ' ')
        r += insert_block(i, c)

    for i in includes:
        print("INCLUDING:", i)
        r += insert_block(i, open(i).read())
    # print(r)
    return r


def file_merge(files=[], append=["./tree.json", "./schemas.md", "../package.json"]):
    files = files + append
    return "".join(f"[-----FILE {x}-----]\n{open(x).read()}\n" for x in files)


def reprompt(prompt):
    system = 'rewrite 5 only prompts in technical ways and keeping  essential details, to exhaust all possible variants to be given to AI Engine. Example JSON array  [{"role": "user", "content": "..."},"role": "user", "content": "..."},]. no comments only programmatic output.'
    a = anthropic.Anthropic().messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        system=system,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    # print(a.content[0].text)
    return json.loads(a.content[0].text)


def rerank_llm(files=[], tasks=[], n_results=3, shallow=False):
    """use LLM to rerank based on task"""
    if not files:
        print("ERROR: no files to rerank")
        return

    if not tasks:
        print("ERROR: no tasks to rerank")
        return

    CONF = {
        "model": MODELS_A[2],
        "max_tokens": 1000,
        "temperature": 0.7,
    }
    if shallow:
        print("Shallow Reranking:", tasks)

        system = """ im giving you some file paths as follows
            FILES: {files}
            INSTRUCTIONS: cherry pick the files which have highest probablity of requiring to be edited wrt given task, account for user's misconceptions, and potential wrong order of filles.
            OUTPUT: just require json output, no "here is a..., certainly..., sure..." , 
            OUTPUT-NOTE: please do not replace file slashes
            FORMAT: [...]
            LIMIT: 0-{n_results} results
            TASKS: {tasks}
            """.format(
            files=files, n_results=n_results, tasks=tasks
        )
        a = anthropic.Anthropic().messages.create(
            **CONF,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": "optimal result for tasks: " + str(tasks),
                },
            ],
        )
        return json.loads(a.content[0].text)
    else:
        context = file_merge(files=files)
        print("Deep Reranking:SIZE", CLIENT_A.count_tokens(context))
        system = """CONTEXT: {context}
            INSTRUCTION: you are a rerank engine, you will process the given code, and return most probable files which are suited for given tasks. be very careful about file names and give exact without change
            FILES: {files}
            TASKS: {tasks}
            OUTPUT: just require json output, no contain "here is a..., certainly..., sure..."
            LIMIT : 0 - {n_results}
            FORMAT: [...]
            """.format(
            n_results=n_results, context=context, tasks=tasks, files=files
        )
        CONF["model"] = MODELS_A[0]
        a = anthropic.Anthropic().messages.create(
            **CONF,
            system=system,
            messages=[
                {
                    "role": "user",
                    "content": "optimal result for tasks: " + str(tasks),
                },
            ],
        )

        return json.loads(a.content[0].text)


if __name__ == "__main__":
    outfile = open("ai-output.md", "w")
    # merge_code() # codebase = open('codebase.txt').read() # index_code()
    make_sourcetree()
    chromify()

    SYS_PROMPT_DICT = {
        "TECH-STACK": ["SvelteKit 2", "Tailwindcss", "Shadcn-Svelte", "Supabase"],
        "RULES": [
            "think you are expert sveltekit master, like rich harris, and enterprise developer.",
            "do robust error handling, and only give minimal output. not full code",
            "should not contains bugs, follow the best practices. concise code. should be fullstack wherever possible.",
            "The task given could be a record from issue tracker",
            "Try to keep the code as similar pattern as previous .",
        ],
        "OUTPUT-FORMAT": [
            'output should be well structured markdown , include file name as | {full_filepath} |\n```<codetype>...```',
            "No explanations, no hello, no of course, no code comments, only indicate where code needs to be pasted",
            "Minimal number of lines, conservative output, just give areas of update, and omit other parts which are same as parent file",
        ],
        # "PREVIOUS-ERRORS": [ open("errors.txt").read(), ],
        # "TARGET": [r"http://localhost:5173/orders/"],
        "TASKS": [
            "There is no data validation while updating champ detail in the champ dashboard.All fields are not mandatory here. Champ can update even without entering any details. The update button is working even when all the fields are not filled"
        ],
    }
    QUERY = ""
    for k, v in SYS_PROMPT_DICT.items():
        QUERY += f"{k}\n - {v}\n\n"
    # context = vsearch("\n".join(SYS_PROMPT_DICT["TASKS"]), results=15)  # print(QUERY,context)
    sym_files = raw_search("\n".join(SYS_PROMPT_DICT["TASKS"]), n=7)
    # reranked_files = rerank_llm(tasks=SYS_PROMPT_DICT["TASKS"], shallow=True, files=sym_files, n_results=5)
    reranked_files = rerank_llm(tasks=SYS_PROMPT_DICT["TASKS"], files=sym_files, n_results=4)
    print(reranked_files)
    # exit()
    RESULT = CLIENT_A.messages.create(
        model=MODELS_A[1],
        temperature=0.9,
        max_tokens=1024 * 4,
        system=f"CODE-CONTEXT:\n{file_merge(reranked_files)}\nFollow these instructions:\n{QUERY}\n ",
        messages=[
            {"role": "user", "content": str(SYS_PROMPT_DICT["TASKS"])},
        ],
    )

    # print(RESULT.content[0], end="")
    for c in RESULT.content:
        outfile.write(c.text)
    os.system("code ai-output.md")
