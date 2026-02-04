import os, re, datetime
from pathlib import Path
from collections import defaultdict


params_pattern = re.compile("(\\$)([0-9])", re.DOTALL)
folder_time_matchers = ["MONTH", "YEAR"]


def compile_matcher(matcher: str, regexp: bool):
    if regexp:
        return re.compile(f"{matcher}", re.IGNORECASE)
    else:
        return re.compile(f"(.*)({matcher})(.*)", re.IGNORECASE)


def find_files(local_dir: str, pattern: re.Pattern = re.compile(".*")):
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


def time_extractor(file:str, matcher:str):
    file_path = Path(file)
    date = datetime.datetime.fromtimestamp(file_path.stat().st_birthtime)
    out = Path(date.strftime("%Y"))
    if matcher.upper() == "MONTH":
        out = out.joinpath(date.strftime("%m"))
    return out
    

def regex_extractor(file:str, matcher:str):
    pattern = re.compile(matcher)
    m = pattern.search(Path(file).name)
    if m:
        return Path(m.group())
    else:
        return Path("_Unmatched")

    

matchers = {
    "time": lambda f,m: time_extractor(f,m),
    "regex": lambda f,m: regex_extractor(f,m),
}


def extract_folder(file: str, type:str, matcher:str):
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
                key = (name, size, creation_date)
                file_map[key].append(file_path.resolve())

    # Filter out entries that only appeared once
    duplicates = {k[0]: v for k, v in file_map.items() if len(v) > 1}
    
    return duplicates


def is_excluded(file: Path, exclude: list):
    for e in exclude:
        if e in f"{file.absolute()}".lower(): 
            return True
    return False
