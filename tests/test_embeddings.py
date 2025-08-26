from pathlib import Path
from src.insight_synthesizer.analysis import embeddings


def test_generate_embeddings_monkeypatch(monkeypatch):
    class DummyModel:
        def encode(self, text):
            return [1.0, 0.0, 0.0]

    monkeypatch.setattr(embeddings, 'SentenceTransformer', lambda *_args, **_kwargs: DummyModel())
    chunks = [embeddings.TextChunk('hello', Path('f.txt'))]
    result = embeddings.generate_embeddings(chunks)
    assert result[0].embedding == [1.0, 0.0, 0.0]
