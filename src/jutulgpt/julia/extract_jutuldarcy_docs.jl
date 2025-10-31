# Julia script to extract all exported function documentation from JutulDarcy
# This script uses the @doc macro to get actual docstrings, not just references

using JutulDarcy
using Markdown

"""
Extract all exported symbols and their documentation from a module.
"""
function extract_module_docs(mod::Module)
    docs_dict = Dict{String, String}()
    
    # Get all exported names from the module
    exported_names = names(mod; all=false, imported=false)
    
    for name in exported_names
        # Skip certain names that aren't useful
        if name in [:eval, :include]
            continue
        end
        
        # Get the symbol
        try
            sym = getfield(mod, name)
            
            # Get the documentation
            doc = Docs.doc(sym)
            
            # Convert to string and clean up
            doc_str = string(doc)
            
            # Skip if it's just a binding or no docs
            if occursin("No documentation found", doc_str) || 
               occursin("Binding", doc_str) && length(doc_str) < 100
                continue
            end
            
            # Store with the qualified name
            qualified_name = string(mod, ".", name)
            docs_dict[qualified_name] = doc_str
        catch e
            # Skip symbols that can't be accessed or documented
            continue
        end
    end
    
    return docs_dict
end

"""
Extract documentation from JutulDarcy and related modules.
"""
function extract_all_jutuldarcy_docs()
    all_docs = Dict{String, String}()
    
    # Extract from main JutulDarcy module
    merge!(all_docs, extract_module_docs(JutulDarcy))
    
    # Also extract from Jutul (the underlying framework)
    try
        using Jutul
        merge!(all_docs, extract_module_docs(Jutul))
    catch
    end
    
    return all_docs
end

"""
Main function - extract docs and output as JSON.
"""
function main()
    println("EXTRACTING_DOCS_START")
    
    docs = extract_all_jutuldarcy_docs()
    
    # Sort by name for consistency
    sorted_names = sort(collect(keys(docs)))
    
    # Output as JSON
    println("{")
    for (i, name) in enumerate(sorted_names)
        doc_content = docs[name]
        
        # Escape special characters for JSON
        escaped_doc = replace(doc_content, "\\" => "\\\\", "\"" => "\\\"", "\n" => "\\n", "\r" => "\\r", "\t" => "\\t")
        
        print("  \"$name\": \"$escaped_doc\"")
        if i < length(sorted_names)
            println(",")
        else
            println()
        end
    end
    println("}")
    
    println("EXTRACTING_DOCS_END")
    println(stderr, "Extracted documentation for $(length(docs)) symbols")
end

# Run if this is the main script
if abspath(PROGRAM_FILE) == @__FILE__
    main()
end
