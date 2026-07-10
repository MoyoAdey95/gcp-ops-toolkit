"""Shared argparse setup so every tool takes the same base flags."""

import argparse


def base_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="output format (default: table)",
    )
    return parser
