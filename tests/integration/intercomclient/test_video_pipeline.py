import pytest
import tempfile
from intercomclient.video_pipeline import VideoPipeline
from tests.integration.conftest import config as test_config


@pytest.fixture
def config():
    """Create and return a Config instance"""
    return test_config()  # Instantiate Config


@pytest.mark.usefixtures("config")
class TestVideoPipeline:
    def test_init_camera(self, config):
        pipeline = VideoPipeline(config=config)
        capture = pipeline.init_camera(source=0)
        assert capture.isOpened()

    def test_record_segment(self, config):
        with tempfile.TemporaryDirectory() as tmp_output_dir_path:
            config.output_dir_path = tmp_output_dir_path
            config.segment_duration = 1
            pipeline = VideoPipeline(config=config)
            pipeline.record_segment()
