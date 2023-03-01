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


def print_usage():
    print("usage: python renamer.py <option_flags> <directory> <matcher> <replace>")
    print("options:")
    print(" - d: dry_run, no renaming")
    print(" - q: quiet, no logging")
    print(" - d: clean, no journal (WARN: no rollback available with no journal)")
    print("i.e.: python renamer.py d ./test '_[0-9]{8}' ''")


def option_of(argv: list, flag: str):
    if argv is None or len(argv) <= 4:
        return False
    return flag in str(argv[1])


if __name__ == "__main__":
    if len(sys.argv) < 4 or len(sys.argv) > 5:
        print_usage()
        exit(1)

    options_delta = 0
    if len(sys.argv) > 4:
        options_delta = 1

    directory = sys.argv[1+options_delta]
    matcher = sys.argv[2+options_delta]
    replace = sys.argv[3+options_delta]
    dry_run = option_of(sys.argv, "d")
    quiet = option_of(sys.argv, "q")
    no_journal = option_of(sys.argv, "c")

    if not quiet:
        log.info(f"you asked to replace '{matcher}' with '{replace}' in '{os.path.abspath(directory)}'")
    if not (os.path.exists(directory) or os.path.isdir(directory)):
        log.error(f"{directory} is not a valid directory!")
        exit(2)

    files = find_files(directory, re.compile(f".*{matcher}.*", re.IGNORECASE))
    files.sort()

    rename_map = {}
    for f in files:
        rename_map[f] = rename_filename(f, matcher, replace)
    if not quiet:
        log.info("MATCHED FILES:")
        for f,r in rename_map.items():
            log.info(f" - {f} -> {os.path.basename(r)}")

    if not no_journal:
        journal_path = os.path.join(os.path.abspath(directory),
                                    f"rename-journal_{os.path.basename(directory)}_{int(time.time())}.yaml")
        with open(journal_path, "w", encoding="utf-8") as out_file:
            for f, r in rename_map.items():
                out_file.write(f"{f}: {r}\n")
        if not quiet:
            log.info(f"journal path: {journal_path}")
    else:
        log.warning("CLEAN active: no journal created, no rollback available.")

    if dry_run:
        log.warning("DRY_RUN active: only journal created, no rename done.")
        exit(0)

    if not quiet:
        log.info("STARTING RENAMING:")
        for f, r in rename_map.items():
            if not quiet:
                log.info(f" - renaming {f} -> {os.path.basename(r)}")
            os.rename(f, r)
