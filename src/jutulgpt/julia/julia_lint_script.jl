using LanguageServer, StaticLint, SymbolServer;
using Printf;

first_arg = abspath(ARGS[1])
path = isdir(first_arg) ? first_arg : dirname(first_arg)

root_file = if length(ARGS) > 1
    abspath(ARGS[2])
elseif isfile(first_arg)
    first_arg
else
    joinpath(path, "src", string(basename(path), ".jl"))
end

s = LanguageServerInstance(Pipe(), stdout, path)
_, symbols = SymbolServer.getstore(s.symbol_server, path)
s.global_env.symbols = symbols
s.global_env.extended_methods = SymbolServer.collect_extended_methods(s.global_env.symbols)
s.global_env.project_deps = collect(keys(s.global_env.symbols))

f = StaticLint.loadfile(s, root_file)
StaticLint.semantic_pass(LanguageServer.getroot(f))

println("STARTING LINT:")
file_text_lines = readlines(root_file)
for doc in LanguageServer.getdocuments_value(s)
    StaticLint.check_all(LanguageServer.getcst(doc), s.lint_options, LanguageServer.getenv(doc, s))
    LanguageServer.mark_errors(doc, doc.diagnostics)

    for diag in doc.diagnostics
        range = diag.range
        start_line = range.start.line + 1
        start_char = range.start.character + 1
        end_line = range.stop.line + 1
        end_char = range.stop.character + 1
        severity_code = something(diag.severity, 2)
        severity_str = ["Error", "Warning", "Information", "Hint"][severity_code]

        source_line = start_line <= length(file_text_lines) ? file_text_lines[start_line] : ""

        println("$severity_str: Line $start_line:$start_char to $end_line:$end_char - $(diag.message)")
        println("- Full line content: ", source_line)
        println()
    end
end

