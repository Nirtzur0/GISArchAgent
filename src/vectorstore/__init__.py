"""Vector store package for document storage and retrieval.

Keep package import lightweight.

Some optional vector-store helpers depend on LangChain/OpenAI/LangSmith. Those
dependencies can be absent or incompatible in environments that still want to
use the core Chroma repository + sample data. Import those heavy modules only
on demand.
"""

from __future__ import annotations

from src.vectorstore.initializer import VectorDBInitializer
from src.vectorstore.data_sources import get_sample_regulations, add_custom_regulations

__all__ = ["VectorDBInitializer", "get_sample_regulations", "add_custom_regulations"]


def __getattr__(name: str):
    # Lazy imports for optional LangChain-based manager.
    if name in {"VectorStoreManager", "MultiCollectionManager"}:
        from src.vectorstore.manager import VectorStoreManager, MultiCollectionManager

        globals()["VectorStoreManager"] = VectorStoreManager
        globals()["MultiCollectionManager"] = MultiCollectionManager
        __all__.extend(["VectorStoreManager", "MultiCollectionManager"])
        return globals()[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
