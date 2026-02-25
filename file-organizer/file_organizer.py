from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Dict, Set, Tuple


# Map extensions to folder names (customize freely)
CATEGORIES: Dict[str, Set[str]] = {
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"},
    "Videos": {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"},
    "Documents": {".pdf", ".txt", ".doc", ".docx", ".rtf", ".odt"},
    "Spreadsheets": {".xls", ".xlsx", ".csv", ".ods"},
    "Presentations": {".ppt", ".pptx", ".odp"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Code": {".py", ".js", ".ts", ".html", ".css", ".json", ".yaml", ".yml", ".md"},
    "Executables": {".exe", ".msi"},
}

DEFAULT_CATEGORY = "Other"


def pick_category(ext: str) -> str:
    ext = ext.lower()
    for category, exts in CATEGORIES.items():
        if ext in exts:
            return category
    return DEFAULT_CATEGORY


def unique_destination_path(dest_path: Path) -> Path:
    """
    If destination exists, append ' (1)', ' (2)', ... before suffix.
    Example: file.txt -> file (1).txt
    """
    if not dest_path.exists():
        return dest_path

    stem = dest_path.stem
    suffix = dest_path.suffix
    parent = dest_path.parent

    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1


def iter_files(folder: Path, recursive: bool) -> list[Path]:
    if recursive:
        return [p for p in folder.rglob("*") if p.is_file()]
    return [p for p in folder.iterdir() if p.is_file()]


def organize_folder(
    folder: Path,
    live: bool = False,
    recursive: bool = False,
    verbose: bool = True,
) -> int:
    """
    Organize files in 'folder' into category subfolders.
    Returns the number of files that would be (or were) moved.
    """
    if not folder.exists() or not folder.is_dir():
        raise ValueError(f"Not a valid folder: {folder}")

    files = iter_files(folder, recursive=recursive)

    moves: list[Tuple[Path, Path]] = []

    for src in files:
        # Don't reorganize files already inside category folders if recursive
        # (prevents endless shuffling)
        if recursive and src.parent != folder:
            # If it's already under a category dir inside the target, skip it
            # e.g. target/Images/pic.jpg shouldn't be moved again.
            try:
                rel = src.relative_to(folder)
                if len(rel.parts) >= 2 and rel.parts[0] in set(CATEGORIES.keys()) | {DEFAULT_CATEGORY}:
                    continue
            except ValueError:
                pass

        category = pick_category(src.suffix)
        dest_dir = folder / category
        dest_dir.mkdir(exist_ok=True)

        dest_path = unique_destination_path(dest_dir / src.name)
        moves.append((src, dest_path))

    print(f"\nScanning: {folder}")
    print(f"Mode: {'LIVE (moving files)' if live else 'DRY RUN (no changes)'}")
    print(f"Recursive: {recursive}")
    print(f"Files found: {len(files)}")
    print(f"Moves planned: {len(moves)}\n")

    if verbose:
        for src, dst in moves:
            # Display as Category/filename
            print(f"{src.name} -> {dst.parent.name}/{dst.name}")

        print("")

    if live:
        for src, dst in moves:
            shutil.move(str(src), str(dst))
        print("Done. Files moved.\n")
    else:
        print("Dry run complete. No files moved.\n")

    return len(moves)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="file_organizer",
        description="Organize files into folders by type (safe dry-run by default).",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        help="Target folder to organize (WSL paths like /mnt/c/Users/NAME/Downloads).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Actually move files (default is dry-run).",
    )
    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Also organize files in subfolders (skips category folders it creates).",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less output (don’t print every file move).",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # If no path is provided, pick a sensible default (Downloads)
    if args.path is None:
        # Try common WSL user path patterns; user can always pass explicit path.
        default = Path("/mnt/c/Users")  # just to build a helpful message
        print(
            "No path provided.\n"
            "Example:\n"
            "  python3 file_organizer.py /mnt/c/Users/ratphour/Downloads/organizer_test\n"
            "Or live mode:\n"
            "  python3 file_organizer.py /mnt/c/Users/ratphour/Downloads/organizer_test --live\n"
        )
        parser.exit(2)

    target = Path(args.path).expanduser()
    organize_folder(
        target,
        live=bool(args.live),
        recursive=bool(args.recursive),
        verbose=not bool(args.quiet),
    )


if __name__ == "__main__":
    main()
