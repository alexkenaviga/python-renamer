import os, re


params_pattern = re.compile("(\\$)([0-9])", re.DOTALL)


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


def rename_filename_regex(filename: str, matcher: re.Pattern, replace_str: str):
    basename = os.path.basename(filename)
    m = matcher.match(basename)
    if m is None:
        return filename

    params_in_replace_str = extract_params(replace_str)
    rename = replace_str
    for p in params_in_replace_str:
        replace_val = m.groups()[p-1] if p > 0 else filename
        rename = rename.replace(f"${p}", replace_val)
    return f"{os.path.join(os.path.dirname(filename),rename)}"


def prepend_filename(filename: str, prepend: str):
    basename = os.path.basename(filename)
    rename = f"{prepend}{basename}"
    return f"{os.path.join(os.path.dirname(filename),rename)}"


def extract_params(replace_str):
    param_matchers = params_pattern.findall(replace_str)
    params_list = []
    for p, v in param_matchers:
        params_list.append(int(v))
    params_list.sort()
    return set(params_list)