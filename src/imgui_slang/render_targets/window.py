"""
A module defining a basic window render target for slangpy imgui applications.
"""

from typing import Callable, Tuple, Unpack, NotRequired
from imgui_bundle import imgui
from reactivex import Observable
from imgui_slang.render_targets.render_target import (
    RenderArgs,
    RenderTarget,
)


class WindowArgs(RenderArgs):
    open: NotRequired[Observable[bool] | None]
    on_close: NotRequired[Callable[[], None] | None]


class Window(RenderTarget):
    size: Tuple[int, int] = (400, 300)
    size_min: Tuple[float, float] = (200, 150)
    size_max: Tuple[float, float] = (imgui.FLT_MAX, imgui.FLT_MAX)
    window_flags: int = imgui.WindowFlags_.none.value

    _open: bool | None = None
    _on_close: Callable[[], None] | None = None

    def __init__(self, **kwargs: Unpack[WindowArgs]) -> None:
        super().__init__(**kwargs)

        open_observable = kwargs.get("open")
        if open_observable is not None:

            def update_open(open: bool) -> None:
                self._open = open

            open_observable.subscribe(update_open)
            self._on_close = kwargs.get("on_close")

    def render_window(self, time: float, delta_time: float, open: bool | None) -> bool:
        """Render the contents of the window.

        :param time: Current time in seconds.
        :param delta_time: Time elapsed since last frame in seconds.
        :param open: Whether the window is open.
        """
        return True

    def render(self, time: float, delta_time: float) -> None:
        if self._open or self._open is None:
            imgui.set_next_window_size(self.size, imgui.Cond_.once.value)
            imgui.set_next_window_size_constraints(self.size_min, self.size_max)
            if (
                not self.render_window(time, delta_time, self._open)
                and self._on_close is not None
            ):
                self._on_close()
