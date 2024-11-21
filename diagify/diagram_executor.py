import subprocess
import tempfile
import os
import glob
import logging


def execute_mingrammer_code(code: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_script:
        script_path = tmp_script.name
        tmp_script.write(code.encode())
        tmp_script.flush()

        try:
            subprocess.run(["python3", script_path], check=True, cwd=os.getcwd())
            output_path = get_latest_png_file()
            logging.info(f"Diagram successfully generated: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            logging.error(f"Execution failed: {e}")
            raise RuntimeError("Failed to execute the generated Mingrammer code.")


def get_latest_png_file(directory=".") -> str:
    list_of_files = glob.glob(f"{directory}/*.png")
    if not list_of_files:
        raise FileNotFoundError("No PNG files found.")
    return max(list_of_files, key=os.path.getctime)
