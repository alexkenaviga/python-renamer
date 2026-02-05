#!/usr/bin/env python3
import sys, logging.config, os, re, time, click, contextlib
from renamer import functions as func
from renamer import options as opt
from renamer import defaults
from pathlib import Path

log = logging.getLogger(__name__)


@click.command(name="rename", help="""Rename files given a matching-pattern and a replace-string\n
i.e.: python renamer.py rename -d ./test '_[0-9]{8}' 'some_string'
""")
@click.argument("directory", type=click.Path(exists=True, file_okay=False),)
@click.argument("matcher", type=str)
@click.argument("replace", type=str)
@opt.regexp_option()
@opt.clean_opt()
@opt.dryrun_opt()
@opt.quiet_opt()
def rename_files_command(
    directory: str, 
    matcher:str,
    replace:str,
    regexp: bool,
    dryrun: bool,
    quiet: bool,
    clean: bool,
):
    directory = Path(directory)
    if not quiet:
        log.info(f"you asked to replace [regexp: {regexp}] '{matcher}' with '{replace}' in '{directory.absolute()}'")

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
        log.debug("MATCHED FILES:")
        for f, r in rename_map.items():
            log.debug(f" - {f} -> {r.name}")

    if not clean:
        journal_path = directory.joinpath(f"rename-journal_{directory.name}_{int(time.time())}.yaml")
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
            log.info(f" - renaming {f} -> {r.name}")
        f.rename(r)


@click.command(name="prepend", help="""Prepends a string to matching filenames (matcher is threated as regexp)\n
i.e.: python renamer.py prepend -d ./test '_[0-9]{8}' 'a_prefix'
""")
@click.argument("directory", type=click.Path(exists=True, file_okay=False),)
@click.argument("matcher", type=str)
@click.argument("prefix", type=str)
@opt.clean_opt()
@opt.dryrun_opt()
@opt.quiet_opt()
def prepend_files_command(
    directory: str, 
    matcher:str,
    prefix:str,
    dryrun: bool,
    quiet: bool,
    clean: bool,
):
    directory = Path(directory)

    if not quiet:
        log.info(f"you asked to prepend '{prefix}' to '{matcher}' in '{directory.absolute()}'")

    files = func.find_files(directory, func.compile_matcher(matcher, True))
    files.sort()

    rename_map = {}
    for f in files:
        rename_map[f] = f.parent.joinpath(f"{prefix}{f.name}")
    if not quiet:
        log.debug("MATCHED FILES:")
        for f, r in rename_map.items():
            log.debug(f" - {f} -> {r.name}")

    if not clean:
        journal_path = directory.joinpath(f"rename-journal_{directory.name}_{int(time.time())}.yaml")
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
                log.info(f" - renaming {f} -> {r.name}")
            f.rename(r)


@click.command(name="restore", help="""Restores file renaming based on a journal file (Works only if folder was unmodified)\n
i.e.: python renamer.py restore -d ./test/journal.yaml'
""")
@opt.click.argument("journal", type=click.Path(exists=True, dir_okay=False))
@opt.quiet_opt()
@opt.dryrun_opt()
def restore_files_command(
    journal:str,
    dryrun: bool,
    quiet: bool
):
    if not quiet:
        log.info(f"you asked to restore '{journal}' [d:{dryrun}, q:{quiet}]")
    if not os.path.exists(journal) or os.path.isdir(journal):
        log.error(f"{journal} is not a valid file!")
        exit(2)

    if dryrun:
        log.warning("DRY_RUN active: only journal created, no rename done.")

    with open(journal, "r", encoding="utf-8") as journal_file:
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
                    if not dryrun:
                        os.rename(f, r)

            except Exception as e:
                log.error(f" - an error occurred while evaluating {file_line}: {str(e)}")

            file_line = journal_file.readline()


@click.command(name="organize", help="""Creates folders based on:\n
- time (if -t is set)
- a piece of filename (if -t is set)

Files are moved in created folder. WARN: action is currently unreversable!

i.e.: python renamer.py organize -d ./test -t MONTH
""")
@click.argument("directory", type=click.Path(exists=True, file_okay=False))
@click.option('-o', '--output-folder', type=str, required=False, default=".", help='Output root folder')
@click.option('-t', '--time-granularity', type=click.Choice(func.folder_time_matchers, 
    case_sensitive=False), help='MONTH for YYYY/MM folders, YEAR for YYYY folders')
@click.option('-e', '--expression', help='The piece of file-name to use as folder-name')
@opt.quiet_opt()
@opt.dryrun_opt()
@opt.clean_opt()
def organize_folders_command(
    directory: str,
    output_folder: str,
    dryrun: bool,
    quiet: bool,
    time_granularity: str,
    expression: str,
    clean: bool
):
    directory = Path(directory)
    
    if not time_granularity and not expression:
        log.error(f"at least one of -t/--time-granularity or -e/--expression options must be set")
        exit(2)
    elif time_granularity and expression:
        log.error(f"options -t/--time-granularity and -e/--expression are mutually exclusive")
        exit(2)

    criteria = "time" if time_granularity else "regex"
    matcher = time_granularity if time_granularity else expression

    if not quiet:
        log.info(f"you asked to create folders for  '{directory}' using method [{criteria}: {matcher}'] in target folder '{output_folder}'")
    elif not os.path.exists(journal) or os.path.isdir(journal):
        log.error(f"{journal} is not a valid file!")
        exit(2)

    journal = {}
    target_path = Path(output_folder)
    files_index = func.find_files(directory)
    for file in files_index:
        folder = func.extract_folder(file, criteria, matcher)
        file_path = Path(file)
        target_file = target_path.joinpath(folder).joinpath(file_path.name).resolve()
        journal[file_path] = target_file

    if not quiet:
        log.debug("MATCHED FILES:")
        for f,r in journal.items():
            log.debug(f" - {f}: {r.parent.absolute()}") 
    
    if dryrun:
        log.warning("DRY_RUN active: only journal will be created")

    journal_path = directory.joinpath(f"organize-journal_{directory.name}_{int(time.time())}.yaml").resolve()
    # No file for 'clean' runs
    cm = contextlib.nullcontext() if clean else open(journal_path, "w", encoding="utf-8")
    if clean: log.warning("CLEAN active: no journal created.")

    with cm as out_file:
        if not quiet: log.info("STARTING ORGANIZATION:")
        for f, r in journal.items():
            if not quiet: log.info(f" - moving {f.name} -> {r.parent.absolute()}")
            
            if not dryrun:
                if not r.parent.exists():
                    r.parent.mkdir(parents=True, exist_ok=True)
                    if not quiet: log.info(f"CREATED FOLDER: {r.parent.absolute()}")
                
                f.rename(r)

            if out_file: out_file.write(f"{f.absolute()}: {r.absolute()}\n")
        if not quiet: log.info(f"journal path: {journal_path}")


@click.command(name="find-duplicates", help="""Find duplicates in 2 folders\n
i.e.: python renamer.py find-duplicates ./test ./test-2
""")
@click.argument("directory-a", type=click.Path(exists=True, file_okay=False))
@click.argument("directory-b", type=click.Path(exists=True, file_okay=False))
@click.option('-e', '--exclude', help='folder/file names to exclude. Can be repeated', multiple=True)
# @click.option('-s', '--show', type=click.Choice(["a", "b"], case_sensitive=False), default="b")
@opt.clean_opt()
def find_duplicates_command(
    directory_a: str,
    directory_b: str,
    exclude: tuple,
    #show: str,
    clean: bool
):
    
    #filter = Path(directory_b) if show.lower() == "b" else Path(directory_a)
    d = func.find_duplicates(directory_a, directory_b, exclude)
    duplicates = []
    for k,v in d.items():
        item = []
        for i in v:
            item.append(str(i.resolve().absolute()))
            #if i.is_relative_to(filter):
        duplicates.append(item)
    
    journal_path = Path(f"./diff.yaml")
    # No file for 'clean' runs
    cm = contextlib.nullcontext() if clean else open(journal_path, "w", encoding="utf-8")
    if clean: log.warning("CLEAN active: no journal created.")

    with cm as out_file:
        log.info("DUPLICATES:")
        for x in duplicates:
            log.info(f"{', '.join(x)}")
            if out_file: out_file.write(f"{', '.join(x)}\n")
        if not clean: 
            log.info(f"journal path: {journal_path}")


# Setup

@click.group()
@click.option('--log-config', type=click.Path(exists=True, dir_okay=False), help="Path to logging.conf")
def cli(log_config):
    if log_config:
        # If the user provides a file, use the old fileConfig
        logging.config.fileConfig(log_config, disable_existing_loggers=False)
    else:
        # Otherwise, use the programmatic dictionary config
        logging.config.dictConfig(defaults.DEFAULT_LOGGING_DICT)
       
    """Main entry point for the CLI."""


cli.add_command(rename_files_command)
cli.add_command(prepend_files_command)
cli.add_command(restore_files_command)
cli.add_command(organize_folders_command)
cli.add_command(find_duplicates_command)