import importlib
import pkgutil
from pathlib import Path
import sys

def import_models():
    """
    Dynamically imports all modules named 'models.py' within the 'src/modules' directory.
    This ensures that SQLAlchemy's MetaData registers all models for Alembic.
    """
    # Add project root and src to path if not already there to support absolute imports correctly
    root_path = str(Path(__file__).parent.parent.parent.resolve())
    src_path = str((Path(__file__).parent.parent.parent / "src").resolve())
    
    if root_path not in sys.path:
        sys.path.append(root_path)
    if src_path not in sys.path:
        sys.path.append(src_path)

    base_path = Path(root_path) / "src" / "modules"
    
    if not base_path.exists():
        print(f"[!] Warning: Base modules path {base_path} not found.")
        return

    print(f"[*] Discovering models in {base_path}...")
    
    # Recursively find all 'models.py' files
    for path in base_path.rglob("models.py"):
        # Convert path to module notation (e.g., src.modules.users.models)
        # We want to start from 'modules' if 'src' is in sys.path
        try:
            relative_path = path.relative_to(base_path.parent.parent) # root/src/modules/...
            module_name = str(relative_path.with_suffix("")).replace("\\", ".").replace("/", ".")
            
            print(f"[*] Importing model module: {module_name}")
            importlib.import_module(module_name)
        except Exception as e:
            import traceback
            print(f"[!] Error importing {module_name} (from {path}): {e}")
            traceback.print_exc()

if __name__ == "__main__":
    import_models()
