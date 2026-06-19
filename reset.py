#!/usr/bin/env python3
"""Standalone script to reset pipeline cache and data."""

import argparse
from pipeline.utils.cleanup import CleanupService


def main():
    parser = argparse.ArgumentParser(
        description="Reset pipeline cache and data"
    )
    parser.add_argument(
        "--db",
        action="store_true",
        help="Reset SQLite database only"
    )
    parser.add_argument(
        "--embeddings",
        action="store_true",
        help="Reset ChromaDB embeddings only"
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Reset raw data files only"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=True,
        help="Reset everything (default if no options specified)"
    )
    
    args = parser.parse_args()
    cleanup = CleanupService()
    
    # If any specific option is chosen, disable default --all
    has_specific_option = args.db or args.embeddings or args.raw
    if has_specific_option:
        args.all = False
    
    if args.db:
        cleanup.reset_database()
    elif args.embeddings:
        cleanup.reset_embeddings()
    elif args.raw:
        cleanup.reset_raw_data()
    elif args.all:
        cleanup.reset_all()


if __name__ == "__main__":
    main()
