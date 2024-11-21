#!/usr/bin/env python3

import logging
import os
from diagify.cli import parse_arguments
from diagify.utils import setup_logging
from diagify.openai_client import generate_code_from_description
from diagify.diagram_executor import execute_mingrammer_code
from diagify.validation import identify_incorrect_imports, generate_correction_prompt
from diagify.utils import ensure_environment_variable
from diagify.system_prompt import system_prompt


def main():
    args = parse_arguments()
    setup_logging()

    ensure_environment_variable("OPENAI_API_KEY")

    # Step 1: Generate Mingrammer code
    mingrammer_code = generate_code_from_description(args.description, system_prompt)
    logging.info(f"Generated code:\n{mingrammer_code}")

    # Step 2: Validate the generated code
    logging.info("Validating generated code for correct imports...")
    from diagify.validation import correct_imports
    incorrect_imports = identify_incorrect_imports(mingrammer_code, correct_imports)

    if incorrect_imports:
        logging.warning(f"Incorrect imports found:\n{incorrect_imports}")
        correction_prompt = generate_correction_prompt(mingrammer_code, incorrect_imports, args.description)
        logging.info(f"Correction prompt:\n{correction_prompt}")
        # Handle corrected code, optionally request correction via OpenAI
        # For now, just log it
    else:
        logging.info("No issues with imports.")

    # Step 3: Execute the code
    try:
        output_path = execute_mingrammer_code(mingrammer_code)
        if args.output:
            os.rename(output_path, args.output)
            output_path = args.output
        logging.info(f"Diagram saved to {output_path}")
    except Exception as e:
        logging.error(f"Failed to generate diagram: {e}")
        exit(1)


if __name__ == "__main__":
    main()

