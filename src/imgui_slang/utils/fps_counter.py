"""
A FPS counter implementation.
"""

from typing import List, Unpack
from imgui_bundle import imgui

from imgui_slang.render_targets.render_target import RenderArgs, RenderTarget


class FPSCounter(RenderTarget):
    # Circular frame time buffer size
    buffer_size: int = 60
    frame_times: List[float]
    head: int = 0

    def __init__(self, **kwargs: Unpack[RenderArgs]) -> None:
        super().__init__(**kwargs)
        self.frame_times = []

    def render(self, time: float, delta_time: float) -> None:
        # Update frame times buffer
        if len(self.frame_times) < self.buffer_size:
            self.frame_times.append(delta_time)
            self.head = len(self.frame_times) - 1
        else:
            self.head = (self.head + 1) % self.buffer_size
            self.frame_times[self.head] = delta_time
        # Calculate average FPS
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        avg_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0.0
        # Render FPS counter
        imgui.text(f"FPS: {avg_fps:.2f}")
