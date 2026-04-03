from typing import Unpack
from reactivex.subject import BehaviorSubject
from imgui_bundle import imgui, imgui_ctx

from imgui_slang.render_targets.window import Window, WindowArgs


MAX_FB_SCALE = 4
MIN_FB_SCALE = 1


class SettingsWindowArgs(WindowArgs):
    fb_scale: BehaviorSubject[int]


class SettingsWindow(Window):
    size_min: tuple[float, float] = (400, 300)

    def __init__(self, **kwargs: Unpack[SettingsWindowArgs]) -> None:
        super().__init__(**kwargs)
        self._fb_scale = kwargs["fb_scale"]

    def render_window(self, time: float, delta_time: float, open: bool | None) -> bool:
        with imgui_ctx.begin(
            "Settings", p_open=open, flags=self.window_flags
        ) as window:
            changed, new_fb_scale = imgui.input_int(
                label="Framebuffer Scale",
                v=self._fb_scale.value,
                step=1,
                step_fast=5,
            )
            if changed:
                self._fb_scale.on_next(
                    max(MIN_FB_SCALE, min(MAX_FB_SCALE, new_fb_scale))
                )
        return open == True
