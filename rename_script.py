import os
import re
import shutil

base_dir = r"c:\Users\shree\project\Cure-Quest"

def rename_dirs_and_files():
    # Rename src/cure_quest -> src/nexus_ai
    src_dir = os.path.join(base_dir, "src", "cure_quest")
    dest_dir = os.path.join(base_dir, "src", "nexus_ai")
    if os.path.exists(src_dir) and not os.path.exists(dest_dir):
        os.rename(src_dir, dest_dir)
        print(f"Renamed {src_dir} to {dest_dir}")

    # Rename curequest.sql
    sql_src = os.path.join(base_dir, "curequest.sql")
    sql_dest = os.path.join(base_dir, "nexus_ai.sql")
    if os.path.exists(sql_src):
        os.rename(sql_src, sql_dest)
        print("Renamed curequest.sql to nexus_ai.sql")
        
    # Rename dump
    dump_src = os.path.join(base_dir, "curequest_backup.dump")
    dump_dest = os.path.join(base_dir, "nexus_ai_backup.dump")
    if os.path.exists(dump_src):
        os.rename(dump_src, dump_dest)
        print("Renamed curequest_backup.dump to nexus_ai_backup.dump")

def replace_in_files():
    excludes = ['node_modules', '.git', '.venv', 'dist', 'build', '__pycache__', 'cure_quest.egg-info']
    extensions = {'.py', '.tsx', '.ts', '.js', '.jsx', '.json', '.md', '.html', '.css', '.toml', '.yaml', '.yml', '.sql', '.example'}
    
    replacements = [
        # Python package name and imports
        (r'cure_quest', r'nexus_ai'),
        # Project names in config
        (r'curequest', r'nexus_ai'),
        # Branding in text / frontend
        (r'CureQuest Agent', r'Nexus_ai Agent'),
        (r'CureQuest', r'Nexus_ai {an medical agent garden}'),
        (r'Cure-Quest', r'nexus_ai'),
        (r'Cure Quest', r'Nexus_ai'),
    ]
    
    compiled_replacements = [(re.compile(p), r) for p, r in replacements]

    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d not in excludes]
        for file in files:
            # Skip this script
            if file == "rename_script.py":
                continue
            
            ext = os.path.splitext(file)[1]
            if ext in extensions or file in ['Dockerfile', 'frontend.Dockerfile', '.env', '.env.example', 'cloudrun.env.example']:
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content
                    for pattern, repl in compiled_replacements:
                        new_content = pattern.sub(repl, new_content)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated {path}")
                except Exception as e:
                    print(f"Could not process {path}: {e}")

if __name__ == "__main__":
    rename_dirs_and_files()
    replace_in_files()
    print("Rebranding complete.")
