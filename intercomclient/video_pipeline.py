import cv2
import logging
from intercomclient.config import Config
from intercomclient.video_writer import VideoWriter

LOG = logging.getLogger(__name__)


class VideoPipeline:
    def __init__(self, config=Config):
        self.config = config
        self.capture = None
        self.segment_number = 0

    def init_camera(self, source=0) -> cv2.VideoCapture:
        source = source or self.config.video_source
        self.capture = cv2.VideoCapture(source)
        if not self.capture.isOpened():
            raise ValueError("Unable to open video source")

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.resolution[0])
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.resolution[1])

        ret, frame = self.capture.read()
        if not ret:
            LOG.error("Cannot read from camera")
            raise RuntimeError("Cannot read from camera")

        return self.capture

    def record_segment(self):
        video_writer = VideoWriter(self.init_camera(), self.config)
        video_writer.record_segment(segment_number=self.segment_number)
        self.segment_number += 1
