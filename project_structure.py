import pathlib

def print_project_tree(start_path=".", indent="", last=True, ignore_dirs=[".git", "__pycache__", "venv"]):
    path = pathlib.Path(start_path)
    if path.name in ignore_dirs:
        return
        
    if path.is_dir():
        print(f"{indent}{'└── ' if last else '├── '}{path.name}/")
        indent += "    " if last else "│   "
        children = sorted(path.iterdir())
        for i, child in enumerate(children):
            print_project_tree(child, indent, i == len(children)-1, ignore_dirs)
    else:
        print(f"{indent}{'└── ' if last else '├── '}{path.name}")

if __name__ == "__main__":
    print("CURRENT PROJECT STRUCTURE:")
    print_project_tree()
    