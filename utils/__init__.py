try:
    from . import webtools
except:
    import webtools
from typing import Literal


def scan_files(patterns=["**/*.py"], ignore_patterns=[], use_gitignore=True):
    import re,os
    import itertools, glob
    from pathlib import Path

    matches = []

    if use_gitignore and Path('.gitignore').exists():
        # print("Using .gitignore")
        with open('.gitignore', 'r') as gitignore_file:
            ignore_patterns += [line.strip() for line in gitignore_file if line.strip() and not line.startswith('#')]

    def should_ignore(file):
        # Compile the regex patterns and match them against the file path
        return any(re.search(re.compile(ignore_pattern), file) for ignore_pattern in ignore_patterns)

    main_dirs = [d for d in glob.iglob("./*") if not any([should_ignore(d)])]

    for d in main_dirs:
        for pattern in patterns:
            for file in glob.iglob(pattern, root_dir=d, recursive=True):
                file= Path(d).joinpath(file).as_posix()
                # print(file)
                file = file.replace("\\", "/")
                if not should_ignore(file):
                    matches.append(file)
    return matches


def getmtime(path):
    from datetime import datetime as dt
    import os

    return dt.fromtimestamp(os.path.getmtime(path)).isoformat()


def enum_text(text: str):
    """return a list of enumerated lines example:
    1: hello
    2: world
    """
    return "\n".join([f'{i+1:3d}: {line}' for i, line in enumerate(text.splitlines())])


def make_filetag(filepath: str, tagname="File", attrs={}, wrapper: Literal["```", "<>"] = "<>", enum=False):
    contents = open(filepath).read()
    attestr = " ".join([f'{k}="{v}"' for k, v in attrs.items()])
    if enum:
        contents = enum_text(filepath)

    match wrapper:
        case "```":
            template = f"```{filepath}\n{contents}\n```"
        case "<>":
            if enum:
                contents = "\n\t".join(contents.splitlines())
            template = f"""\n----------\n<{tagname} path="{filepath}" {attestr}>\n{contents}\n</{tagname}>\n"""
        case _:
            raise ValueError(f"Unexpected wrapper: {wrapper}")

    return template


def dict_to_xml(dict):
    """user k,v[list] to xml if v is string then direct, if v is list wraps with <item></item> for each item"""
    resp = ""
    for k, v in dict.items():
        if isinstance(v, str):
            dict[k] = v
        elif isinstance(v, list):
            dict[k] = "\n".join([f"<item>{x}</item>" for x in v])

    for k, v in dict.items():
        resp += f"<{k}>\n{v}\n</{k}>\n"
    return resp


def edit_file(path: str, diff: list[dict]):
    # WIP
    """## this function can precisely edit a file
    diff argument example for merging 1,2 lines:
        [{"-": [1,2], "+": {1:"apple ball"}}]
        here [1,2] are line numbers with 1 based indexing, 1 : apple , 2: ball, after edit 1 has "apple ball"
    "-" means delete line
    "+" means add line with content as value and number as key
    """
    lines = open(path).readlines()
    print(lines)
    for change in diff:
        if "-" in change:
            for line_number in change["-"]:
                lines[line_number - 1] = None

        if "+" in change:
            for line_number, content in change["+"].items():
                if line_number > len(lines):
                    lines.append("\n" + content)
                else:
                    lines[line_number - 1] = content + "\n"

    lines = [x for x in lines if x is not None]
    print(lines)
    return "".join(lines)
    # with open(path, 'w') as f:
    #     f.writelines(lines)


def jsonify(inp):
    import re, os, json

    if os.path.exists(inp) and any(inp.endswith(x) for x in ["txt", "json", "md", "html"]):
        inp = open(inp).read()

    match = re.search(r'\{[\s\S]*\}|\[[\s\S]*\]', inp)
    if match is not None:
        inp = json.loads(match.group())
    return inp


def count_tokens(text):
    import tiktoken

    return len(tiktoken.get_encoding("cl100k_base").encode(text))


def to_clipboard(text):
    import pyperclip

    pyperclip.copy(text)


if __name__ == "__main__":
    print(jsonify("../TASK-REFACTOR.txt"))

    # newfile = edit_file("../f1", [{"-": [1, 2], "+": {1: "apple ball"}}])
    # newfile = edit_file("../f1", [{"+": {4: "ashiled"}}])
    # print(newfile)
