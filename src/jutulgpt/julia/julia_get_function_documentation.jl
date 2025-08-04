
using Jutul, JutulDarcy;
using CSTParser;
using CSTParser: EXPR;

# Get file path path from command line arguments, and read its content
# if length(ARGS) < 1
#     error("No input file provided!")
# end

# input_file = ARGS[1]

first_arg = abspath(ARGS[1])
path = isdir(first_arg) ? first_arg : dirname(first_arg)

root_file = if length(ARGS) > 1
    abspath(ARGS[2])
elseif isfile(first_arg)
    first_arg
else
    joinpath(path, "src", string(basename(path), ".jl"))
end

code_string = read(root_file, String)

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
    pattern = Regex("\\b([a-zA-Z_][a-zA-Z0-9_]*)\\s*\\(")

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

    func_names_with_doc = String[]
    for func_name in function_names
        doc = string(get_doc(func_name))
        if !isempty(doc)
            # Add func_name to the list of func_names_with_doc
            push!(func_names_with_doc, func_name)
            # Format the output
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

    return output, func_names_with_doc
end;

# code_string = """CartesianMesh();setup_doublet();simulate_reservoir();""";
documentation, func_names = get_docs_for_functions(code_string);
println("FUNCTION NAMES:");
println(func_names);
println("DOCUMENTATION");
println(documentation);
