import os
import hashlib

def run_inventory(repo_name, repo_dir, manifests_dir):
    print(f"Inventorying {repo_name} at {repo_dir}...")
    
    # 1. Tree (max depth 3 relative paths)
    tree_lines = []
    for root, dirs, files in os.walk(repo_dir):
        rel_root = os.path.relpath(root, repo_dir)
        depth = 0 if rel_root == "." else len(rel_root.split(os.sep))
        if depth > 3:
            continue
        if ".git" in root.split(os.sep):
            continue
        for f in sorted(files):
            rel_file = os.path.join(rel_root, f).replace("\\", "/")
            if rel_file.startswith("./"):
                rel_file = rel_file[2:]
            tree_lines.append(f"./{rel_file}\n")
    tree_lines.sort()
    with open(os.path.join(manifests_dir, f"{repo_name}_tree.txt"), "w", encoding="utf-8") as f:
        f.writelines(tree_lines)
        
    # 2. Artifact hashes (.joblib, .json, .yaml, .yml, .lock)
    hash_extensions = {".joblib", ".json", ".yaml", ".yml", ".lock"}
    artifact_lines = []
    total_bytes = 0
    total_files = 0
    
    for root, dirs, files in os.walk(repo_dir):
        if ".git" in root.split(os.sep):
            continue
        for f in sorted(files):
            file_path = os.path.join(root, f)
            try:
                sz = os.path.getsize(file_path)
                total_bytes += sz
                total_files += 1
            except OSError:
                pass
                
            _, ext = os.path.splitext(f)
            if ext.lower() in hash_extensions:
                rel_file = os.path.relpath(file_path, repo_dir).replace("\\", "/")
                try:
                    hasher = hashlib.sha256()
                    with open(file_path, "rb") as fp:
                        while chunk := fp.read(65536):
                            hasher.update(chunk)
                    artifact_lines.append(f"{hasher.hexdigest()}  {rel_file}\n")
                except Exception as e:
                    artifact_lines.append(f"# ERROR {rel_file}: {e}\n")
                    
    artifact_lines.sort()
    with open(os.path.join(manifests_dir, f"{repo_name}_artifact_hashes.sha256"), "w", encoding="utf-8") as f:
        f.writelines(artifact_lines)
        
    # 3. Size
    mb = total_bytes / (1024 * 1024)
    size_str = f"{total_bytes} bytes ({mb:.2f} MB) across {total_files} files\n"
    with open(os.path.join(manifests_dir, f"{repo_name}_size.txt"), "w", encoding="utf-8") as f:
        f.write(size_str)
        
    print(f"Done {repo_name}: {len(tree_lines)} tree entries, {len(artifact_lines)} artifact hashes, {mb:.2f} MB.")

if __name__ == "__main__":
    run_inventory("repo_a", "repos/repo_a", "manifests")
    run_inventory("repo_b", "repos/repo_b", "manifests")
