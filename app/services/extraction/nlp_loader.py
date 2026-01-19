import spacy
import logging

logger = logging.getLogger(__name__)

_nlp_instance = None

def load_ginza():
    """
    GiNZA (spaCy) モデルをロードし、シングルトンとして返します。
    """
    global _nlp_instance
    if _nlp_instance is None:
        try:
            # 高精度版 (ja_ginza_electra) があれば優先、なければ標準 (ja_ginza)
            try:
                logger.info("Loading GiNZA (ja_ginza_electra)...")
                _nlp_instance = spacy.load("ja_ginza_electra")
            except OSError:
                logger.info("ja_ginza_electra not found. Loading ja_ginza...")
                _nlp_instance = spacy.load("ja_ginza")
            logger.info("GiNZA loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load GiNZA: {e}. Please install with `pip install ja_ginza`.")
            _nlp_instance = None
    return _nlp_instance