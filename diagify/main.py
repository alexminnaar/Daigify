#!/usr/bin/env python3

import logging
import os
from diagify.cli import parse_arguments
from diagify.utils import setup_logging
from diagify.llm_client import call_openai,call_openai_user_prompt_only
from diagify.diagram_executor import execute_mingrammer_code
from diagify.validation import identify_incorrect_imports, generate_correction_prompt, create_error_correction_prompt
from diagify.utils import ensure_environment_variable
from diagify.system_prompt import system_prompt


def main():
    args = parse_arguments()
    setup_logging()
    ensure_environment_variable("OPENAI_API_KEY")
    logging.info(f"Diagify is using model: {args.model}")

    # Step 1: Generate Mingrammer code
    logging.info("Generating Mingrammer code...")
    mingrammer_code = call_openai(args.description, system_prompt, args.model)

    # Step 2: Validate the generated code
    from diagify.validation import correct_imports
    incorrect_imports = identify_incorrect_imports(mingrammer_code, correct_imports)

    if incorrect_imports:
        logging.info(f"Incorrect imports found! Diagify will try to correct this...")
        correction_prompt = generate_correction_prompt(mingrammer_code, incorrect_imports, args.description)

        # Step 2a: Correct the imports using OpenAI API
        corrected_code = call_openai_user_prompt_only(correction_prompt, args.model)
        if corrected_code:
            mingrammer_code = corrected_code
        else:
            logging.error("Failed to correct imports. Proceeding with the original code.")
    else:
        logging.info("No issues with imports.")

    # Step 3: Execute the code
    try:
        output_path = execute_mingrammer_code(mingrammer_code)
        if args.output:
            os.rename(output_path, args.output)
            output_path = args.output
        logging.info(f"Final Mingrammer code generated:\n{mingrammer_code}")
        logging.info(f"Success! Diagram saved to {output_path}")
    except Exception as e:

        error_traceback = str(e)
        logging.info(f"Execution failed with error! Diagify will try to correct this...")

        # Step 3a: Generate an error correction prompt
        error_correction_prompt = create_error_correction_prompt(mingrammer_code, error_traceback, args.description)

        # Step 3b: Request OpenAI to fix the error
        fixed_code = call_openai(error_correction_prompt, system_prompt, args.model)

        if fixed_code:
            try:
                output_path = execute_mingrammer_code(fixed_code)
                if args.output:
                    os.rename(output_path, args.output)
                    output_path = args.output
                logging.info(f"Final Mingrammer code generated:\n{mingrammer_code}")
                logging.info(f"Success! Diagram saved to {output_path}")
            except Exception as retry_error:
                logging.error(f"Retry failed with error: {retry_error}")
                exit(1)
        else:
            logging.error("Failed to fix the code after execution error. Exiting.")
            exit(1)


if __name__ == "__main__":
    main()

