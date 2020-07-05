"""
Check if a project meets the minimum requirements for testing
"""
from pathlib import Path

root = Path('/Users/Edu/dev/ds-project-template/imdb')

assert (root / 'environment.yml').exists()