from datetime import datetime
import cv2
import logging
import os
import json
import time
from pathlib import Path
from intercomclient.segment import Segment

LOG = logging.getLogger(__name__)


class VideoWriter:
    def __init__(self, capture_client, config):
        self.capture_client = capture_client
        self.config = config
        self.writer = None
        self.frame_count = 0
        self.segment_number = None

        # Verify our directories exist
        Path(self.config.output_dir_path).mkdir(parents=True, exist_ok=True)
        self.fourcc = cv2.VideoWriter_fourcc(*self.config.fourcc)

    def capture_frame(self):
        """Capture single frame with timestamp"""
        ret, frame = self.capture_client.read()
        if not ret:
            LOG.warning("Failed to capture frame")
            return None

        # Add timestamp overlay
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(
            frame,
            timestamp,
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),  # Green text
            2,
        )

        return frame

    def record_segment(self, segment_number) -> Segment:
        self.segment_number = segment_number
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = (
            f"segment_{timestamp}_{self.segment_number:04d}.{self.config.video_format}"
        )
        output_file_path = os.path.join(self.config.output_dir_path, filename)
        self.writer = cv2.VideoWriter(
            output_file_path, self.fourcc, self.config.fps, self.config.resolution
        )

        if not self.writer.isOpened():
            LOG.error("Cannot open video writer")
            raise RuntimeError("Cannot open video writer")

        def continue_recording():
            duration_complete = (
                datetime.now() - segment_start
            ).seconds < self.config.segment_duration

            return duration_complete

        try:
            segment_start = datetime.now()
            while continue_recording():
                frame = self.capture_frame()
                if frame is not None:
                    self.writer.write(frame)
                    self.frame_count += 1

                time.sleep(1 / self.config.fps)
                LOG.debug(
                    f"Recording segment {self.segment_number}, frame {self.frame_count}"
                )

            segment = Segment(
                segment_number=self.segment_number,
                start_time=datetime.now().timestamp(),
                end_time=datetime.now().timestamp(),
                frame_count=self.frame_count,
                file_path=output_file_path,
            )

            self.save_metadata(segment)

        except Exception as e:
            raise e

        finally:
            self.writer.release()

        return segment

    def save_metadata(self, segment, motion_events=None):
        """Save metadata JSON for the segment"""
        metadata = {
            "filename": segment.file_path,
            "camera_id": "pi-01",
            "start_time": segment.start_time,
            "end_time": segment.end_time,
            "duration_seconds": self.config.segment_duration,
            "resolution": f"{self.config.resolution[0]}x{self.config.resolution[1]}",
            "fps": self.config.fps,
            "total_frames": segment.frame_count,
            "motion_events": motion_events or [],
            "file_size_bytes": os.path.getsize(segment.file_path)
            if os.path.exists(segment.file_path)
            else 0,
        }

        metadata_path = segment.file_path.replace(
            f".{self.config.video_format}", ".json"
        )
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
