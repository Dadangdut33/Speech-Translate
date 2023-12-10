from torch._dynamo import skipfiles


def replace_function(file_path: str, old_function_name: str, new_function_code: str):
    new_function_code = new_function_code.strip()
    # Step 1: Read the content of the file
    with open(file_path, 'r', encoding="utf-8") as file:
        file_content = file.read()

    # Step 2: Identify the function you want to replace
    start_index = file_content.find(f'def {old_function_name}(')
    end_index = file_content.find('\n', start_index)  # Assuming the function ends with a newline character

    # Step 3: Find the end of the old function
    old_function_end = file_content.find('\n\n', end_index)  # Assuming two newline characters indicate the end of a function

    # Step 4: Replace the old function with the new function
    new_file_content = file_content[:start_index] + new_function_code + file_content[old_function_end:]

    # Step 5: Write the modified content back to the file
    with open(file_path, 'w', encoding="utf-8") as file:
        file.write(new_file_content)


print(">> Patching torch._dynamo.skipfiles to avoid error on torch._dynamo.skipfiles.SKIP_DIRS because of m.__file__")
replace_function(
    skipfiles.__file__, "_module_dir", """
def _module_dir(m: types.ModuleType):
    try:
        return _strip_init_py(m.__file__)
    except AttributeError:
        return ""
"""
)
