"""
Application class for SlangPy ImGui Bundle.
"""

from pathlib import Path
from typing import List, Sequence
from imgui_bundle import imgui, implot3d
import slangpy as spy
from pyglm import glm
import time
import asyncio
from reactivex.subject import BehaviorSubject

import slangpy_imgui_bundle
from slangpy_imgui_bundle.render_targets.dockspace import Dockspace
from slangpy_imgui_bundle.imgui_adapter import ImguiAdapter
from slangpy_imgui_bundle.render_targets.render_target import RenderTarget


class App:
    # Window config.
    window_size = glm.ivec2(960, 540)
    window_title = "SlangPy Application"
    window_resizable = True
    fb_scale = 1.0

    # SGL config.
    device_type = spy.DeviceType.automatic
    enable_debug_layer = False
    shader_paths = [slangpy_imgui_bundle.GUI_SHADER_PATH]

    # Render targets.
    _render_targets: List[RenderTarget] = []
    _dockspace: Dockspace | None = None

    # Application states.
    _start_time: float = 0.0
    _last_frame_time: float = 0.0
    _curr_window_size: BehaviorSubject[glm.ivec2] = BehaviorSubject(
        glm.ivec2(window_size)
    )

    def __init__(self, user_shader_paths: List[Path] = []) -> None:
        self.window = spy.Window(
            width=self.window_size.x,
            height=self.window_size.y,
            title=self.window_title,
            resizable=self.window_resizable,
        )
        # Append user shader paths to default shader paths.
        self.shader_paths.extend(user_shader_paths)
        # Create SGL device.
        self.device = spy.create_device(
            type=self.device_type,
            enable_debug_layers=self.enable_debug_layer,
            include_paths=self.shader_paths,
        )

        # Setup renderer.
        imgui.create_context()
        implot3d.create_context()
        self.io = imgui.get_io()
        self.io.set_ini_filename("")
        self.io.set_log_filename("")
        # Enable docking.
        self.io.config_flags |= imgui.ConfigFlags_.docking_enable.value
        self.adapter = ImguiAdapter(self.window, self.device, self.fb_scale)

        # Setup callbacks.
        self.window.on_resize = self.on_resize
        self.window.on_mouse_event = self.on_mouse_event
        self.window.on_keyboard_event = self.on_keyboard_event
        self.window.on_drop_files = self.on_drop_files
        self.window.on_gamepad_event = self.on_gamepad_event
        self.window.on_gamepad_state = self.on_gamepad_state

        # Create dockspace.
        self._dockspace = Dockspace(
            device=self.device,
            window_size=self._curr_window_size,
        )

        # Setup app states.
        self._start_time = time.time()
        self._last_frame_time = self._start_time

    def on_resize(self, width: int, height: int) -> None:
        self.adapter.fb_scale = self.fb_scale
        self.adapter.resize(width, height)
        self._curr_window_size.on_next(glm.ivec2(width, height))

    def on_mouse_event(self, event: spy.MouseEvent) -> None:
        self.adapter.mouse_event(event)

    def on_keyboard_event(self, event: spy.KeyboardEvent) -> None:
        self.adapter.key_event(event)
        self.adapter.unicode_input(event.codepoint)

    def on_gamepad_event(self, event: spy.GamepadEvent) -> None:
        pass

    def on_gamepad_state(self, state: spy.GamepadState) -> None:
        pass

    def on_drop_files(self, file_paths: Sequence[str]) -> None:
        pass

    def update(self) -> None:
        pass

    async def run(self) -> None:
        while not self.window.should_close():
            current_time = time.time()
            elapsed_time = current_time - self._start_time
            delta_time = current_time - self._last_frame_time
            self._last_frame_time = current_time

            # Poll events.
            self.window.process_events()
            # Start ImGui frame.
            imgui.new_frame()

            # Render dockspace.
            if self._dockspace is not None:
                self._dockspace.render(elapsed_time, delta_time)
            # Render all render targets.
            for target in self._render_targets:
                target.render(elapsed_time, delta_time)

            imgui.render()
            # Render ImGui.
            self.adapter.render(imgui.get_draw_data())

            self.update()

            # Yield to event loop.
            await asyncio.sleep(0)
