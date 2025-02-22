import os

def replace_text_in_file(file_path, old_text, new_text):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_content = content.replace(old_text, new_text)
        if new_content != content:  # Only rewrite if changes are made
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Updated: {file_path}")
    except Exception as e:
        print(f"Skipping {file_path} (Error: {e})")

def rename_files_and_folders(directory, old_text, new_text):
    for root, dirs, files in os.walk(directory, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            replace_text_in_file(file_path, old_text, new_text)

        for name in dirs:
            old_path = os.path.join(root, name)
            if old_text in name:
                new_name = name.replace(old_text, new_text)
                new_path = os.path.join(root, new_name)
                os.rename(old_path, new_path)
                print(f"Renamed folder: {old_path} -> {new_path}")

    # Rename root project folder if needed
    base_name = os.path.basename(directory)
    if old_text in base_name:
        new_base_name = base_name.replace(old_text, new_text)
        new_directory = os.path.join(os.path.dirname(directory), new_base_name)
        os.rename(directory, new_directory)
        print(f"Renamed project folder: {directory} -> {new_directory}")

if __name__ == "__main__":
    project_root = os.getcwd()  # Get current project directory
    old_name = "MindedHealth"
    new_name = "MindedHealth"

    rename_files_and_folders(project_root, old_name, new_name)
    print("✅ Project name update completed!")
