import click


def dryrun_opt():
    return click.option(
        "-d",
        "--dryrun",
        is_flag=True,
        show_default=True,
        default=False,
        help="Execute a Dry Run (doesn't apply any change)",
    )

def quiet_opt():
    return click.option(
        "-q",
        "--quiet",
        is_flag=True,
        show_default=True,
        default=False,
        help="quiet, no logging",
    )

def clean_opt():
    return click.option(
        "-c",
        "--clean",
        is_flag=True,
        show_default=True,
        default=False,
        help="no journal (WARN: no rollback available with no journal)",
    )

def regexp_option():
    return click.option(
        "-e",
        "--regexp",
        is_flag=True,
        show_default=True,
        default=False,
        help="If set, matcher will be used as a regexp, exact match is used otherwise",
    )