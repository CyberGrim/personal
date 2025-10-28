import os
import shutil
import sys
from markdown_parser import generate_pages_recursive

STATIC_DIR = "./static"
PUBLIC_DIR = "./docs"

BASEPATH = sys.argv[1] if len(sys.argv) > 1 else "/"

def recursive_copy_creation(src_path, dest_path):
    for item in os.listdir(src_path):
        child_src = os.path.join(src_path, item)
        child_dest = os.path.join(dest_path, item)

        if os.path.isdir(child_src):
            print(f"MKDIR {child_dest}")
            os.makedirs(child_dest, exist_ok=True)
            recursive_copy_creation(child_src, child_dest)
        else:
            print(f"COPY {child_src} -> {child_dest}")
            shutil.copy(child_src, child_dest)

def clean_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)

if __name__ == "__main__":
    clean_directory(PUBLIC_DIR)
    os.makedirs(PUBLIC_DIR, exist_ok=True)
    if not os.path.exists(STATIC_DIR):
        raise Exception(f"{STATIC_DIR} doesn't exist. Unable to continue")    
    recursive_copy_creation(STATIC_DIR, PUBLIC_DIR)
    generate_pages_recursive(BASEPATH, "./content", "./template.html", "./docs")
