"""Initialize or reset the SQLite database (use on PythonAnywhere Bash console)."""
import sys

from main import init_database

if __name__ == '__main__':
    force = '--reset' in sys.argv
    init_database(force=force)
