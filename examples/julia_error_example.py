from jutulgpt.julia_interface import run_string

if __name__ == "__main__":
    julia_code = """
    throw("Intentional error for testing")
    """

    result = run_string(julia_code)

    print("Result of running Julia code:")
    if result["error"]:
        print("Error occurred:")
        print(result["error_message"])
    else:
        print("Code executed successfully.")
        print("Output:", result["out"])
