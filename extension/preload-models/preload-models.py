# ---------------------------------------------------------------------------
# SQLAlchemy Model Registry Pre-Loader
# Since all cross-model imports use TYPE_CHECKING (never run at runtime),
# we must explicitly import every model module so each class gets registered
# in SQLAlchemy's DeclarativeBase registry. This allows string-based
# relationship references like relationship("BusinessEntity") to resolve.
# ---------------------------------------------------------------------------
import importlib
from pathlib import Path


def _preload_sqlalchemy_models():
    """Import all models.py files so their classes register with SQLAlchemy."""
    base_dir = Path("src/modules")
    if not base_dir.exists():
        return
    for model_file in sorted(base_dir.rglob("models.py")):
        module_path = (
            str(model_file.with_suffix("")).replace("\\", ".").replace("/", ".")
        )
        try:
            importlib.import_module(module_path)
        except Exception as e:
            print(f"[model_preloader] Warning: failed to load {module_path}: {e}")


_preload_sqlalchemy_models()
