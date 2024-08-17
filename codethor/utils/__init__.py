from typing import Literal


def scan_files(patterns=None, ignore_patterns=[], use_gitignore=True):
    """
    Scans for files matching patterns, respecting ignore rules.

    Args:
        patterns: Glob patterns to match.
        ignore_patterns: Regex patterns to ignore. Default: []
        use_gitignore: Include .gitignore rules. Default: True

    Returns:
        List of matching file paths.

    Process:
    1. Adds .gitignore rules if applicable
    2. Filters main directories against ignore patterns
    3. Recursively searches each directory for matching files
    4. Applies ignore patterns to found files
    5. Normalizes and returns matching paths
    """
    import re, os
    import glob
    from pathlib import Path

    if patterns is None:
        raise ValueError("At least one pattern must be specified. example ['**/*.py']")
    if isinstance(patterns, str):
        patterns = [patterns]

    matches = []

    if use_gitignore and Path('.gitignore').exists():
        with open('.gitignore', 'r') as gitignore_file:
            for l in gitignore_file.readlines():
                l = l.strip()
                if not l: # skip empty
                    continue
                if not l.startswith('#'):
                    l = f".{l}" if l.startswith("*") else l
                    ignore_patterns.append(l)

        # print("Using .gitignore", ignore_patterns)

    def is_ignored(file):
        try:
            for ignore_pattern in ignore_patterns:
                ignore_pattern = ignore_pattern.replace("/**", "/*")
                try:
                    regex = re.compile(ignore_pattern)
                    if re.search(regex, file):

                        return True
                except re.error:
                    print(f"WARNING:Regex: {ignore_pattern} | File: {file}")
                    continue
            return False
        except Exception as e:
            print(f"ERROR: {e}, File: {file}")
            return False

    for pattern in patterns:
        for file in glob.glob(pattern, recursive=True):
            file = file.replace("\\", "/")
            # print("file", file, is_ignored(file))
            if is_ignored(file):
                continue
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
            template = f"```{filepath.split('.')[-1]} {filepath}\n{contents}\n```"
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
            dict[k] = "\n".join([f"<li>{x}</li>" for x in v])

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
    start_directory = r'D:\GitHub\FREELANCE\Client-Himanshu\chunavexpress.com\frontend'  # Current directory
    file_tree = generate_file_tree(start_directory)
    print(file_tree)
