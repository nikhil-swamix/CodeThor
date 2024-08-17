import os, json, time, datetime, sys
from pathlib import Path
from typing import List, Optional
from chromadb import PersistentClient, Collection, QueryResult, EmbeddingFunction
from utils import scan_files, getmtime, make_filetag, dict_to_xml
from utils.embedder import OllamaEmbedder, VoyageAIEmbeddingFunction, MixedbreadAIEmbeddingFunction
from .uaiclient import Client
from concurrent.futures import ThreadPoolExecutor
from termcolor import colored, cprint
sys.path.append(os.path.dirname(__file__))

class DebugLevel:
    """
    A class to manage debug levels for output verbosity in different methods.

    Attributes:
        summary (bool): Flag to indicate if summary information should be displayed.
        summary_detailed (bool): Flag to indicate if detailed summary information should be displayed.
        add_files_iterator (bool): Flag to control output during file addition iteration.
        add_files_show_updated (bool): Flag to indicate if updated files should be displayed during addition.
        rerank_show_filetree (bool): Flag to indicate if the file tree should be displayed during reranking.
    """

    summary = True
    summary_detailed = False
    add_files_iterator = True
    add_files_show_updated = False
    rerank_show_filetree = True
    resolve_codebase_show_sys_msg = True
    resolve_codebase_show_ctx_msg = False


def create_file_tree(file_list):
    # Create a dictionary to hold directory structure
    rtree = {"./": []}

    for file_path in file_list:
        parts = file_path.split("/")

        if len(parts) == 1:
            # If it's a top-level file, add it directly to "./"
            rtree["./"].append(file_path)
        else:
            # Otherwise, add to appropriate dictionary entry
            dir_name = parts[0]
            if rtree.get(dir_name) is None:
                rtree[dir_name] = []
            rtree[dir_name].append("/".join(parts[1:]))

    # Create a string representation of the file tree
    result = ""
    for directory, files in rtree.items():
        # result += f"📂{directory}{'/' if not directory.endswith('/') else '' }\n"
        for file in files:
            result += f"└─📄 {directory}/{file}\n"
    return result.strip()


def prepend_summary(file_path, tree="", debug=DebugLevel()):
    fcontent = open(file_path).read()
    summary = Client("openai|gpt-4o-mini").chat(
        [
            {
                "system": f"""you are a code review expert, summarize code as  comprehensively as possible so that Natural queries by user might be captured by a vector search engine try to refer from the system context which I will provide to add additional information, final output should be a medium length 2-3 paragraphs"""
            },
            {"user": f"## my sourcecode tree looks like this\n{tree}"},
            {"user": f"## my sourcecode file looks like this\n{fcontent}"},
        ],
    )
    if debug.summary:
        cprint(f"Summarized: {file_path}", "cyan")
        if debug.summary_detailed:
            print(f"{summary}")

    fcontent = f"""
    # SUMMARY OF {file_path}
    {summary}
    ```{file_path.split('.')[-1]} {file_path}\n{fcontent}\n```\n--------------------
    """.replace(
        "    ", "", 4
    )

    return fcontent


class CodeAgent:
    def __init__(self, path: str, db_path: str = "./.ai/db", embed_model: str = "voyage-code-2", **kwargs):
        if not path:
            raise ValueError("Project path must be specified.")
        if not kwargs['scanner_args']:
            raise ValueError("scanner_args must be specified in kwargs.")
        self.kwargs = kwargs
        self.path = path
        os.chdir(self.path)

        # STATICS
        self.project_name = "-".join(Path(self.path).parts[-2:])
        self.collection_name = f"{self.project_name}_{embed_model}"
        self.summary_collection_name = f"summary-{self.collection_name}"
        # DB
        self.crdb = PersistentClient(str(Path(path, db_path)))
        self.collection: Optional[Collection] = None
        self.init_db(model_name=embed_model)
        self.matched_files = scan_files(**kwargs['scanner_args'])
        self.add_files(self.matched_files)

    def init_db(self, model_name=None):
        if model_name is None:
            raise ValueError("Model name must be specified.")

        if "voyage" in model_name:
            emfn = VoyageAIEmbeddingFunction(model_name=model_name)
        else:
            emfn = MixedbreadAIEmbeddingFunction()

        self.collection = self.crdb.get_or_create_collection(
            name=self.collection_name,
            embedding_function=emfn,
        )

    def add_files(self, files: List[str], inject_summary=True, debug=DebugLevel()):
        """
        Add or update files in the specified collection files are passef by scanner fn.

        Args:
            collection (Collection): The ChromaDB collection to add files to.
            files (List[str]): A list of file paths to add or update.
            debug (int): The debug level for output verbosity.
        """
        if self.collection is None:
            raise ValueError("Collection must be initialized first. refer to init_db()")

        file_dicts: List[dict] = [{"path": f, "mtime": getmtime(f)} for f in files]
        chunk_size = 32
        file_chunks = [file_dicts[i : i + chunk_size] for i in range(0, len(file_dicts), chunk_size)]

        for chunk in file_chunks:
            upsertables = {
                "ids": [],
                "documents": [],
                "metadatas": [],
            }

            for f in chunk:
                q = self.collection.get(f["path"])
                exists = bool(q["ids"])
                updated = False

                if exists and q["metadatas"]:
                    updated = True if (q["metadatas"][0]['mtime'] != f["mtime"]) else False

                if not exists or updated:

                    if debug.add_files_iterator:
                        print(f"Adding {f['path']}")

                    c = open(f["path"], "r").read()
                    if not c:
                        continue

                    if inject_summary:
                        content = prepend_summary(f["path"], tree=create_file_tree(self.matched_files), debug=debug)

                    content = c if c else "<empty_file>"
                    upsertables["ids"].append(f["path"])
                    upsertables["documents"].append(content)
                    upsertables["metadatas"].append({"path": f["path"], "mtime": f["mtime"]})

            if upsertables["ids"]:
                if debug.add_files_show_updated:
                    print("ChangedFiles:", upsertables["ids"])

                self.collection.upsert(**upsertables)

    # def sync_summary(self, base_c: Collection, summary_c: Collection, max_workers: int = 6, debug: int = 0):
    #     """
    #     Synchronize the summary collection with the base collection.\n
    #     Args:
    #         base_c (Collection): The base ChromaDB collection.
    #         summary_c (Collection): The summary ChromaDB collection.
    #         max_workers (int): The maximum number of worker threads for summarization.
    #         debug (int): The debug level for output verbosity.
    #     """

    #     def summarize(path: str, col: Collection):
    #         print(f"Summarizing {path}")
    #         client: Client = Client("deepseek|deepseek-coder")
    #         content = open(path, "r").read()
    #         r = client.chat(
    #             [{"user": f"please read the file\n{content}"}],
    #             system=f"you are expert coder, keep only vital info, and summarize the file. not more than 200 words. add the file path at the end as below \n {path}",
    #         )
    #         col.upsert([path], documents=[r], metadatas=[{"path": path, "mtime": getmtime(path)}])

    #     q = base_c.get(limit=1000, include=["metadatas"])
    #     pool = ThreadPoolExecutor(max_workers)
    #     awaiter = []
    #     for i, m in zip(q["ids"], q["metadatas"]):
    #         exists: bool = bool(summary_c.get(i)['ids'])
    #         updated = False
    #         if exists:
    #             updated = (
    #                 True if (summary_c.get(i, include=['metadatas'])['metadatas'][0]['mtime'] != m["mtime"]) else False
    #             )

    #         if not exists or updated:
    #             awaiter.append(pool.submit(summarize, i, summary_c))

    #         if debug >= 2:
    #             if updated or not exists:
    #                 print(f"summarizing/adding {i}")

    #     pool.shutdown()

    def db_reality_check(self, debug: int = 0):
        """
        Perform a reality check on the database, removing entries for non-existent files.
        Args:
            files (List[str]): A list of existing file paths.
            colls (List[Collection]): A list of ChromaDB collections to check.
            debug (int): The debug level for output verbosity.
        """
        if not self.collection:
            raise ValueError("Collection must be initialized first.")

        for c in [self.collection]:
            allitems = c.get(limit=1000, include=[])

            for i in allitems["ids"]:
                if i not in self.matched_files:
                    print(f"Deleting {i} from {c.name}")
                    c.delete([i])

    def empty_collection(self, c: Collection | List[Collection]):
        """
        Empty the specified collection(s) by deleting all entries.\n
        """
        if not isinstance(c, list):
            c = [c]
        for cc in c:
            cc.delete(cc.get(limit=1000)['ids'])

    def rerank(self, q, enhance_llm=False, nctx_files=5, debug=DebugLevel()) -> QueryResult:
        if not self.collection:
            raise ValueError("Collection must be initialized first.")

        rel = self.collection.query(
            query_texts=(q),
            n_results=nctx_files,
        )

        if debug.rerank_show_filetree:
            cprint("RERANK:\n" + create_file_tree(rel["ids"][0]), "light_blue")

        if not enhance_llm:
            return rel
        else:
            rel_files = "\n\n".join(
                [make_filetag(f, attrs={"type": "reference/context"}, wrapper="```") for f in rel["ids"][0]]
            )
            p = f"""
            # CONTEXT
            # {rel_files}
            """.replace(
                "\t", "", 4
            )

            resp = Client("deepinfra|meta-llama/Meta-Llama-3.1-70B-Instruct").chat(
                system=p,
                messages=[
                    {
                        "user": f"""
                        # INSTRUCTION 
                        only give me list of files based on context im providing. just json output. no steps, explanations or anything else.
                        give me 3-10 most relevant files to my query\n # Query: {q}
                        # OUTPUT FORMAT JSON
                        [\"file1\", \"file2\",...]
                        """
                    }
                ],
            )
            try:
                print(resp)
                return json.loads(resp)
            except:
                raise Exception(f"FAIL:Json Parse Error\n{resp}")

    def resolve_codebase(
        self, q: str, system=None, enhance_llm=False, nctx_files=5, stream=True, debug=DebugLevel()
    ) -> str:
        rel = self.rerank(q, enhance_llm, nctx_files=nctx_files, debug=debug)

        context = "\n--------------------\n".join(
            [make_filetag(f, attrs={"type": "reference"}, wrapper="```") for f in rel["ids"][0]]
        )
        cprint(f"Context Tokens: {len(context)//3.6:.0f} ", "yellow")

        if debug.resolve_codebase_show_sys_msg:
            print(system)
        if debug.resolve_codebase_show_ctx_msg:
            print(context)

        resp = Client("deepseek|deepseek-coder").chat(
            system=f"""
            IMPORTANT OUTPUT INSTRUCTIONS:{system}\n\n
            CONTEXT:\n{context}\n
            """,
            messages=[{"user": f"{q}"}],
            temperature=0.1,
            stream=stream,
        )
        if stream:
            STAMP = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            open(f".ai/{STAMP}-out.md", "w")
            os.system(f"code .ai/{STAMP}-out.md")
            for r in resp:
                if r:
                    open(f".ai/{STAMP}-out.md", "a+").write(r)
            return f"{STAMP}-out.md"

        else:
            return resp


if __name__ == "__main__":
    # os.system("../.venv/Scripts/activate")

    PROFILES = {
        "juddoc": {
            "path": r"D:\GitHub\WORK\JudDoc\Backend",
            "scanner_args": {
                "patterns": [r"**/*.py"],
                "ignore_patterns": ["migrations", "__init__"],
            },
            "nctx_files": 15,
            "enhance_llm": True,
        },
        "codethor": {
            "path": r"D:\GitHub\CodeThor",
            "scanner_args": {
                "patterns": [r"**/*.py"],
                "ignore_patterns": ["html", "__init__"],
            },
            "nctx_files": 15,
            "enhance_llm": False,
        },
    }

    PROFILE = PROFILES["codethor"]

    # QUERY = """ i want to paginate my API give best approach and how to test it. and implications in react frontend """
    SYS = ""
    QUERY = """
Task: Create an exhaustive, highly detailed, and well-structured README documentation for a complete codebase, with a primary focus on files located in the root directory. The README should serve as a comprehensive guide for developers, maintainers, and users of the codebase.

Key Areas of Focus:

Core Library Analysis:

Provide an in-depth examination of the core library components
Detail each module, class, and function within the core library
Explain the purpose, functionality, and interdependencies of core components
Component Breakdown:

Systematically dissect and document every component in the codebase
Clarify the role of each component within the overall system architecture
Highlight any design patterns or architectural principles employed
Import and Dependency Management:

Map out all import statements and their significance
Explain external dependencies and their integration into the project
Provide guidance on managing and updating dependencies
API Documentation:

Create exhaustive API documentation for all public interfaces
Detail every method, function, and class exposed by the API
Include comprehensive parameter descriptions, return types, and usage examples
Parameter Analysis:

For each function and method, provide an in-depth explanation of all parameters
Include data types, default values, and acceptable ranges for parameters
Offer examples demonstrating the impact of different parameter values
Usage Guidelines:

Provide clear, step-by-step instructions for using the codebase
Include code snippets and examples for common use cases
Offer best practices and optimization tips
Installation and Setup:

Detail the installation process, including all prerequisites
Provide environment setup instructions for various operating systems
Include troubleshooting guides for common installation issues
Testing and Quality Assurance:

Explain the testing framework and methodologies used
Provide instructions for running tests and interpreting results
Offer guidelines for contributing new tests or expanding test coverage
Performance Considerations:

Discuss any performance optimizations implemented in the codebase
Provide benchmarks and performance metrics where applicable
Offer guidance on scaling and optimizing for different use cases
Security Considerations:

Highlight any security features or best practices implemented
Provide guidance on secure usage of the codebase
Discuss any known vulnerabilities and mitigation strategies
Contribution Guidelines:

Outline the process for contributing to the project
Provide coding standards and style guidelines
Explain the code review and merge process
Changelog and Version History:

Maintain a detailed changelog of all significant updates
Provide version compatibility information
Highlight breaking changes and migration guides between versions
License and Legal Information:

Clearly state the project's license and any legal considerations
Explain any restrictions on usage or distribution
Provide attribution for any third-party libraries or resources used
Format and Structure:

Utilize markdown formatting for optimal readability
Implement a clear and logical hierarchy of headings and subheadings
Use tables, code blocks, and bullet points to organize information effectively
Include a detailed table of contents with hyperlinks for easy navigation
Additional Notes:

There is no upper limit on content length; prioritize comprehensiveness over brevity
Generate content continuously, ensuring all aspects of the codebase are thoroughly documented
Adapt the structure and focus as needed based on the specific characteristics of the codebase
Include cross-references and links between related sections for improved navigation
Consider adding visual aids such as diagrams or flowcharts to illustrate complex concepts
"""
    agent = CodeAgent(**PROFILE)
    agent.db_reality_check()
    agent.resolve_codebase(q=QUERY, system=SYS, nctx_files=PROFILE["nctx_files"])

    # TESTS------------------------

    # print(f"Found {len(agent.matched_files)} files ")
    # print(agent.collection.get(["tests/main.py"]))
    # reranked = agent.rerank(q=QUERY, enhance_llm=True, nctx_files=PROFILE["nctx_files"])
    # print(reranked)

    # print(prepend_summary("populate-database.py"))
    # r = create_file_tree(agent.matched_files)
    # print(r)
    # agent.resolve_codebase(q=QUERY,enhance_llm=PROFILE["enhance_llm"], nctx_files=PROFILE["nctx_files"])
