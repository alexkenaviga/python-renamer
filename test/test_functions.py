import re, pytest, datetime
from renamer import functions as func
from types import SimpleNamespace
from pathlib import Path


def test_extract_params_success():
    """Tests common matching for extract_params function"""
    some_str = "aaa_$1_bbb_$52_${date}_$n"
    data = func.extract_params(some_str)
    assert "1" in data
    assert "52" in data
    assert "{date}" in data
    assert "n" not in data

    assert len(func.extract_params("")) == 0
    assert len(func.extract_params(None)) == 0


def test_rename_filename_regex_success(monkeypatch):
    dt_utc = datetime.datetime(2026, 2, 5, 8, 30, 0, tzinfo=datetime.timezone.utc)
    fixed_timestamp = int(dt_utc.timestamp())
    fake_stat = SimpleNamespace(st_birthtime=fixed_timestamp)

    def fake_stat_method(self):
        return fake_stat

    monkeypatch.setattr(Path, "stat", fake_stat_method)

    matcher = func.compile_matcher("(some_filename_about_)(something)(.*)", True)
    input = Path("some_filename_about_something.png")
    out = func.rename_filename_regex(input, matcher, "$2_${date}$3")

    assert out.name == "something_20260205_093000.png"
    assert out.parent.resolve() == input.parent.resolve(),\
        f"Expected input parent '{input.parent}' to be equal to output parent '{out.parent}'"


def test_rename_filename_success(monkeypatch):
    matcher = func.compile_matcher("about_something", False)
    input = Path("some_filename_about_something.png")
    out = func.rename_filename(input, matcher, "i_like")
    
    assert out.name == "some_filename_i_like.png"
    assert out.parent.resolve() == input.parent.resolve(),\
        f"Expected input parent '{input.parent}' to be equal to output parent '{out.parent}'"


def test_find_files_mocked(monkeypatch):
    class FakePath:
        def __init__(self, name, is_file=True):
            self.name = name
            self._is_file = is_file
        def is_file(self):
            return self._is_file
        def resolve(self):
            return f"/mocked/path/{self.name}"
    
    fake_files = [
        FakePath("a1.txt"),
        FakePath("a2.csv"),
        FakePath("b1.csv"),
        FakePath("subdir", is_file=False),  # simulate a directory
    ]

    def fake_rglob(self, pattern):
        return fake_files

    monkeypatch.setattr(Path, "rglob", fake_rglob)

    base = Path("/does/not/matter")
    result = func.find_files(base, re.compile(r"^a\d.*\.*"))

    assert len(result) == 2
    assert "/mocked/path/a1.txt" in result
    assert "/mocked/path/a2.csv" in result


def test_time_extractor_success(monkeypatch) -> Path:
    dt_utc = datetime.datetime(2026, 2, 5, 8, 30, 0, tzinfo=datetime.timezone.utc)
    fixed_timestamp = int(dt_utc.timestamp())
    fake_stat = SimpleNamespace(st_birthtime=fixed_timestamp)

    def fake_stat_method(self):
        return fake_stat

    monkeypatch.setattr(Path, "stat", fake_stat_method)

    input = Path("some_filename_about_something.png")
    out = func.time_extractor(input, "MonTH")

    assert out.name == "02"
    assert out.parent.name == "2026"


def test_regex_extractor_success(monkeypatch) -> Path:
    input = Path("some_filename_about_something.png")
    assert func.regex_extractor(input, ".*_(.+)\\..*").name == "something"
    assert func.regex_extractor(input, "^.{4}").name == "some"
 

def test_manage_name_conflicts_empty_map():
    assert func.manage_name_conflicts({}) == {}

def test_manage_name_conflicts_no_duplicates():
    rename_map = {
        Path("a.txt"): Path("x.txt"),
        Path("b.txt"): Path("y.txt"),
    }
    assert func.manage_name_conflicts(rename_map) == rename_map

def test_manage_name_conflicts_with_duplicates():
    rename_map = {
        Path("a.txt"): Path("file.txt"),
        Path("b.txt"): Path("file.txt"),
        Path("c.txt"): Path("file.txt"),
    }
    result = func.manage_name_conflicts(rename_map)
    expected = {
        Path("a.txt"): Path("file.txt"),
        Path("b.txt"): Path("file_001.txt"),
        Path("c.txt"): Path("file_002.txt"),
    }
    assert result == expected

def test_manage_name_conflicts_mixed_duplicates():
    rename_map = {
        Path("a.txt"): Path("file.txt"),
        Path("b.txt"): Path("file.txt"),
        Path("c.txt"): Path("unique.txt"),
    }
    result = func.manage_name_conflicts(rename_map)
    expected = {
        Path("a.txt"): Path("file.txt"),
        Path("b.txt"): Path("file_001.txt"),
        Path("c.txt"): Path("unique.txt"),
    }
    assert result == expected

def test_manage_name_conflicts_nested_paths():
    rename_map = {
        Path("folder/a.txt"): Path("folder/file.txt"),
        Path("folder/b.txt"): Path("folder/file.txt"),
        Path("folder/c.txt"): Path("folder/file.txt"),
    }
    result = func.manage_name_conflicts(rename_map)
    expected = {
        Path("folder/a.txt"): Path("folder/file.txt"),
        Path("folder/b.txt"): Path("folder/file_001.txt"),
        Path("folder/c.txt"): Path("folder/file_002.txt"),
    }
    assert result == expected