#!/usr/bin/env python3
import sys, logging.config, os, re, time, click

logging.config.fileConfig('logging.conf')
log = logging.getLogger()
params_pattern = re.compile("(\\$)([0-9])", re.DOTALL)


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
i.e.: python renamer.py d ./test '_[0-9]{8}' 'some_string'
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

    matcher_c = compile_matcher(matcher, regexp)
    files = find_files(directory, matcher_c)
    files.sort()

    rename_map = {}
    for f in files:
        if regexp:
            rename_map[f] = rename_filename_r(f, matcher_c, replace)
        else:
            rename_map[f] = rename_filename(f, matcher_c, replace)
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


def compile_matcher(matcher: str, regexp: bool):
    if regexp:
        return re.compile(f"{matcher}", re.IGNORECASE)
    else:
        return re.compile(f"(.*)({matcher})(.*)", re.IGNORECASE)


def find_files(local_dir: str, pattern: re.Pattern):
    files_list = []
    for item in os.scandir(local_dir):
        if item.is_dir():
            files_list.extend(find_files(f"{os.path.join(local_dir, item.name)}", pattern))
        elif pattern.match(item.name):
            files_list.append(os.path.abspath(f"{os.path.join(local_dir, item.name)}"))
    return files_list


def rename_filename(filename: str, matcher: re.Pattern, replace_str: str):
    basename = os.path.basename(filename)
    m = matcher.match(basename)
    if m is None:
        return filename
    rename = f"{m.group(1)}{replace_str}{m.group(3)}"
    return f"{os.path.join(os.path.dirname(filename),rename)}"


def rename_filename_r(filename: str, matcher: re.Pattern, replace_str: str):
    basename = os.path.basename(filename)
    m = matcher.match(basename)
    if m is None:
        return filename

    params_in_replace_str = extract_params(replace_str)
    rename = replace_str
    for p in params_in_replace_str:
        replace_val = m.groups()[p-1] if p > 0 else filename
        # log.debug(f"  - replacing ${p} with {replace_val}")
        rename = rename.replace(f"${p}", replace_val)
    # log.debug(f"  - result {replace_str} -> {rename}")
    return f"{os.path.join(os.path.dirname(filename),rename)}"


def extract_params(replace_str):
    param_matchers = params_pattern.findall(replace_str)
    params_list = []
    for p, v in param_matchers:
        params_list.append(int(v))
    params_list.sort()
    return set(params_list)


# Setup

@click.group()
def cli():
    """Main entry point for the CLI."""


cli.add_command(rename_files_command)