import os
import logging


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def ensure_environment_variable(var_name: str):
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Environment variable '{var_name}' is not set.")
    return value
