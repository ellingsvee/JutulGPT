from typing import List

from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.julia.julia_code_runner import run_code


def _get_full_julia_code_string(eval_code: str) -> str:
    full_code = """
using Jutul, JutulDarcy;
using CSTParser;
using CSTParser: EXPR;

# Your existing docstring retriever function
function get_doc(funcname::String)
    try
        obj = getfield(Main, Symbol(funcname))
        doc = Base.Docs.doc(obj)
        # print(doc)
        # return doc === nothing ? "No documentation found." : sprint(show, "text/plain", doc)
        return doc === nothing ? "No documentation found." : doc
    catch e
        # return "Error retrieving documentation: $e"
        return ""
    end
end;

# Function to extract function names from CST
function extract_function_names(expr::EXPR)
    function_names = Set{String}()

    function traverse(node)
        # Debug: print node type and value
        # println("Node type: ", typeof(node), ", head: ", get(node, :head, "no head"), ", val: ", get(node, :val, "no val"))

        if isa(node, EXPR)
            # Check if this is a function call
            if haskey(node, :head) && node.head isa CSTParser.Head
                if node.head == CSTParser.CALL
                    # The first child should be the function name
                    if length(node.args) > 0
                        func_expr = node.args[1]
                        func_name = get_function_name(func_expr)
                        if func_name !== nothing && func_name != ""
                            push!(function_names, func_name)
                        end
                    end
                end
            end

            # Recursively traverse all children
            if haskey(node, :args) && node.args isa Vector
                for arg in node.args
                    traverse(arg)
                end
            end
        end
    end

    traverse(expr)
    return collect(function_names)
end;

# Helper function to extract function name from expression
function get_function_name(expr)
    if isa(expr, EXPR)
        if haskey(expr, :head) && haskey(expr, :val)
            if expr.head == CSTParser.IDENTIFIER
                return string(expr.val)
            elseif expr.head == CSTParser.CURLY
                # For parametric types, get the base name
                if length(expr.args) > 0
                    return get_function_name(expr.args[1])
                end
            elseif expr.head == CSTParser.OP && string(expr.val) == "."
                # For qualified names like Module.function, get the last part
                if length(expr.args) >= 2
                    return get_function_name(expr.args[end])
                end
            end
        elseif haskey(expr, :val) && isa(expr.val, String)
            return expr.val
        end
    end
    return nothing
end;

# Alternative approach using a simpler traversal
function extract_function_names_simple(code_string::String)
    function_names = Set{String}()

    try
        cst = CSTParser.parse(code_string)

        function traverse_simple(node)
            if isa(node, EXPR)
                # Look for function calls by checking the structure
                if haskey(node, :args) && length(node.args) > 0
                    # Check if this looks like a function call pattern
                    first_arg = node.args[1]
                    if isa(first_arg, EXPR) && haskey(first_arg, :val)
                        val_str = string(first_arg.val)
                        # Check if this looks like a function name (starts with letter, contains letters/numbers/_)
                        if match(r"^[a-zA-Z][a-zA-Z0-9_]*$", val_str) !== nothing
                            # Check if there are parentheses or other args suggesting it's a call
                            if length(node.args) > 1
                                push!(function_names, val_str)
                            end
                        end
                    end
                end

                # Recursively traverse
                if haskey(node, :args)
                    for arg in node.args
                        traverse_simple(arg)
                    end
                end
            end
        end

        traverse_simple(cst)

    catch e
        println("Error in simple extraction: $e")
    end

    return collect(function_names)
end;

# Regex-based fallback approach
function extract_function_names_regex(code_string::String)
    function_names = Set{String}()

    # Pattern to match function calls: identifier followed by opening parenthesis
    pattern = Regex("\\\\b([a-zA-Z_][a-zA-Z0-9_]*)\\\\s*\\\\(")

    for match in eachmatch(pattern, code_string)
        func_name = match.captures[1]
        # Filter out common keywords that aren't functions
        if !in(func_name, ["if", "while", "for", "try", "catch", "function", "macro", "struct", "module"])
            push!(function_names, func_name)
        end
    end

    return collect(function_names)
end;

# Main function that tries multiple approaches
function parse_and_extract_functions(code_string::String)
    functions_regex = extract_function_names_regex(code_string)
    return functions_regex
end;


function get_docs_for_functions(code_string::String)
    function_names = parse_and_extract_functions(code_string)
    output = ""

    for func_name in function_names
        doc = string(get_doc(func_name))
        if !isempty(doc)
            output *= "\n# Documentation for '$func_name':\n"
            # If doc is a string, apply regex replacement
            if isa(doc, String)
                # Replace every # at the start of a line with ##
                doc = replace(doc, r"^#"m => "##")
            end
            output *= doc * "\n"
            output *= "\n" * "="^50 * "\n"
        end
    end

    return output
end;
"""
    full_code += (
        f'\ncode_string = """{eval_code}""";\n'
        "res = get_docs_for_functions(code_string);\n"
        "println(res);\n"
    )
    return full_code


def _get_full_julia_code_string_from_function_list(function_names: List[str]) -> str:
    full_code = """
using Jutul, JutulDarcy;
using CSTParser;
using CSTParser: EXPR;

# Your existing docstring retriever function
function get_doc(funcname::String)
    try
        obj = getfield(Main, Symbol(funcname))
        doc = Base.Docs.doc(obj)
        # print(doc)
        # return doc === nothing ? "No documentation found." : sprint(show, "text/plain", doc)
        return doc === nothing ? "No documentation found." : doc
    catch e
        # return "Error retrieving documentation: $e"
        return ""
    end
end;
"""
    julia_vector_string = (
        "[" + ", ".join([f'"{name}"' for name in function_names]) + "]"
    )

    full_code += f"""
function get_docs_for_functions()
    function_names = {julia_vector_string}
    output = ""

    for func_name in function_names
        doc = string(get_doc(func_name))
        if !isempty(doc)
            output *= "\n# Documentation for '$func_name':\n"
            # If doc is a string, apply regex replacement
            if isa(doc, String)
                # Replace every # at the start of a line with ##
                doc = replace(doc, r"^#"m => "##")
            end
            output *= doc * "\n"
            output *= "\n" * "="^50 * "\n"
        end
    end

    return output
end;
"""
    full_code += "res = get_docs_for_functions();\nprintln(res);\n"
    return full_code


def get_function_documentation_from_code(code: str) -> str:
    print_to_console(
        text="Retrieving function documentation from the generated code...",
        title="Function Documentation Retriever",
        border_style=colorscheme.warning,
    )

    full_code = _get_full_julia_code_string(code)
    try:
        res = run_code(code=full_code)
        print_to_console(
            text="Function documentation retrieved successfully!",
            title="Function Documentation Retriever",
            border_style=colorscheme.success,
        )
        return res.get("output")
    except Exception as _:
        print_to_console(
            text="Function documentation retrieval failed.",
            title="Function Documentation Retriever",
            border_style=colorscheme.error,
        )
        return ""


def get_function_documentation_from_function_names(function_names: List[str]) -> str:
    full_code = _get_full_julia_code_string_from_function_list(function_names)
    try:
        res = run_code(code=full_code)
        return res.get("output")
    except Exception as _:
        return ""
        return ""
