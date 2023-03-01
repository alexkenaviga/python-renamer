#!/usr/bin/env python3
import sys
import logging.config
import os
import re
import time

logging.config.fileConfig('logging.conf')
log = logging.getLogger()


def find_files(local_dir: str, pattern: re.Pattern):
    files_list = []
    for item in os.scandir(local_dir):
        if item.is_dir():
            files_list.extend(find_files(f"{os.path.join(local_dir, item.name)}", pattern))
        elif pattern.match(item.name):
            files_list.append(os.path.abspath(f"{os.path.join(local_dir, item.name)}"))
    return files_list


def rename_filename(filename: str, matcher_str: str, replace_str: str):
    p = re.compile(f"(.*)({matcher_str})(.*)", re.IGNORECASE)
    basename = os.path.basename(filename)
    m = p.match(basename)
    if m is None:
        return filename
    rename = f"{m.group(1)}{replace_str}{m.group(3)}"
    return f"{os.path.join(os.path.dirname(filename),rename)}"


if __name__ == "__main__":
    if len(sys.argv) < 4:
        log.info(f"usage: python renamer.py <directory> <matcher> <replace>")
        exit(1)

    directory = sys.argv[1]
    matcher = sys.argv[2]
    replace = sys.argv[3]
    log.info(f"you asked to replace '{matcher}' with '{replace}' in '{os.path.abspath(directory)}'")

    files = find_files(directory, re.compile(f".*{matcher}.*", re.IGNORECASE))
    files.sort()
    log.info("# Matched files:")
    for f in files:
        log.info(f" - {f} -> {os.path.basename(rename_filename(f, matcher, replace))}")

    journal_path = os.path.join(os.path.abspath(directory),f"rename-journal_{directory}_{int(time.time())}.yaml")
    with open(journal_path, "w", encoding="utf-8") as out_file:
        for f in files:
            out_file.write(f"{f}: {os.path.basename(rename_filename(f, matcher, replace))}\n")
