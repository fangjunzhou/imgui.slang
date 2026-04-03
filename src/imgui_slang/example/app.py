from typing import Unpack
from imgui_bundle import imgui
from reactivex.subject import BehaviorSubject
from imgui_slang.app import App
from imgui_slang.example.demo_windows import (
    ImGuiDemoWindow,
    ImPlot3DDemoWindow,
)
from imgui_slang.example.settings import SettingsWindow
from imgui_slang.example.file_menu_item import OpenFileMenuItem, SaveFileMenuItem
from imgui_slang.render_targets.dockspace import Dockspace, DockspaceArgs
from imgui_slang.render_targets.menu import (
    Menu,
    MenuItem,
)


class ExampleDockspaceArgs(DockspaceArgs):
    imgui_demo_opened: BehaviorSubject[bool]
    implot_demo_opened: BehaviorSubject[bool]
    settings_opened: BehaviorSubject[bool]


class ExampleDockspace(Dockspace):
    def __init__(self, **kwargs: Unpack[ExampleDockspaceArgs]) -> None:
        super().__init__(**kwargs)
        self._menu_items = [
            Menu(
                device=self._device,
                adapter=self._adapter,
                name="File",
                children=[
                    OpenFileMenuItem(
                        device=self._device,
                        adapter=self._adapter,
                    ),
                    SaveFileMenuItem(
                        device=self._device,
                        adapter=self._adapter,
                    ),
                ],
            ),
            Menu(
                device=self._device,
                adapter=self._adapter,
                name="Views",
                children=[
                    MenuItem(
                        device=self._device,
                        adapter=self._adapter,
                        name="ImGui Demo Window",
                        open=kwargs["imgui_demo_opened"],
                        on_open_changed=lambda opened: kwargs[
                            "imgui_demo_opened"
                        ].on_next(opened),
                    ),
                    MenuItem(
                        device=self._device,
                        adapter=self._adapter,
                        name="ImPlot Demo Window",
                        open=kwargs["implot_demo_opened"],
                        on_open_changed=lambda opened: kwargs[
                            "implot_demo_opened"
                        ].on_next(opened),
                    ),
                ],
            ),
            MenuItem(
                device=self._device,
                adapter=self._adapter,
                name="Settings",
                open=kwargs["settings_opened"],
                on_open_changed=lambda opened: kwargs["settings_opened"].on_next(
                    opened
                ),
            ),
        ]

    def build(self, dockspace_id: int) -> None:
        # Build dock space.
        if not imgui.internal.dock_builder_get_node(dockspace_id):
            imgui.internal.dock_builder_remove_node(dockspace_id)
            main_id = imgui.internal.dock_builder_add_node(dockspace_id)
            imgui.internal.dock_builder_dock_window("Dear ImGui Demo", main_id)
            imgui.internal.dock_builder_dock_window("ImPlot3D Demo", main_id)
            imgui.internal.dock_builder_finish(dockspace_id)


class ExampleApp(App):
    _imgui_demo_opened: BehaviorSubject[bool] = BehaviorSubject(True)
    _implot_demo_opened: BehaviorSubject[bool] = BehaviorSubject(False)
    _settings_opened: BehaviorSubject[bool] = BehaviorSubject(False)

    def __init__(self) -> None:
        super().__init__([])

        self._render_targets = [
            ImGuiDemoWindow(
                device=self.device,
                adapter=self.adapter,
                open=self._imgui_demo_opened,
                on_close=lambda: self._imgui_demo_opened.on_next(False),
            ),
            ImPlot3DDemoWindow(
                device=self.device,
                adapter=self.adapter,
                open=self._implot_demo_opened,
                on_close=lambda: self._implot_demo_opened.on_next(False),
            ),
            SettingsWindow(
                device=self.device,
                adapter=self.adapter,
                open=self._settings_opened,
                on_close=lambda: self._settings_opened.on_next(False),
                fb_scale=self._fb_scale,
            ),
        ]

        self._dockspace = ExampleDockspace(
            device=self.device,
            adapter=self.adapter,
            window_size=self._curr_window_size,
            imgui_demo_opened=self._imgui_demo_opened,
            implot_demo_opened=self._implot_demo_opened,
            settings_opened=self._settings_opened,
        )
