import os

# --- CONFIGURATION ---
# 1. Extensions to include (Add or remove as needed)
ALLOWED_EXTENSIONS = {
    '.py', '.js', '.jsx', '.ts', '.tsx', 
    '.html', '.css', '.java', '.c', '.cpp', 
    '.h', '.cs', '.php', '.rb', '.go', 
    '.rs', '.swift', '.kt', '.sql', '.json', 
    '.xml', '.yaml', '.yml', '.md'
}

# 2. Folders to ignore (Standard junk folders)
IGNORE_FOLDERS = {
    '__pycache__', 'node_modules', '.git', 
    '.idea', '.vscode', 'venv', 'env', 
    'bin', 'obj', 'build', 'dist'
}

# 3. Output filename
OUTPUT_FILE = "full_code_review.txt"

def is_text_file(filename):
    """Checks if the file extension is in the allowed list."""
    return any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS)

def main():
    root_dir = os.getcwd()  # Gets the current folder where script is running
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        # Walk through all directories and files
        for dirpath, dirnames, filenames in os.walk(root_dir):
            
            # Modify dirnames in-place to skip ignored folders
            dirnames[:] = [d for d in dirnames if d not in IGNORE_FOLDERS]
            
            for filename in filenames:
                # Skip the output file itself to avoid infinite loops
                if filename == OUTPUT_FILE or filename == "prepare_review.py":
                    continue
                
                if is_text_file(filename):
                    filepath = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(filepath, root_dir)
                    
                    try:
                        with open(filepath, "r", encoding="utf-8", errors="ignore") as infile:
                            content = infile.read()
                            
                            # --- FORMATTING FOR THE REVIEW FILE ---
                            outfile.write("=" * 80 + "\n")
                            outfile.write(f"FILE: {relative_path}\n")
                            outfile.write("=" * 80 + "\n")
                            outfile.write(content + "\n\n")
                            
                            print(f"Added: {relative_path}")
                            
                    except Exception as e:
                        print(f"Skipped {relative_path} due to error: {e}")

    print(f"\n✅ Success! All main files have been copied to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()