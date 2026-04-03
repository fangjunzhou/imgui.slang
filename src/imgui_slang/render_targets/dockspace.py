"""
A dockspace implementation to host imgui windows, menus, and status bar.
"""

from typing import List, Unpack
from imgui_bundle import imgui, imgui_ctx
from reactivex import Observable
import reactivex.operators as ops
from pyglm import glm

from imgui_slang.render_targets.render_target import (
    RenderArgs,
    RenderTarget,
)


class DockspaceArgs(RenderArgs):
    window_size: Observable[glm.ivec2]


class Dockspace(RenderTarget):
    _menu_items: List[RenderTarget] = []
    _status_items: List[RenderTarget] = []

    _window_size: glm.ivec2

    def __init__(self, **kwargs: Unpack[DockspaceArgs]) -> None:
        super().__init__(**kwargs)

        def update_window_size(size: glm.ivec2) -> None:
            self._window_size = glm.ivec2(size)

        kwargs["window_size"].pipe(ops.distinct()).subscribe(update_window_size)

    def build(self, dockspace_id: int) -> None:
        """Build the dockspace layout.

        :param dockspace_id: The imgui dockspace ID.
        """
        pass

    def render(self, time: float, delta_time: float) -> None:
        # Render menu bar.
        with imgui_ctx.begin_main_menu_bar():
            for item in self._menu_items:
                item.render(time, delta_time)

        # Dockspace.
        side_bar_height = imgui.get_frame_height()
        imgui.set_next_window_pos((0.0, side_bar_height))
        imgui.set_next_window_size(
            (self._window_size.x, self._window_size.y - 2 * side_bar_height)
        )
        window_flags = (
            imgui.WindowFlags_.no_title_bar.value
            | imgui.WindowFlags_.no_collapse.value
            | imgui.WindowFlags_.no_resize.value
            | imgui.WindowFlags_.no_move.value
            | imgui.WindowFlags_.no_bring_to_front_on_focus.value
            | imgui.WindowFlags_.no_nav_focus.value
            | imgui.WindowFlags_.no_background.value
        )
        with imgui_ctx.begin("Dockspace", True, window_flags):
            dockspace_id = imgui.get_id("MainDockspace")
            self.build(dockspace_id)
            imgui.dock_space(dockspace_id)

        # Render status bar.
        imgui.set_next_window_pos((0.0, self._window_size.y - side_bar_height))
        imgui.set_next_window_size((self._window_size.x, side_bar_height))
        window_flags = (
            imgui.WindowFlags_.no_title_bar.value
            | imgui.WindowFlags_.no_collapse.value
            | imgui.WindowFlags_.menu_bar.value
            | imgui.WindowFlags_.no_resize.value
            | imgui.WindowFlags_.no_move.value
            | imgui.WindowFlags_.no_bring_to_front_on_focus.value
            | imgui.WindowFlags_.no_nav_focus.value
            | imgui.WindowFlags_.no_background.value
        )
        with imgui_ctx.begin("StatusBar", True, window_flags):
            with imgui_ctx.begin_menu_bar():
                for item in self._status_items:
                    item.render(time, delta_time)
