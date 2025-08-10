import os
import sys
import argparse
from pathlib import Path
from collections import defaultdict
import time

# Configuration variables
DEFAULT_DIR = str(Path.home())  # Default home directory
DEFAULT_DEPTH = 3  # Default display depth
DEFAULT_MIN_SIZE = 300 * 1024 * 1024  # 300MB in bytes
REPORT_FILE = 'report.txt'  # Report filename
DEFAULT_TOP_FILES = 10  # Default number of top files
DEFAULT_TOP_DIRS = 10  # Default number of top directories


class ProgressIndicator:
    """Class for displaying progress in console"""

    def __init__(self, silent=False):
        self.silent = silent
        self.spinner = ['-', '\\', '|', '/']
        self.spinner_pos = 0

    def spin(self):
        if self.silent:
            return
        self.spinner_pos = (self.spinner_pos + 1) % 4
        sys.stdout.write(f"\rAnalyzing {self.spinner[self.spinner_pos]}")
        sys.stdout.flush()

    def clear(self):
        if not self.silent:
            sys.stdout.write("\r")
            sys.stdout.flush()


def get_size(start_path='.'):
    """Recursively calculates directory size, subdirectories and files count"""
    total_size = 0
    dir_count = 0
    file_count = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        dir_count += len(dirnames)
        file_count += len(filenames)
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total_size += os.path.getsize(fp)
            except (OSError, PermissionError):
                continue
    return total_size, dir_count, file_count


def format_size(size):
    """Formats size to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def find_large_items(path, min_size=0, top_files=10, top_dirs=10, progress=None):
    """Finds largest files and directories"""
    large_files = []
    large_dirs = []

    for dirpath, dirnames, filenames in os.walk(path):
        if progress:
            progress.spin()

        # Checking files
        for filename in filenames:
            filepath = os.path.join(dirpath, filename)
            try:
                size = os.path.getsize(filepath)
                if size >= min_size:
                    large_files.append((filepath, size))
            except (OSError, PermissionError):
                continue

        # Checking directories
        try:
            dir_size, _, _ = get_size(dirpath)
            large_dirs.append((dirpath, dir_size))
        except (PermissionError, OSError):
            continue

    # Sorting and selecting top
    large_files.sort(key=lambda x: x[1], reverse=True)
    large_dirs.sort(key=lambda x: x[1], reverse=True)

    return large_files[:top_files], large_dirs[:top_dirs]


def analyze_directory(path, max_depth=3, current_depth=0, min_size=DEFAULT_MIN_SIZE):
    """Recursively analyzes directory and returns structure"""
    if current_depth > max_depth:
        return None

    try:
        total_size, dir_count, file_count = get_size(path)
    except (PermissionError, OSError):
        return None

    name = os.path.basename(path) if current_depth > 0 else path
    result = {
        'name': name,
        'size': total_size,
        'dir_count': dir_count,
        'file_count': file_count,
        'is_file': False,
        'children': []  # Always initialize empty list children
    }

    if current_depth < max_depth:
        try:
            entries = os.listdir(path)
        except (PermissionError, OSError):
            entries = []

        dirs = []
        files = []
        for entry in entries:
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                dirs.append((entry, full_path))
            else:
                try:
                    size = os.path.getsize(full_path)
                    if size >= min_size:
                        ext = os.path.splitext(entry)[1][1:].lower()
                        files.append((entry, size, ext))
                except (OSError, PermissionError):
                    continue

        # Sort directories by size (descending)
        dirs_sizes = []
        for name, full_path in dirs:
            try:
                size, _, _ = get_size(full_path)
                dirs_sizes.append((name, full_path, size))
            except (PermissionError, OSError):
                continue

        dirs_sizes.sort(key=lambda x: x[2], reverse=True)

        # Adding only first 5 largest directories
        for name, full_path, size in dirs_sizes[:5]:
            child = analyze_directory(full_path, max_depth, current_depth + 1, min_size)
            if child:
                result['children'].append(child)

        # Sort files by size (descending) and add first 5 largest
        files.sort(key=lambda x: x[1], reverse=True)
        for name, size, ext in files[:5]:
            result['children'].append({
                'name': name,
                'size': size,
                'is_file': True,
                'extension': ext
            })

    return result


def generate_report(structure, large_files, large_dirs, file=None):
    """Generates full report"""
    # Tree structure
    generate_tree_report(structure, file=file)

    # Top files
    print("\n\nTop 10 largest files:", file=file)
    for i, (path, size) in enumerate(large_files, 1):
        print(f"{i}. {path} - {format_size(size)}", file=file)

    # Top directories
    print("\nTop 10 largest directories:", file=file)
    for i, (path, size) in enumerate(large_dirs, 1):
        print(f"{i}. {path} - {format_size(size)}", file=file)


def generate_tree_report(structure, level=0, is_last=False, parent_prefix="", file=None):
    """Generates tree part of report with correct branching symbols"""
    if structure is None:
        return

    children = structure.get('children', [])

    # Determine prefix for current element
    if level == 0:
        # Root directory
        prefix = ""
        connector = ""
    else:
        prefix = parent_prefix
        connector = "└── " if is_last else "├── "

    # Forming string for current element
    if structure.get('is_file', False):
        ext = structure.get('extension', 'file')
        line = f"{prefix}{connector}{structure['name']}\t# {format_size(structure['size'])} - {ext} file"
    else:
        line = f"{prefix}{connector}{structure['name']}/\t# {format_size(structure['size'])}, {structure['dir_count']} dir, {structure['file_count']} files"

    print(line, file=file)

    # Determine prefix for children
    if level > 0:
        if is_last:
            child_prefix = parent_prefix + "    "
        else:
            child_prefix = parent_prefix + "│   "
    else:
        child_prefix = ""

    # Recursively process children
    for i, child in enumerate(children):
        is_last_child = (i == len(children) - 1)
        generate_tree_report(child, level + 1, is_last_child, child_prefix, file)

def parse_size(size_str):
    """Parses size string (e.g. '300M', '1G') to bytes"""
    size_str = size_str.upper()
    if 'K' in size_str:
        return int(float(size_str.replace('K', '')) * 1024)
    elif 'M' in size_str:
        return int(float(size_str.replace('M', '')) * 1024 * 1024)
    elif 'G' in size_str:
        return int(float(size_str.replace('G', '')) * 1024 * 1024 * 1024)
    elif 'T' in size_str:
        return int(float(size_str.replace('T', '')) * 1024 * 1024 * 1024 * 1024)
    else:
        return int(size_str)  # Default bytes


def print_large_items(large_files, large_dirs, top_files, top_dirs):
    """Outputs top files and directories to console"""
    print("\nTop largest files:")
    for i, (path, size) in enumerate(large_files[:top_files], 1):
        print(f"{i}. {path} - {format_size(size)}")

    print("\nTop largest directories:")
    for i, (path, size) in enumerate(large_dirs[:top_dirs], 1):
        print(f"{i}. {path} - {format_size(size)}")


def main():
    parser = argparse.ArgumentParser(description='Analyzes directory sizes and creates report')
    parser.add_argument('directory', nargs='?', default=DEFAULT_DIR,
                        help=f'Directory to analyze (default: {DEFAULT_DIR})')
    parser.add_argument('--depth', type=int, default=DEFAULT_DEPTH,
                        help=f'Tree display depth (default: {DEFAULT_DEPTH})')
    parser.add_argument('-m', '--min-size', type=str, default='300M',
                        help='Minimum file size to display (e.g. 300M, 1G) (default: 300M)')
    parser.add_argument('-f', '--files', type=int, default=DEFAULT_TOP_FILES,
                        help=f'Number of top files to display (default: {DEFAULT_TOP_FILES})')
    parser.add_argument('--dirs', type=int, default=DEFAULT_TOP_DIRS,
                        help=f'Number of top directories to display (default: {DEFAULT_TOP_DIRS})')
    parser.add_argument('-s', '--silent', action='store_true',
                        help='Silent mode (do not output progress and results to console)')

    args = parser.parse_args()

    target_dir = args.directory
    depth = args.depth
    silent = args.silent
    top_files = args.files
    top_dirs = args.dirs

    # Parsing minimum size
    try:
        min_size = parse_size(args.min_size)
    except ValueError:
        print("Error: invalid minimum size format. Use for example '300M' or '1G'", file=sys.stderr)
        sys.exit(1)

    if not os.path.isdir(target_dir):
        print(f"Error: '{target_dir}' is not a directory or doesn't exist", file=sys.stderr)
        sys.exit(1)

    progress = ProgressIndicator(silent)

    if not silent:
        print(f"Analyzing directory: {target_dir}")
        print(f"Analysis depth: {depth}, min file size: {format_size(min_size)}")
        print(f"Number of top files: {top_files}, top directories: {top_dirs}")

    # Finding largest files and directories
    large_files, large_dirs = find_large_items(target_dir, min_size, top_files, top_dirs, progress)
    progress.clear()

    # Analyzing directory structure
    structure = analyze_directory(target_dir, depth, min_size=min_size)

    # Generating report
    report_path = os.path.join(os.getcwd(), REPORT_FILE)
    with open(report_path, 'w', encoding='utf-8') as f:
        generate_report(structure, large_files, large_dirs, file=f)

    if not silent:
        # Outputting top files and directories to console
        print_large_items(large_files, large_dirs, top_files, top_dirs)
        print(f"\nReport saved to: {report_path}")


if __name__ == '__main__':
    main()