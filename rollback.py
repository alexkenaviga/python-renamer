#!/usr/bin/env python3
import sys
import logging.config
import os
import re
import time

logging.config.fileConfig('logging.conf')
log = logging.getLogger()


def rename_filename(filename: str, matcher_str: str, replace_str: str):
    p = re.compile(f"(.*)({matcher_str})(.*)", re.IGNORECASE)
    basename = os.path.basename(filename)
    m = p.match(basename)
    if m is None:
        return filename
    rename = f"{m.group(1)}{replace_str}{m.group(3)}"
    return f"{os.path.join(os.path.dirname(filename),rename)}"


def print_usage():
    print("usage: python rollback.py <option_flags> <journal_file>")
    print("options:")
    print(" - d: dry_run, no renaming")
    print(" - q: quiet, no logging")
    print("i.e.: python rollback.py d ./rename-journal_test_1677664708.yaml")


def option_of(argv: list, flag: str):
    if argv is None or len(argv) <= 2:
        return False
    return flag in str(argv[1])


if __name__ == "__main__":
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print_usage()
        exit(1)

    options_delta = 0
    if len(sys.argv) > 2:
        options_delta = 1

    journal_path = sys.argv[1 + options_delta]
    dry_run = option_of(sys.argv, "d")
    quiet = option_of(sys.argv, "q")

    if not quiet:
        log.info(f"you asked to restore '{journal_path}' [d:{dry_run}, q:{quiet}]")
    if not os.path.exists(journal_path) or os.path.isdir(journal_path):
        log.error(f"{journal_path} is not a valid file!")
        exit(2)

    if dry_run:
        log.warning("DRY_RUN active: only journal created, no rename done.")

    with open(journal_path, "r", encoding="utf-8") as journal_file:
        file_line = journal_file.readline()
        while file_line:
            try:
                split = file_line.split(":")
                r = split[0].strip()
                f = split[1].strip()
                if not os.path.exists(f) or os.path.isdir(f):
                    if not quiet:
                        log.info(f" - skipping {f} [doesn't exist]")
                else:
                    if not quiet:
                        log.info(f" - renaming {f} -> {os.path.basename(r)}")
                    if not dry_run:
                        os.rename(f, r)

            except Exception as e:
                log.error(f" - an error occurred while evaluating {file_line}: {str(e)}")

            file_line = journal_file.readline()
