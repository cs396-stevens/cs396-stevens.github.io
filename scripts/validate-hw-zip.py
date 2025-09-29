import os
import argparse
import re
import zipfile
import json
from pathlib import Path
from enum import Enum

ZIP_DIR_PTRN = re.compile(r"(?P<last>[a-z\-]+)_(?P<first>[a-z\-]+)(:?_(?P<other>[a-z\-]+))?\.hw(?P<hw>\d+)")

LOG = False

def log(*args, **kwargs):
    if LOG: print(*args, **kwargs)

class Status(Enum):
    OK          =  0
    BADZIP      = -1
    DNE         = -2
    CORRUPTED   = -3
    EMPTY       = -4
    MULTDIRS    = -5
    BADNAME     = -6
    NOSOLUTIONS = -7
    SOLUTIONDIR = -8
    MULTCHILD   = -9
    BADPATHS    = -10

    @property
    def ok(self):
        return self == Status.OK

    @property
    def code(self):
        return self.value

    @property
    def msg(self):
        match self:
            case Status.BADZIP:
                return "not a zip file"
            case Status.DNE:
                return "file does not exist"
            case Status.CORRUPTED:
                return "file is corrupted"
            case Status.EMPTY:
                return "file is empty"
            case Status.MULTDIRS:
                return "file has too many top-level directories"
            case Status.BADNAME:
                return "internal directory has invalid naming convention"
            case Status.NOSOLUTIONS:
                return "missing solutions.pdf"
            case Status.SOLUTIONDIR:
                return "'solutions.pdf' is a directory"
            case Status.MULTCHILD:
                return "only 'solutions.pdf' and 'src/' allowed in zipfile"
            case Status.BADPATHS:
                return "invalid zipfile paths"
            case _:
                return "zipfile ok!"

def build_tree(paths):
    """
    Convert a list of file paths into a nested dictionary representing
    the folder structure.

    Example:
        ["a/b/c.txt", "a/d.txt"] ->
        {"a": {"b": {"c.txt": None}, "d.txt": None}}
    """
    tree = {}
    for path in paths:
        parts = path.strip("/").split("/")
        node = tree
        for i in range(len(parts) - 1):
            parent = parts[i]
            child = parts[i+1]
            if parent not in node:
                node[parent] = {}
            if child not in node[parent]:
                node[parent][child] = {}
            node = node[parent]
    return tree


def validate_zip(zip_path):
    """
    Validate the internal structure of a zip file.

    Args:
        zip_path (str or Path): Path to the zip file.
        expected_structure (list[str], optional): List of expected file/folder paths.

    Returns:
        Status: validation status
        dict:   zipfile internal directory structure if available
    """
    zip_path = Path(zip_path)

    if not zip_path.exists():
        return (Status.DNE, None)

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check CRC integrity
            if (bad_file := zf.testzip()):
                return (Status.CORRUPTED, None)
            # else:
            #     print("Integrity check passed (no CRC errors).")

            # actual_files = set(zf.namelist())
            # print(f"Files in archive: {len(actual_files)}")

            paths = zf.namelist()
            log(json.dumps(paths, indent=2))

            if not paths:
                return (Status.EMPTY, None)

            zip_tree = build_tree(paths)

            if not zip_tree:
                return (Status.BADPATHS, paths)

            if len(zip_tree) > 1:
                return (Status.MULTDIRS, zip_tree)

            root_dir = next(iter(zip_tree.keys()))

            if not (match := ZIP_DIR_PTRN.search(root_dir)):
                return (Status.BADNAME, zip_tree)

            if "solutions.pdf" not in zip_tree[root_dir]:
                return (Status.NOSOLUTIONS, zip_tree)

            if zip_tree[root_dir]["solutions.pdf"]:
                return (Status.SOLUTIONDIR, zip_tree)

            children = list(zip_tree[root_dir].keys())
            if 'src' not in children or len(children) > 2:
                return (Status.MULTCHILD, zip_tree)

    except zipfile.BadZipFile:
        return (Status.BADZIP, None)
    except Exception as e:
        return (Status.UNEXPECTED, None)

    return (Status.OK, zip_tree)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="validate homework zipfile submission")
    parser.add_argument("zipfile", type=Path,
        help="Path to the ZIP file to validate")
    # parser.add_argument("-e", "--expected",
    #     help="Path to a json file with the expected structure")

    args = parser.parse_args()

    # expected = None
    # if args.expected:
    #     with open(args.expected, "r") as f:
    #         expected = [line.strip() for line in f if line.strip()]

    status, _ = validate_zip(args.zipfile)
    print(status.msg)
    exit(status.code)

