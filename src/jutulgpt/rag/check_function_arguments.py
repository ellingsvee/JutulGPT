# import os
# import re


# def _get_called_functions(code: str, function_list: list) -> set:
#     """
#     Check which functions from the function_list are called in the code.
#     Returns a set of called function names.
#     """
#     called_functions = set()
#     for function in function_list:
#         # Match function call with optional whitespace and (
#         pattern = rf"{function}\s*\("
#         if re.search(pattern, code):
#             called_functions.add(function)
#     return called_functions


# def _get_used_keywords(code: str, function_name: str) -> set:
#     """
#     Extract the keyword arguments used in a Julia function call from a string.
#     Returns a set of used keyword argument names.
#     """
#     pattern = rf"{function_name}\s*\((.*?)\)"
#     match = re.search(pattern, code, re.DOTALL)
#     if not match:
#         raise ValueError(f"Function call to {function_name} not found in code.")

#     args = match.group(1)
#     used_keywords = set()
#     for part in args.split(","):
#         part = part.strip()
#         if "=" in part:
#             key = part.split("=")[0].strip()
#             used_keywords.add(key)
#     return used_keywords


def _get_valid_keywords_for_function(function_name: str) -> set:
    """
    Retrieve the valid keyword arguments for a given function from the extracted_julia_names.txt file.
    """
    valid_keywords = set()
    with open("src/jutulgpt/rag/extracted_julia_names.txt", "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            # Match lines like: FunctionName(arg1, arg2; key1=, key2=)
            match = re.match(rf"^{re.escape(function_name)}\((.*?)\)$", line)
            if match:
                args_str = match.group(1)
                # Split by ; to separate positional and keyword arguments
                if ";" in args_str:
                    _, kwarg_str = args_str.split(";", 1)
                    # Extract keyword names before '=' or after ','
                    for kw in kwarg_str.split(","):
                        kw = kw.strip()
                        if "=" in kw:
                            key = kw.split("=")[0].strip()
                            valid_keywords.add(key)
                        elif kw:  # handle cases like <keyword arguments>
                            valid_keywords.add(kw)
    return valid_keywords


# def _check_arguments_for_code_line(code_line: str):
#     with open("src/jutulgpt/rag/extracted_julia_names.txt", "r") as f:
#         function_list = []
#         for line in f:
#             line = line.strip()
#             if not line:
#                 continue
#             # Extract function name before first '('
#             name_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
#             if name_match:
#                 function_list.append(name_match.group(1))

#     # Check which functions are called in the code
#     called_functions = _get_called_functions(code_line, function_list)

#     for function in called_functions:
#         used_keywords = _get_used_keywords(code_line, function)
#         valid_keywords = _get_valid_keywords_for_function(function)
#         valid_keywords = {
#             kw for kw in valid_keywords if kw not in {"kwarg...", "<kwarg>"}
#         }
#         if not valid_keywords:
#             print(f"⚠️ No valid keywords found for function {function}.")
#             continue

#         invalid = used_keywords - valid_keywords
#         if invalid:
#             print(
#                 f"❌ Invalid keyword arguments for {function}: {invalid}. Valid keywords are: {valid_keywords}"
#             )
#             return False, function, invalid, valid_keywords
#         else:
#             print(f"✅ All keyword arguments for {function} are valid.")
#             return True, function, used_keywords, valid_keywords


# def check_arguments(code: str):
#     """
#     Check the validity of keyword arguments in a Julia function call within the provided code.
#     """
#     # Split the code into lines to check each line separately
#     code_lines = code.splitlines()
#     for line in code_lines:
#         line = line.strip()
#         if not line:
#             continue  # Skip empty lines
#         _check_arguments_for_code_line(line)


# if __name__ == "__main__":
#     # Example code snippet to check
#     example_code = """
#     case, sections = btes(num_wells = 48, depths = [0.0, 0.5, 100, 125],
#         charge_months = ["April", "May", "June", "July", "August", "September"],
#         discharge_months = ["October", "November", "December", "January", "February", "March"],
#         num_years = 4,
#     );
#     """
#     check_arguments(example_code)

import re


def extract_function_calls(code: str, function_list: list):
    """
    Extract all function calls (with arguments) from code, even if they span multiple lines.
    Returns a list of (function_name, arg_string).
    """
    calls = []
    # Build a regex pattern for all function names
    pattern = r"(" + "|".join(re.escape(fn) for fn in function_list) + r")\s*\("
    for match in re.finditer(pattern, code):
        name = match.group(1)
        start = match.end()  # position after the opening '('
        i = start
        depth = 1
        while i < len(code) and depth > 0:
            if code[i] == "(":
                depth += 1
            elif code[i] == ")":
                depth -= 1
            i += 1
        if depth == 0:
            arg_string = code[start : i - 1]
            calls.append((name, arg_string))
    return calls


def _get_used_keywords_from_arg_string(arg_string: str) -> set:
    used_keywords = set()
    for part in arg_string.split(","):
        part = part.strip()
        if "=" in part:
            key = part.split("=")[0].strip()
            used_keywords.add(key)
    return used_keywords


def check_arguments(code: str):
    # Load function names from extracted_julia_names.txt
    with open("src/jutulgpt/rag/extracted_julia_names.txt", "r") as f:
        function_list = []
        for line in f:
            line = line.strip()
            if not line:
                continue
            name_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*\(", line)
            if name_match:
                function_list.append(name_match.group(1))

    # Extract all function calls (with arguments) from the code
    calls = extract_function_calls(code, function_list)

    results = []
    for function, arg_string in calls:
        used_keywords = _get_used_keywords_from_arg_string(arg_string)
        valid_keywords = _get_valid_keywords_for_function(function)
        keyword_args = {
            kw
            for kw in valid_keywords
            if kw in {"kwarg...", "<kwarg>", "<keyword arguments>"}
        }
        if not keyword_args:
            valid_keywords = valid_keywords - keyword_args
            invalid = used_keywords - valid_keywords
            if invalid:
                print(
                    f"❌ Invalid keyword arguments for {function}: {invalid}. Valid keywords are: {valid_keywords}"
                )
                results.append((False, function, invalid, valid_keywords))
            else:
                print(f"✅ All keyword arguments for {function} are valid.")
                results.append((True, function, used_keywords, valid_keywords))
        else:
            print(f"Unable to check {function} due to keyword arguments.")
            results.append((True, function, used_keywords, valid_keywords))
    return results


# (Keep your _get_valid_keywords_for_function as before)

if __name__ == "__main__":
    # Example code snippet to check
    example_code = """
    case, sections = btes(num_wells = 48, depths = [0.0, 0.5, 100, 125],
        charge_months = ["April", "May", "June", "July", "August", "September"],
        discharge_months = ["October", "November", "December", "January", "February", "March"],
        num_years = 4,
    );
    results = simulate_reservoir(case;
    simulator=simulator, config=config, info_level=-1);
    """
    check_arguments(example_code)
