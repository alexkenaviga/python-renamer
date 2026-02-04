#!/usr/bin/env python3
import sys, logging.config, os, re, time, click
from renamer import functions as func

logging.config.fileConfig('logging.conf')
log = logging.getLogger()


def common_options(f):
    """
    Decorate the command with common args and options
    """
    f = click.option(
        "-d",
        "--dryrun",
        is_flag=True,
        show_default=True,
        default=False,
        help="Execute a Dry Run (doesn't apply any change)",
    )(f)
    f = click.option(
        "-c",
        "--clean",
        is_flag=True,
        show_default=True,
        default=False,
        help="no journal (WARN: no rollback available with no journal)",
    )(f)
    f = click.option(
        "-q",
        "--quiet",
        is_flag=True,
        show_default=True,
        default=False,
        help="quiet, no logging",
    )(f)

    return f


@click.command(name="rename", help="""Rename files given a matching-pattern and a replace-string\n
i.e.: python renamer.py rename -d ./test '_[0-9]{8}' 'some_string'
""")
@click.argument("directory", type=str,)
@click.argument("matcher", type=str)
@click.argument("replace", type=str)
@click.option(
        "-e",
        "--regexp",
        is_flag=True,
        show_default=True,
        default=False,
        help="If set, matcher will be used as a regexp, exact match is used otherwise",
    )
@common_options
def rename_files_command(
    directory: str, 
    matcher:str,
    replace:str,
    regexp: bool,
    dryrun: bool,
    quiet: bool,
    clean: bool,
):
    if not quiet:
        log.info(f"you asked to replace [regexp: {regexp}] '{matcher}' with '{replace}' in '{os.path.abspath(directory)}'")
    if not (os.path.exists(directory) or os.path.isdir(directory)):
        log.error(f"{directory} is not a valid directory!")
        exit(2)

    matcher_c = func.compile_matcher(matcher, regexp)
    files = func.find_files(directory, matcher_c)
    files.sort()

    rename_map = {}
    for f in files:
        if regexp:
            rename_map[f] = func.rename_filename_regex(f, matcher_c, replace)
        else:
            rename_map[f] = func.rename_filename(f, matcher_c, replace)
    if not quiet:
        log.info("MATCHED FILES:")
        for f, r in rename_map.items():
            log.info(f" - {f} -> {os.path.basename(r)}")

    if not clean:
        journal_path = os.path.join(os.path.abspath(directory),
                                    f"rename-journal_{os.path.basename(directory)}_{int(time.time())}.yaml")
        with open(journal_path, "w", encoding="utf-8") as out_file:
            for f, r in rename_map.items():
                out_file.write(f"{f}: {r}\n")
        if not quiet:
            log.info(f"journal path: {journal_path}")
    else:
        log.warning("CLEAN active: no journal created, no rollback available.")

    if dryrun:
        log.warning("DRY_RUN active: only journal created, no rename done.")
        exit(0)

    if not quiet:
        log.info("STARTING RENAMING:")
        for f, r in rename_map.items():
            if not quiet:
                log.info(f" - renaming {f} -> {os.path.basename(r)}")
            os.rename(f, r)


@click.command(name="prepend", help="""Prepends a string to matching filenames (matcher is threated as regexp)\n
i.e.: python renamer.py prepend -d ./test '_[0-9]{8}' 'a_prefix'
""")
@click.argument("directory", type=str,)
@click.argument("matcher", type=str)
@click.argument("prefix", type=str)
@common_options
def prepend_files_command(
    directory: str, 
    matcher:str,
    prefix:str,
    dryrun: bool,
    quiet: bool,
    clean: bool,
):
    if not quiet:
        log.info(f"you asked to prepend '{prefix}' to '{matcher}' in '{os.path.abspath(directory)}'")
    if not (os.path.exists(directory) or os.path.isdir(directory)):
        log.error(f"{directory} is not a valid directory!")
        exit(2)

    files = func.find_files(directory, func.compile_matcher(matcher, True))
    files.sort()

    rename_map = {}
    for f in files:
        rename_map[f] = func.prepend_filename(f, prefix)
    if not quiet:
        log.info("MATCHED FILES:")
        for f, r in rename_map.items():
            log.info(f" - {f} -> {os.path.basename(r)}")

    if not clean:
        journal_path = os.path.join(os.path.abspath(directory),
                                    f"rename-journal_{os.path.basename(directory)}_{int(time.time())}.yaml")
        with open(journal_path, "w", encoding="utf-8") as out_file:
            for f, r in rename_map.items():
                out_file.write(f"{f}: {r}\n")
        if not quiet:
            log.info(f"journal path: {journal_path}")
    else:
        log.warning("CLEAN active: no journal created, no rollback available.")

    if dryrun:
        log.warning("DRY_RUN active: only journal created, no rename done.")
        exit(0)

    if not quiet:
        log.info("STARTING PREPENDING:")
        for f, r in rename_map.items():
            if not quiet:
                log.info(f" - renaming {f} -> {os.path.basename(r)}")
            os.rename(f, r)


# Setup

@click.group()
def cli():
    """Main entry point for the CLI."""


cli.add_command(rename_files_command)
cli.add_command(prepend_files_command)