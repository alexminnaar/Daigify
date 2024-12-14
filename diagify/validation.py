import difflib
import os
import importlib
import diagrams


def populate_exec_globals_and_get_imports() -> list:
    """Populate exec_globals with Mingrammer diagram classes and return valid import statements."""
    import_statements = []
    diagrams_path = os.path.dirname(diagrams.__file__)

    for root, dirs, files in os.walk(diagrams_path):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                relative_path = os.path.relpath(os.path.join(root, file), diagrams_path)
                module_name = f"diagrams.{relative_path[:-3].replace(os.path.sep, '.')}"

                try:
                    module = importlib.import_module(module_name)
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type):
                            import_statements.append(f"from {module_name} import {attr_name}")
                except ImportError:
                    pass
    return import_statements


# Generate `correct_imports` list dynamically
correct_imports = populate_exec_globals_and_get_imports()


def identify_incorrect_imports(generated_code: str, correct_imports: list) -> dict:
    """
    Identify incorrect import statements in the generated code and provide suggestions
    with emphasis on matching the imported entity (e.g., class or function name).
    """
    incorrect_imports = {}

    for line in generated_code.splitlines():
        # Check for import statements
        if (line.startswith("from diagrams") or line.startswith("import diagrams")) and line not in [
            "from diagrams import Diagram",
            "from diagrams import Cluster, Diagram",
            "from diagrams import Diagram, Cluster"
        ]:
            if line not in correct_imports:
                # Extract the imported entity (e.g., "Kubernetes" in the example)
                imported_entity = line.split("import")[-1].strip() if "import" in line else ""

                # Filter correct_imports to focus on matching the imported entity
                focused_matches = [
                    match for match in correct_imports
                    if imported_entity and imported_entity in match
                ]

                # If no focused matches, use general closest matches
                closest_matches = focused_matches if focused_matches else difflib.get_close_matches(
                    line, correct_imports, n=10, cutoff=0.6
                )

                # Filter out private/special names
                closest_matches = [
                    match for match in closest_matches
                    if not match.split()[-1].startswith("_")
                ]

                if closest_matches:
                    incorrect_imports[line] = closest_matches

    return incorrect_imports


def generate_correction_prompt(generated_code: str, incorrect_imports: dict, original_prompt: str) -> str:
    """Generate a prompt to correct invalid imports."""
    incorrect_imports_text = "\n".join(
        f"- Incorrect: {incorrect} | Suggested: {suggested}"
        for incorrect, suggested in incorrect_imports.items()
    )
    return f"""
    You are an expert code debugger.  I will show you some python code that uses the Mingrammer diagramming tool
    That uses some incorrect imports that I want you to fix.  The original intention of the code was the following:\n
    {original_prompt}\n  Below is the code with the incorrect imports: \n
    {generated_code}\n
    The incorrect import lines and some possible suggestions for correct imports is below.\n
    {incorrect_imports_text}\n
    Please replace only the incorrect import lines with the suggested imports. Keep the rest of the code unchanged.
    The response you generate should only contain the python code without anything else.  
    It should not even be wrapped in ```python <generated_python_code> ```, instead it should just contain <generated_python_code>.
    """


def create_error_correction_prompt(code: str, error: str, description: str) -> str:

    return f"""
    You are a Python expert specializing in diagram generation. I attempted to run the following code, 
    which was intended to generate a diagram based on this description:\n\n{description}\n\n
    However, it threw the following error:\n\n{error}\n\n
    Here is the code that caused the error:\n\n{code}\n\n
    Please fix the code so that it runs without errors and achieves the intended purpose. 
    The response you generate should only contain the python code without anything else.  
    It should not even be wrapped in ```python <generated_python_code> ```, instead it should just contain <generated_python_code>.
    """