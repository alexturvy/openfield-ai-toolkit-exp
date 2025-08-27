import sys, types, unittest
from pathlib import Path

sys.path.insert(0, '/workspace/src')


class CleanPipelineSmokeTest(unittest.TestCase):
	def setUp(self):
		pkg = types.ModuleType('insight_synthesizer'); pkg.__path__ = []
		sys.modules['insight_synthesizer'] = pkg
		utils_pkg = types.ModuleType('insight_synthesizer.utils'); utils_pkg.__path__ = []
		sys.modules['insight_synthesizer.utils'] = utils_pkg
		pm_mod = types.ModuleType('insight_synthesizer.utils.progress_manager')
		class ProgressStage:
			DOCUMENT_PROCESSING='Document Processing'
			EMBEDDING_GENERATION='Embedding Generation'
			CLUSTERING='Clustering Analysis'
			INSIGHT_SYNTHESIS='Insight Synthesis'
			VALIDATION='Theme Validation'
			REPORT_GENERATION='Report Generation'
		class DummyPM:
			def start_pipeline(self, total_stages:int=7): pass
			def stage_context(self, *a, **k):
				class Ctx:
					def __enter__(self2): return 0
					def __exit__(self2, exc_type, exc, tb): return False
				return Ctx()
			def finish(self): pass
			def set_stage_status(self, *a, **k): pass
			def update_stage(self, *a, **k): pass
			def log_info(self, *a, **k): pass
		def get_progress_manager(): return DummyPM()
		pm_mod.get_progress_manager = get_progress_manager
		pm_mod.ProgressStage = ProgressStage
		sys.modules['insight_synthesizer.utils.progress_manager'] = pm_mod
		
		emb = types.ModuleType('insight_synthesizer.analysis.embeddings')
		def gen(chunks, progress_manager=None):
			for c in chunks:
				setattr(c, 'embedding', [0.1,0.2,0.3])
			return chunks
		emb.generate_embeddings = gen
		sys.modules['insight_synthesizer.analysis.embeddings'] = emb
		clu = types.ModuleType('insight_synthesizer.analysis.clustering')
		class Cluster:
			def __init__(self, chunks):
				self.chunks = chunks
				self.size = len(chunks)
		clu.perform_clustering = lambda chunks, progress_reporter=None, progress_manager=None: (chunks, [Cluster([c for c in chunks if getattr(c,'embedding',None) is not None])])
		sys.modules['insight_synthesizer.analysis.clustering'] = clu
		llm_pkg = types.ModuleType('insight_synthesizer.llm'); llm_pkg.__path__ = []
		sys.modules['insight_synthesizer.llm'] = llm_pkg
		llm_client = types.ModuleType('insight_synthesizer.llm.client')
		class StubLLM:
			def generate_json(self, *a, **k):
				return True, {
					'theme_name': 'Communication Friction',
					'summary': 'Users experience coordination issues and rely on workarounds.',
					'confidence': 0.82,
					'question_indices': [0],
					'secondary_lenses': ['user_needs']
				}
		llm_client.get_llm_client = lambda: StubLLM()
		sys.modules['insight_synthesizer.llm.client'] = llm_client
		val_pkg = types.ModuleType('insight_synthesizer.validation'); val_pkg.__path__ = []
		sys.modules['insight_synthesizer.validation'] = val_pkg
		val_mod = types.ModuleType('insight_synthesizer.validation.theme_validator')
		class ValidationResult:
			def __init__(self):
				self.theme_coverages = []
				self.overall_quality = 'good'
				self.total_quotes_extracted = 0
				self.avg_coverage_score = 0.65
				self.validation_summary = 'Smoke validation: good coverage across sources.'
		class ThemeValidator:
			def validate_themes(self, synthesized_themes, original_file_paths, progress_manager=None):
				return ValidationResult()
		val_mod.ThemeValidator = ThemeValidator; val_mod.ValidationResult = ValidationResult
		sys.modules['insight_synthesizer.validation.theme_validator'] = val_mod
		
		ten_mod = types.ModuleType('insight_synthesizer.analysis.tensions')
	
ten_mod.detect_tensions = lambda themes, progress_reporter=None: [{'theme_a':1,'theme_b':2,'summary':'Opposing signals'}]
		sys.modules['insight_synthesizer.analysis.tensions'] = ten_mod

	def test_clean_pipeline_smoke(self):
		from insight_synthesizer_clean.pipeline import Pipeline
		base = Path('/workspace/tmp_clean_tests'); base.mkdir(parents=True, exist_ok=True)
		plan = base/'plan.txt'; plan.write_text('- What are pain points?\n- What do users need?\n', encoding='utf-8')
		d = base/'docs'; d.mkdir(exist_ok=True)
		(d/'doc1.txt').write_text('User: Meetings are chaotic.\n\nInterviewer: Tell me more.\n\nUser: We use our own trackers as a workaround.', encoding='utf-8')
		pipe = Pipeline(); report = pipe.run(plan, sorted(d.glob('**/*.txt')))
		self.assertIn('# Insight Report', report.markdown)
		self.assertIn('Communication Friction', report.markdown)
		self.assertTrue(report.tensions == [] or isinstance(report.tensions, list))


if __name__ == '__main__':
	unittest.main()