from jutulgpt.cli import colorscheme, print_to_console
from jutulgpt.julia.julia_code_runner import run_lint_code


def get_linting_result(code: str) -> str:
    print_to_console(
        text="Running linter on the code...",
        title="Linter",
        border_style=colorscheme.warning,
    )

    try:
        res, err = run_lint_code(code=code)
        lines = res.splitlines()
        for i, line in enumerate(lines):
            if "STARTING LINT:" in line:
                linting_result = "\n".join(lines[i + 1 :])

                if linting_result:
                    print_to_console(
                        text=linting_result,
                        title="Linter Result",
                        border_style=colorscheme.error,
                    )
                else:
                    print_to_console(
                        text="No linting issues found.",
                        title="Linter Result",
                        border_style=colorscheme.success,
                    )
                return linting_result

        return ""

    except Exception as _:
        return ""
