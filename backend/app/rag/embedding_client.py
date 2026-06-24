from app.core import config

_model = None


def get_bi_encoder():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(config.RAG_BI_ENCODER_MODEL)
    return _model


def encode_texts(texts: list[str]) -> list[list[float]]:
    vectors = get_bi_encoder().encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]
