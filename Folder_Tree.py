import os

EXCLUDED_KEYWORDS = ['venv', '__pycache__']  # Case-insensitive

def should_exclude_folder(folder_name):
    lower_name = folder_name.lower()
    return any(kw in lower_name for kw in EXCLUDED_KEYWORDS)

def print_tree(start_path=".", max_depth=3, current_depth=0, prefix="", file_limit=20, folder_limit=10):
    if current_depth > max_depth:
        return

    try:
        entries = sorted(os.listdir(start_path))
    except (PermissionError, FileNotFoundError):
        return

    dirs = [e for e in entries if os.path.isdir(os.path.join(start_path, e))]
    files = [e for e in entries if os.path.isfile(os.path.join(start_path, e)) and not e.startswith('.')]

    shown_dirs = dirs[:folder_limit]
    for entry in shown_dirs:
        full_path = os.path.join(start_path, entry)
        print(f"{prefix}📁 {entry}/")

        if entry.startswith('.') or should_exclude_folder(entry):
            continue  # Skip recursion

        print_tree(full_path, max_depth, current_depth + 1, prefix + "    ", file_limit, folder_limit)

    if len(dirs) > folder_limit:
        print(f"{prefix}... ({len(dirs) - folder_limit} more folders hidden)")

    shown_files = files[:file_limit]
    for entry in shown_files:
        print(f"{prefix}📄 {entry}")

    if len(files) > file_limit:
        print(f"{prefix}... ({len(files) - file_limit} more files hidden)")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    print(f"📂 Folder Tree for: {base_dir}")
    print_tree(".", max_depth=3, file_limit=20, folder_limit=10)
