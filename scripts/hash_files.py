import hashlib
import os
import sys

def hash_dir(target_dir, output_file):
    lines = []
    for root, dirs, files in os.walk(target_dir):
        dirs.sort()
        for f in sorted(files):
            file_path = os.path.join(root, f)
            rel_path = os.path.relpath(file_path).replace("\\", "/")
            try:
                hasher = hashlib.sha256()
                with open(file_path, "rb") as fp:
                    while chunk := fp.read(65536):
                        hasher.update(chunk)
                digest = hasher.hexdigest()
                lines.append(f"{digest}  {rel_path}\n")
            except Exception as e:
                lines.append(f"# ERROR reading {rel_path}: {e}\n")
    lines.sort()
    with open(output_file, "w", encoding="utf-8") as out:
        out.writelines(lines)
    print(f"Hashed {len(lines)} files from '{target_dir}' into '{output_file}'.")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "docs"
    dest = sys.argv[2] if len(sys.argv) > 2 else "manifests/supplied_docs.sha256"
    hash_dir(target, dest)
