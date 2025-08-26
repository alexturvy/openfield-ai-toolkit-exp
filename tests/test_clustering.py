import sys
import types
import importlib

# Create stub modules before importing target
sklearn = types.ModuleType('sklearn')
preprocessing = types.ModuleType('sklearn.preprocessing')
preprocessing.normalize = lambda x: x
metrics = types.ModuleType('sklearn.metrics')
metrics.silhouette_score = lambda embeddings, labels: 0.5
sklearn.preprocessing = preprocessing
sklearn.metrics = metrics
sys.modules['sklearn'] = sklearn
sys.modules['sklearn.preprocessing'] = preprocessing
sys.modules['sklearn.metrics'] = metrics

umap_mod = types.ModuleType('umap')
class DummyUMAP:
    def __init__(self, *args, **kwargs):
        pass
    def fit_transform(self, embeddings):
        return embeddings
umap_mod.UMAP = DummyUMAP
sys.modules['umap'] = umap_mod

hdbscan_mod = types.ModuleType('hdbscan')
class DummyHDBSCAN:
    def __init__(self, *args, **kwargs):
        pass
    def fit_predict(self, embeddings):
        half = len(embeddings) // 2
        return [0 if i < half else 1 for i in range(len(embeddings))]

hdbscan_mod.HDBSCAN = DummyHDBSCAN
sys.modules['hdbscan'] = hdbscan_mod

from src.insight_synthesizer.analysis import clustering
importlib.reload(clustering)

class DummyChunk:
    def __init__(self, emb):
        self.embedding = emb
        self.cluster_id = None


def test_perform_clustering_stubs():
    chunks = [DummyChunk([0, 0]), DummyChunk([0.1, 0]), DummyChunk([5, 5]), DummyChunk([5.1, 5.1])]
    updated, clusters = clustering.perform_clustering(chunks)
    assert len(clusters) == 2
    assert all(c.cluster_id in [0, 1] for c in clusters)
