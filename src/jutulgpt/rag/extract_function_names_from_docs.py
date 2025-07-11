import os
import re
from pathlib import Path


def extract_julia_names_from_markdown(md_text):
    """
    Extract Julia function/type names from Julia code blocks in markdown text.
    Returns a set of names.
    """
    names = set()
    # Find all julia code blocks
    code_blocks = re.findall(r"```julia(.*?)```", md_text, re.DOTALL | re.IGNORECASE)
    for block in code_blocks:
        # Match function/type signatures: e.g., WellGroup(...), SimpleWell(...)
        matches = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(", block, re.MULTILINE)
        names.update(matches)
    return names


def extract_julia_names_and_args_from_markdown(md_text):
    """
    Extract Julia function/type names and their arguments from Julia code blocks in markdown text.
    Handles nested parentheses in argument lists.
    Returns a set of (name, args) tuples.
    """
    results = set()
    code_blocks = re.findall(r"```julia(.*?)```", md_text, re.DOTALL | re.IGNORECASE)
    for block in code_blocks:
        lines = block.splitlines()
        for line in lines:
            # Look for something like Name(
            match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
            if match:
                name = match.group(1)
                # Now extract the full argument list, handling nested parentheses
                start = line.find("(")
                if start == -1:
                    continue
                i = start + 1
                depth = 1
                args = []
                while i < len(line):
                    c = line[i]
                    if c == "(":
                        depth += 1
                    elif c == ")":
                        depth -= 1
                        if depth == 0:
                            break
                    args.append(c)
                    i += 1
                # If we didn't close, skip
                if depth != 0:
                    continue
                arg_str = "".join(args)
                results.add((name.strip(), arg_str.strip()))
    return results


def get_all_markdown_files(docs_dirs):
    """
    Given a list of directories, return all .md files in them (recursively).
    """
    files = []
    for docs_dir in docs_dirs:
        for path in Path(docs_dir).rglob("*.md"):
            files.append(path)
    return files


def extract_all_names_from_docs(docs_dirs):
    """
    Go through all markdown files in docs_dirs and extract all Julia names.
    """
    all_names = set()
    md_files = get_all_markdown_files(docs_dirs)
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            text = f.read()
        names = extract_julia_names_from_markdown(text)
        all_names.update(names)
    return all_names


# def write_function_names_to_file():
#     docs_dirs = ["src/jutulgpt/rag/jutuldarcy/docs", "src/jutulgpt/rag/fimbul/docs"]
#     names = extract_all_names_from_docs(docs_dirs)

#     with open(
#         "src/jutulgpt/rag/extracted_julia_names.txt", "w", encoding="utf-8"
#     ) as out_file:
#         for name in sorted(names):
#             out_file.write(f"{name}\n")


def write_function_names_to_file():
    docs_dirs = ["src/jutulgpt/rag/jutuldarcy/docs", "src/jutulgpt/rag/fimbul/docs"]
    all_results = set()
    md_files = get_all_markdown_files(docs_dirs)
    for md_file in md_files:
        with open(md_file, "r", encoding="utf-8") as f:
            text = f.read()
        all_results.update(extract_julia_names_and_args_from_markdown(text))

    with open(
        "src/jutulgpt/rag/extracted_julia_names.txt", "w", encoding="utf-8"
    ) as out_file:
        for name, args in sorted(all_results):
            out_file.write(f"{name}({args})\n")


if not os.path.exists("src/jutulgpt/rag/extracted_julia_names.txt"):
    print("Extracting Julia function/type names from documentation...")
    write_function_names_to_file()

if __name__ == "__main__":
    write_function_names_to_file()
