import sys
import logging.config
import os
import re

logging.config.fileConfig('logging.conf')
log = logging.getLogger()


def find_files(local_dir: str, pattern: re.Pattern):
    files_list = []
    for item in os.scandir(local_dir):
        if item.is_dir():
            files_list.extend(find_files(f"{local_dir}/{item.name}", pattern))
        elif pattern.match(item.name):
            files_list.append(os.path.abspath(f"{local_dir}/{item.name}"))
    return files_list


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"usage: python renamer.py <directory> <matcher> <replace>")
        exit(1)

    directory = sys.argv[1]
    matcher = sys.argv[2]
    replace = sys.argv[3]
    print(f"you asked to replace '{matcher}' with '{replace}' in '{directory}'")

    files = find_files(directory, re.compile(f".*{matcher}.*", re.IGNORECASE))
    files.sort()
    print("# Matched files:")
    for f in files:
        print(f" - {f}")
