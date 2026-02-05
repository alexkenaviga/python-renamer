import os, re, datetime
from pathlib import Path
from collections import defaultdict


params_pattern = re.compile("(\\$)([0-9]+|\\{date\\})", re.DOTALL)
folder_time_matchers = ["MONTH", "YEAR"]


def compile_matcher(matcher: str, regexp: bool):
    if regexp:
        return re.compile(f"{matcher}", re.IGNORECASE)
    else:
        return re.compile(f"(.*)({matcher})(.*)", re.IGNORECASE)


def find_files(base: Path, pattern: re.Pattern = re.compile(".*")) -> lsit(Path):
    return [
        path.resolve()
        for path in base.rglob("*")
        if path.is_file() and pattern.match(path.name)
    ]


def rename_filename(file: Path, matcher: re.Pattern, replace_str: str) -> Path:
    m = matcher.match(file.name)
    if m is None:
        return file

    rename = f"{m.group(1)}{replace_str}{m.group(3)}"
    return file.parent.joinpath(rename).resolve()


def rename_filename_regex(file: Path, matcher: re.Pattern, replace_str: str) -> Path:
    m = matcher.match(file.name)
    if m is None:
        return file

    params_in_replace_str = extract_params(replace_str)
    rename = replace_str

    for par in params_in_replace_str:
        if par == "{date}":
            date = datetime.datetime.fromtimestamp(file.stat().st_birthtime)
            rename = rename.replace("${date}", date.strftime("%Y%m%d_%H%M%S"))
        else:
            pos = int(par)
            replace_val = m.groups()[pos-1] if pos > 0 else file.name
            rename = rename.replace(f"${pos}", replace_val)

    return file.parent.joinpath(rename).resolve()


def extract_params(replace_str):
    params_list = []
    if not replace_str: 
        return params_list
    
    param_matchers = params_pattern.findall(replace_str)
    for p, v in param_matchers:
        params_list.append(v)
    params_list.sort()
    return set(params_list)


def time_extractor(file_path:Path, matcher:str) -> Path:
    date = datetime.datetime.fromtimestamp(file_path.stat().st_birthtime)
    out = Path(date.strftime("%Y"))
    if matcher.upper() == "MONTH":
        out = out.joinpath(date.strftime("%m"))
    return out
    

def regex_extractor(file:Path, matcher:str):
    pattern = re.compile(matcher)
    m = pattern.search(file.name)
    if m:
        if len(m.groups()) > 0:
            return Path(m.group(1))
        else: 
            return Path(m.group())
    else:
        return Path("_Unmatched")

    

matchers = {
    "time": lambda f,m: time_extractor(f,m),
    "regex": lambda f,m: regex_extractor(f,m),
}


def extract_folder(file: Path, type:str, matcher:str):
    if not file:
        raise Exception(f"Invalid empty path provided for folder extraction")

    if not type or (type.lower()) not in matchers.keys():
        raise Exception(f"Invalid type {type} for folder matcher")
    
    extractor = matchers[type]
    return extractor(file, matcher)


def find_duplicates(folder_a, folder_b, exclude:tuple):
    file_map = defaultdict(list)
    exclude_list = [x.lower() for x in exclude ]
    
    folders = [Path(folder_a), Path(folder_b)] if folder_a != folder_b else Path(folder_a)
    for folder in folders:
        if not folder.is_dir():
            raise Exception(f"{folder} is not a valid directory.")
            
        # rglob("*") finds all files recursively
        for file_path in folder.rglob("*"):
            if file_path.is_file() and not is_excluded(file_path, exclude_list):
        
                # Extract metadata
                creation_date = file_path.stat().st_birthtime
                name = file_path.name
                size = file_path.stat().st_size
                
                # Use metadata as the unique key
                # key = (name, size, creation_date)
                key = (size, creation_date)
                file_map[key].append(file_path.resolve())

    # Filter out entries that only appeared once
    duplicates = {k[0]: v for k, v in file_map.items() if len(v) > 1}
    
    return duplicates


def is_excluded(file: Path, exclude: list):
    for e in exclude:
        if e in f"{file.absolute()}".lower(): 
            return True
    return False


def manage_name_conflicts(rename_map: dict[Path, Path]) -> dict[Path, Path]:
    if not rename_map:
        return {}

    # Group sources by target
    index = defaultdict(list)
    for src, ren in rename_map.items():
        index[ren].append(src)

    out = dict(rename_map)

    # Handle duplicates
    for rename, items in index.items():
        for i, item in enumerate(items[1:], start=1):  # skip the first
            out[item] = rename.parent / f"{rename.stem}_{i:03d}{rename.suffix}"

    return out