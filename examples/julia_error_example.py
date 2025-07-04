from jutulgpt.julia_interface import run_string

if __name__ == "__main__":
    # julia_code = """
    # x = 2; y = x^3; y
    # """
    # julia_code = """
    # throw("Intentional error for testing")
    # """
    julia_code = """
    using InvalidMdule
    """

    result = run_string(julia_code)

    print("Result of running Julia code:")
    if result["error"]:
        print("Error occurred:")
        print(f"out: {result['out']}")
        print(f"error: {result['error']}")
        print(f"error_message: {result['error_message']}")
        print(f"error_stacktrace: {result['error_stacktrace']}")
    else:
        print("Code executed successfully.")
        print("Output:", result["out"])
