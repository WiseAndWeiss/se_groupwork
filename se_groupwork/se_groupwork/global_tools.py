import sys
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

G_EMBEDDING = None
G_SQLVECTOOL = None
G_MEILITOOL = None
G_FAISSTOOL = None

def is_test_mode():
    if "test" in sys.argv:
        return True
    if getattr(settings, "TEST_MODE", False):
        return True
    return False

def global_embedding_load():
    global G_EMBEDDING
    if G_EMBEDDING is not None:
        return G_EMBEDDING
    G_EMBEDDING = HuggingFaceEmbeddings(
        model_name=settings.EMBEDDING_MODEL_PATH,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True}
    )
    return G_EMBEDDING


def global_sqlvec_tool_load():
    from askAI.sqlvec.sqlvec_tool import SqliteVectorTool
    global G_SQLVECTOOL
    if G_SQLVECTOOL is not None:
        return G_SQLVECTOOL
    G_SQLVECTOOL = SqliteVectorTool(test_mode=is_test_mode())
    return G_SQLVECTOOL


def global_faiss_tool_load():
    """Backward-compatible alias; FAISS replaced by sqlite-vec."""
    global G_FAISSTOOL
    if G_FAISSTOOL is not None:
        return G_FAISSTOOL
    G_FAISSTOOL = global_sqlvec_tool_load()
    return G_FAISSTOOL

def global_meili_tool_load():
    from article_selector.meilisearch.meili_tools import MeilisearchTool
    global G_MEILITOOL
    if G_MEILITOOL is not None:
        return G_MEILITOOL
    G_MEILITOOL = MeilisearchTool(test_mode=is_test_mode())
    return G_MEILITOOL