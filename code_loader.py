# code_loader.py
import git
import os
import shutil

def clone_repository(repo_url, local_path):
    """Clones a Git repository to a local path."""
    if os.path.exists(local_path):
        # If the directory exists, remove it to ensure a fresh clone
        shutil.rmtree(local_path)
    print(f"Cloning repository: {repo_url}...")
    git.Repo.clone_from(repo_url, local_path)
    print("Cloning complete.")

def get_code_files(repo_path, extensions=['.py', '.js', '.ts', '.java', '.cs', '.html', '.css', '.md']):
    """Walks through the repo and returns a list of code file paths."""
    code_files = []
    for root, _, files in os.walk(repo_path):
        # Exclude .git directory and other common non-code directories
        if '.git' in root or 'node_modules' in root or '__pycache__' in root:
            continue
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                code_files.append(os.path.join(root, file))
    return code_files

if __name__ == '__main__':
    # Example usage
    repo_url = 'https://github.com/langchain-ai/langchain' # A large, interesting repo
    local_repo_path = 'temp_repo'
    
    clone_repository(repo_url, local_repo_path)
    files = get_code_files(local_repo_path)
    
    print(f"Found {len(files)} code files.")
    # Print first 5 files as a sample
    for f in files[:5]:
        print(f)