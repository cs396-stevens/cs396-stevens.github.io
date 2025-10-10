import os
import re
import zipfile
import shutil
import argparse
import tempfile

from pathlib import Path

LOG = False

NAME_PTRN = re.compile(r"[a-zA-Z'\-]+")

def log(*args, **kwargs):
    global LOG
    if LOG: print(*args, **kwargs)

SKIP_FILES = [
    ".DS_Store",
]

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=str, default=None,
        help="first name")
    parser.add_argument("--last", type=str, default=None,
        help="last name")
    parser.add_argument("--hw", type=int, default=None,
        help="integer homework number")
    parser.add_argument("--solutions", type=Path, default=None,
        help="path to solutions.pdf")
    parser.add_argument("--src", type=Path, default=None,
        help="path to src directory")
    parser.add_argument("--out", type=Path, default=Path("."),
        help="path to output directory")
    parser.add_argument("-v", dest='verbose', action='store_true', default=LOG,
        help="print debug output")
    args = parser.parse_args()

    LOG = args.verbose

    if not args.first:
        log("no first name specified, prompting on stdin")
        args.first = input("first name: ")
        assert NAME_PTRN.search(args.first), \
            "names can only contain characters in [a-zA-Z'\\-]"
        args.first = args.first.lower()

    if not args.last:
        log("no last name specified, prompting on stdin")
        args.last = input("last name: ")
        assert NAME_PTRN.search(args.last), \
            "names can only contain characters in [a-zA-Z'\\-]"
        args.last = args.last.lower()

    if not args.hw:
        log("no hw number specified, prompting on stdin")
        args.hw = int(input("hw number: "), 0)

    if not args.solutions:
        log("no solutions pdf specified, prompting on stdin")
        args.solutions = Path(input("solutions pdf file path: "))
        assert args.solutions.exists(), "solutions file not found"
        assert args.solutions.suffix == ".pdf", \
            "solutions file does not have pdf extension. is it a pdf?"

    if not args.src:
        log("no source code directory specified, prompting on stdin")
        args.src = Path(input("src directory path: "))
        assert args.src.is_dir(), "src directory not found or not a directory"

    with tempfile.TemporaryDirectory() as td:
        log(f"creating temporary directory @ {td}")
        tmpdir = Path(td)
        hwdir = tmpdir / f"{args.last}_{args.first}.hw{str(args.hw)}"
        log(f"creating hw directory @ {str(hwdir)}")
        hwdir.mkdir(parents=True)
        log(f"copying solutions pdf...")
        shutil.copy(args.solutions, hwdir / "solutions.pdf")
        log(f"copying source code directory...")
        shutil.copytree(args.src, hwdir / "src")
        log(f"creating zipfile...")
        target = args.out / f"{hwdir.name}.zip"
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(str(tmpdir)):
                for file in files:
                    if file in SKIP_FILES: continue
                    abs_path = os.path.join(root, file)
                    rel_path = os.path.relpath(abs_path, str(tmpdir))
                    zf.write(abs_path, rel_path)
        log(f"zipfile created @ {str(target)}.")
        log("deleting temporary directory...")
    log("done.")