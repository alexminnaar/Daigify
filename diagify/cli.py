import argparse


def parse_arguments():
    parser = argparse.ArgumentParser(description="Diagify: Translate descriptions into technical diagrams.")
    parser.add_argument("description", type=str, help="The description of the diagram to generate.")
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional output path for the generated diagram (default: current directory).",
    )
    return parser.parse_args()
