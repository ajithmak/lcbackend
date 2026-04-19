#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lakshmi_crackers.settings')

    # Load .env file if present (development convenience)
    # In production, set environment variables directly on the server.
    try:
        from dotenv import load_dotenv
        load_dotenv()  # reads .env from the current working directory
    except ImportError:
        pass  # python-dotenv not installed → env vars already set externally

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
