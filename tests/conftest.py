import sys
from pathlib import Path
import types

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide lightweight stubs for heavy optional dependencies
if 'umap' not in sys.modules:
    umap_mod = types.ModuleType('umap')
    class DummyUMAP:
        def __init__(self, *args, **kwargs):
            pass
        def fit_transform(self, data):
            return data
    umap_mod.UMAP = DummyUMAP
    sys.modules['umap'] = umap_mod

if 'hdbscan' not in sys.modules:
    hdbscan_mod = types.ModuleType('hdbscan')
    class DummyHDBSCAN:
        def __init__(self, *args, **kwargs):
            pass
        def fit_predict(self, data):
            return [0] * len(data)
    hdbscan_mod.HDBSCAN = DummyHDBSCAN
    sys.modules['hdbscan'] = hdbscan_mod

if 'sklearn' not in sys.modules:
    sklearn = types.ModuleType('sklearn')
    preprocessing = types.ModuleType('sklearn.preprocessing')
    preprocessing.normalize = lambda x: x
    metrics = types.ModuleType('sklearn.metrics')
    metrics.silhouette_score = lambda emb, labels: 0.0
    sklearn.preprocessing = preprocessing
    sklearn.metrics = metrics
    sys.modules['sklearn'] = sklearn
    sys.modules['sklearn.preprocessing'] = preprocessing
    sys.modules['sklearn.metrics'] = metrics
if 'sentence_transformers' not in sys.modules:
    st_mod = types.ModuleType('sentence_transformers')
    class DummyModel:
        def encode(self, text):
            return [0.0]
    st_mod.SentenceTransformer = lambda *args, **kwargs: DummyModel()
    sys.modules['sentence_transformers'] = st_mod

# Add numpy stub
if 'numpy' not in sys.modules:
    numpy_mod = types.ModuleType('numpy')
    numpy_mod.array = lambda x: x
    numpy_mod.zeros = lambda x: [0] * x if isinstance(x, int) else [[0] * x[1] for _ in range(x[0])]
    numpy_mod.float32 = float
    sys.modules['numpy'] = numpy_mod
    
# Add rich stub
if 'rich' not in sys.modules:
    rich_mod = types.ModuleType('rich')
    console_mod = types.ModuleType('rich.console')
    panel_mod = types.ModuleType('rich.panel')
    progress_mod = types.ModuleType('rich.progress')
    table_mod = types.ModuleType('rich.table')
    
    class DummyConsole:
        def print(self, *args, **kwargs):
            print(*[str(arg).replace('[bold]', '').replace('[/]', '').replace('[green]', '').replace('[blue]', '') for arg in args])
    
    class DummyPanel:
        def __init__(self, content, **kwargs):
            self.content = content
    
    class DummyProgress:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def add_task(self, *args, **kwargs):
            return 1
        def update(self, *args, **kwargs):
            pass
    
    class DummyTable:
        def __init__(self, *args, **kwargs):
            pass
        def add_column(self, *args, **kwargs):
            pass
        def add_row(self, *args, **kwargs):
            pass
    
    console_mod.Console = DummyConsole
    panel_mod.Panel = DummyPanel
    progress_mod.Progress = DummyProgress
    progress_mod.SpinnerColumn = lambda: None
    progress_mod.TextColumn = lambda x: None
    progress_mod.BarColumn = lambda: None
    progress_mod.TaskProgressColumn = lambda: None
    progress_mod.TimeElapsedColumn = lambda: None
    table_mod.Table = DummyTable
    
    rich_mod.console = console_mod
    rich_mod.panel = panel_mod
    rich_mod.progress = progress_mod
    rich_mod.table = table_mod
    
    sys.modules['rich'] = rich_mod
    sys.modules['rich.console'] = console_mod
    sys.modules['rich.panel'] = panel_mod
    sys.modules['rich.progress'] = progress_mod
    sys.modules['rich.table'] = table_mod
