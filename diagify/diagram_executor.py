import subprocess
import tempfile
import os
import glob
import logging
import sys


def execute_mingrammer_code(code: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp_script:
        script_path = tmp_script.name
        tmp_script.write(code.encode())
        tmp_script.flush()

        try:
            # Capture stdout and stderr from the executed script
            result = subprocess.run(
                [sys.executable, script_path],
                check=True,
                cwd=os.getcwd(),
                text=True,
                capture_output=True,
            )
            logging.info(f"Script executed successfully: {result.stdout}")
            output_path = get_latest_png_file()
            logging.info(f"Diagram successfully generated: {output_path}")
            return output_path
        except subprocess.CalledProcessError as e:
            # Capture and log the detailed error output
            logging.info("Mingrammer code execution failed!")
            raise RuntimeError(f"Failed to execute the generated Mingrammer code. Error:\n{e.stderr}")


def get_latest_png_file(directory=".") -> str:
    list_of_files = glob.glob(f"{directory}/*.png")
    if not list_of_files:
        raise FileNotFoundError("No PNG files found.")
    return max(list_of_files, key=os.path.getctime)
