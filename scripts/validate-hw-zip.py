import os
import argparse
import re
import zipfile
from pathlib import Path

ZIP_DIR_PTRN = re.compile(r"(?P<last>[a-z\-]+)_(?P<first>[a-z\-]+)(:?_(?P<other>[a-z\-]+))?\.hw(?P<hw>\d+)")

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
        bool: True if validation passes, False otherwise.
    """
    zip_path = Path(zip_path)

    if not zip_path.exists():
        print(f"Error: {zip_path} does not exist.")
        return False

    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            # Check CRC integrity
            if (bad_file := zf.testzip()):
                print(f"Integrity check failed: {bad_file} is corrupted.")
                return False
            # else:
            #     print("Integrity check passed (no CRC errors).")

            # actual_files = set(zf.namelist())
            # print(f"Files in archive: {len(actual_files)}")

            paths = zf.namelist()

            if not paths:
                print(f"{str(zip_path)} is empty.")
                return False

            zip_tree = build_tree(paths)

            if len(zip_tree) > 1:
                print(f"{str(zip_path)} has too many top-level directories.")
                return False

            root_dir = next(iter(zip_tree.keys()))

            if not (match := ZIP_DIR_PTRN.search(root_dir)):
                print(f"invalid naming convention: {root_dir}")
                print("must be all lowercase, spaces replaced with '_'.")
                return False

            if "solutions.pdf" not in zip_tree[root_dir]:
                print(f"missing '{root_dir}/solutions.pdf'")
                return False

            if zip_tree[root_dir]["solutions.pdf"]:
                print("'solutions.pdf' is a directory")
                return False

            children = list(zip_tree[root_dir].keys())
            if 'src' not in children or len(children) > 2:
                print(f"only 'solutions.pdf' and 'src/' allowed in zipfile")
                return False

            return True
    except zipfile.BadZipFile:
        print("Error: Not a valid ZIP file.")
        return False


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

    if (ok := validate_zip(args.zipfile)):
        print(f"{args.zipfile} ok!")
    exit(0 if ok else 2)

