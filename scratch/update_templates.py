import os

templates_dir = (
    r"c:\Users\elies\OneDrive\Documents\Projects\new-finance-app\src\app\templates"
)

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = content.replace('.js"', '.js"')
            new_content = new_content.replace(".js'", ".js'")

            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated {path}")
