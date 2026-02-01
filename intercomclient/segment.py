from dataclasses import dataclass


@dataclass
class Segment:
    segment_number: int
    start_time: float
    end_time: float
    frame_count: int
    file_path: str
