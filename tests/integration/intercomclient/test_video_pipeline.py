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

    # def test_init_writer(self, config):
    #     with tempfile.TemporaryDirectory() as tmp_output_dir_path:
    #         config.output_dir_path = tmp_output_dir_path
    #         pipeline = VideoPipeline(config=config)
    #         writer = pipeline.init_writer(0)
    #         assert writer.isOpened()

    # def test_capture_frame(self, config):
    #     pipeline = VideoPipeline(config=config)
    #     capture = pipeline.init_camera(source=0)
    #     frame = pipeline.capture_frame()
    #     capture.release()
    #     assert frame is not None

    def test_record_segment(self, config):
        with tempfile.TemporaryDirectory() as tmp_output_dir_path:
            config.output_dir_path = tmp_output_dir_path
            config.segment_duration = 1
            pipeline = VideoPipeline(config=config)
            pipeline.record_segment()
