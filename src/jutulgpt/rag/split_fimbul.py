import re
from textwrap import dedent
from typing import List

from langchain_core.documents import Document


def _extract_docstring_function_pairs(code: str):
    """
    Extract (function_name, docstring, body) tuples from Julia code.
    """
    lines = code.splitlines()
    results = []

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        # Look for docstring start
        if line.startswith('"""'):
            doc_lines = []
            i += 1
            while i < len(lines) and '"""' not in lines[i]:
                doc_lines.append(lines[i])
                i += 1
            if i == len(lines):
                break  # Unterminated docstring
            i += 1  # skip ending """
            docstring = dedent("\n".join(doc_lines))

            # Now look for function
            while i < len(lines) and not lines[i].strip().startswith("function"):
                i += 1
            if i == len(lines):
                break

            # Parse function header
            func_header = lines[i]
            match = re.match(r"function\s+(\w+)", func_header.strip())
            if not match:
                i += 1
                continue
            func_name = match.group(1)

            # Extract full function block using nesting level
            func_lines = [lines[i]]
            nesting = 1
            i += 1
            while i < len(lines) and nesting > 0:
                line_strip = lines[i].strip()
                func_lines.append(lines[i])

                # Count block openings
                if re.match(r"^(function|if|for|while|begin|let|try)\b", line_strip):
                    nesting += 1
                elif line_strip == "end":
                    nesting -= 1
                i += 1

            func_body = dedent(
                "\n".join(func_lines[1:-1])
            )  # Exclude 'function ...' and final 'end'
            results.append((func_name, docstring.strip(), func_body.strip()))
        else:
            i += 1

    return results


def _parse_section(lines, header):
    in_section = False
    section_lines = []
    for i, line in enumerate(lines):
        if line.strip().lower().startswith(f"# {header.lower()}"):
            in_section = True
            continue
        if in_section:
            if line.strip().startswith("#") and not line.strip().startswith("# -"):
                break  # next section
            if line.strip().startswith("-"):
                section_lines.append(line.strip())
    return section_lines


def _extract_return_from_body(body: str) -> str | None:
    """
    Extract the return value from function body, e.g. `return WI`
    """
    match = re.search(r"\breturn\s+(.+)", body)
    if match:
        return match.group(1).strip()
    return None


def _extract_summary(lines, signature_start_idx=0):
    """
    Given a list of lines and the index where the function signature starts,
    return the first non-empty line after the signature as the summary.
    """
    # Move to the line after the signature
    idx = signature_start_idx + 1

    # Skip lines that are part of the signature (e.g., kwargs..., closing parenthesis)
    while idx < len(lines):
        line = lines[idx].strip()
        # Skip if line is empty or looks like a parameter line or just a closing parenthesis
        if not line or line.endswith(")") or line.endswith("..."):
            idx += 1
            continue
        # Found the first non-empty, non-signature line
        return line
    return "No summary found."


def _parse_docstring(docstring, body: str):
    lines = docstring.splitlines()
    lines = [line.rstrip() for line in lines if line.strip()]
    # summary = lines[1] if len(lines) > 1 else "No summary found."
    summary = _extract_summary(lines)
    if summary == "# Keyword arguments":
        summary = "No summary found."

    # Extract sections
    args_lines = _parse_section(lines, "Arguments") + _parse_section(
        lines, "Keyword arguments"
    )
    returns_lines = _parse_section(lines, "Returns")

    args = []
    for line in args_lines:
        match = re.match(r"-\s+`?(\w+)`?(?:\s*=\s*(.*?)`?)?:\s*(.*)", line)
        if match:
            name, default, desc = match.groups()
            if default:
                args.append(f"- `{name} = {default}` — {desc}")
            else:
                args.append(f"- `{name}` — {desc}")
        else:
            args.append(f"- {line}")  # fallback

    returns = []
    for line in returns_lines:
        stripped = re.sub(r"^-\s+", "", line)
        returns.append(stripped)

    # If no returns in docstring, try parsing function body
    if not returns:
        inferred_return = _extract_return_from_body(body)
        if inferred_return:
            for ret in [r.strip() for r in inferred_return.split(",")]:
                if ret:
                    returns.append(f"- `{ret}` (inferred from function body)")
        # if inferred_return:
        #     returns.append(f"- `{inferred_return}` (inferred from function body)")

    return summary, "\n".join(args), "\n".join(returns)


# def split_docs(document: Document) -> List[Document]:
#     content = document.page_content
#     current_metadata = document.metadata.copy()
#
#     documents = []
#     for func_name, docstring, body in _extract_docstring_function_pairs(content):
#         summary, args_block, returns_block = _parse_docstring(docstring, body)
#         ## `{func_name}` – {summary}
#         chunk_text = f"""\
# ## {func_name} - {summary}
#
# ### Arguments
# {args_block if args_block else "None"}
#
# ### Returns
# {returns_block if returns_block else "None"}
# """
#         documents.append(
#             Document(
#                 page_content=chunk_text,
#                 metadata={**current_metadata, "heading": func_name},
#             )
#         )
#     return documents


def split_examples(document: Document) -> List[Document]:
    content = document.page_content
    current_metadata = document.metadata.copy()
    documents = [
        Document(
            page_content=content,
            metadata={**current_metadata},
        )
    ]
    return documents


#
# def format_doc(doc: Document) -> str:
#     # header_keys = ["Header 1", "Header 2"]
#     # section_path_parts = [
#     #     str(doc.metadata[k])
#     #     for k in header_keys
#     #     if k in doc.metadata and doc.metadata[k] is not None
#     # ]
#     # section_path = " > ".join(section_path_parts) if section_path_parts else "Root"
#     # file_source = doc.metadata.get("source", "Unknown Document")
#
#     file_source = doc.metadata.get("source", "Unknown Document")
#     function_name = doc.metadata.get("heading", "Unknown Function")
#
#     return f"## From `{file_source}` - Function `{function_name}`:\n{doc.page_content.strip()}"
