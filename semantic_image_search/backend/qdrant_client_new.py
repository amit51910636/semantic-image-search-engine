from qdrant_client import QdrantClient
from qdrant_client.http import models
from semantic_image_search.backend.config import Config
from semantic_image_search.backend.logger import GLOBAL_LOGGER as log
from semantic_image_search.backend.exception.custom_exception import SemanticImageSearchException


class QdrantClientManager:
    """
    Qdrant Client Manager (Singleton)
    """

    _client = None

    @classmethod
    def get_client(cls) -> QdrantClient:
        """Lazy initialize the Qdrant client"""
        if cls._client is None:

            if not Config.QDRANT_URL:
                log.warning("QDRANT_URL missing in environment")

            if not Config.QDRANT_API_KEY:
                log.warning("QDRANT_API_KEY missing in environment")

            log.info(
                "Initializing Qdrant client",
                url=Config.QDRANT_URL,
                using_api_key=bool(Config.QDRANT_API_KEY)
            )

            try:
                cls._client = QdrantClient(
                    url=Config.QDRANT_URL,
                    api_key=Config.QDRANT_API_KEY,
                )
                log.info("Qdrant client initialized successfully")

            except Exception as e:
                log.error("Failed to initialize Qdrant client", error=str(e))
                raise SemanticImageSearchException("Failed to init Qdrant client", e)

        return cls._client

    @classmethod
    def ensure_collection(cls):
        """Ensure Qdrant collection exists"""

        try:
            client = cls.get_client()

            log.info("Fetching existing Qdrant collections...")

            all_collections = client.get_collections().collections
            existing = {c.name for c in all_collections}

            if Config.QDRANT_COLLECTION not in existing:


# old code - amit - commented
                # log.info(
                #     "Creating new Qdrant collection",
                #     collection=Config.QDRANT_COLLECTION,
                #     vector_size=Config.VECTOR_SIZE,
                #     distance="COSINE",
                # )

                # client.create_collection(
                #     collection_name=Config.QDRANT_COLLECTION,
                #     vectors={
                #         "default": models.VectorParams(
                #             size=Config.VECTOR_SIZE,
                #             distance=models.Distance.COSINE,
                #             on_disk=True,   # important for large datasets
                #         )
                #     },
                # )


                log.info(
                    "Creating new Qdrant collection",
                    collection=Config.QDRANT_COLLECTION,
                    vector_size=Config.VECTOR_SIZE,
                    distance="COSINE",
                )

                # Try new -> intermediate -> legacy create_collection signatures
                creation_error = None

                # 1) New-style: vectors_config (some recent qdrant-client versions)
                try:
                    client.create_collection(
                        collection_name=Config.QDRANT_COLLECTION,
                        vectors_config={
                            "default": {
                                "size": Config.VECTOR_SIZE,
                                "distance": models.Distance.COSINE,
                                # on_disk param may not exist in some APIs; if yours needs it, add it below
                                # "on_disk": True
                            }
                        },
                    )
                    log.info("Qdrant collection created (vectors_config)", collection=Config.QDRANT_COLLECTION)
                    creation_error = None
                except Exception as e_new:
                    creation_error = e_new
                    # Only continue to fallback if it's likely an argument/signature mismatch
                    msg = str(e_new).lower()
                    if ("unknown arguments" not in msg) and ("vectors" not in msg and "vectors_config" not in msg):
                        log.error("create_collection (vectors_config) failed with unexpected error", error=str(e_new))
                        raise

                # 2) Intermediate-style: vectors kwarg (what your code originally used)
                if creation_error is not None:
                    try:
                        client.create_collection(
                            collection_name=Config.QDRANT_COLLECTION,
                            vectors={
                                "default": models.VectorParams(
                                    size=Config.VECTOR_SIZE,
                                    distance=models.Distance.COSINE,
                                    on_disk=True,
                                )
                            },
                        )
                        log.info("Qdrant collection created (vectors)", collection=Config.QDRANT_COLLECTION)
                        creation_error = None
                    except Exception as e_mid:
                        creation_error = e_mid
                        msg = str(e_mid).lower()
                        if ("unknown arguments" not in msg) and ("vectors" not in msg):
                            log.error("create_collection (vectors) failed with unexpected error", error=str(e_mid))
                            raise

                # 3) Legacy-style: vector_size + distance
                if creation_error is not None:
                    try:
                        client.create_collection(
                            collection_name=Config.QDRANT_COLLECTION,
                            vector_size=Config.VECTOR_SIZE,
                            distance="Cosine",  # older API sometimes expects string form
                        )
                        log.info("Qdrant collection created (vector_size + distance)", collection=Config.QDRANT_COLLECTION)
                        creation_error = None
                    except Exception as e_legacy:
                        log.error("All create_collection attempts failed", error=str(e_legacy))
                        raise SemanticImageSearchException("Failed to ensure Qdrant collection", e_legacy)



                log.info("Qdrant collection created", collection=Config.QDRANT_COLLECTION)

            else:
                log.info(
                    "Using existing Qdrant collection",
                    collection=Config.QDRANT_COLLECTION,
                )




        except Exception as e:
            log.error("Failed to ensure Qdrant collection", error=str(e))
            raise SemanticImageSearchException("Failed to ensure Qdrant collection", e)


if __name__ == "__main__":
    client = QdrantClientManager.get_client()
    QdrantClientManager.ensure_collection()
