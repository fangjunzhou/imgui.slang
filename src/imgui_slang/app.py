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

import imgui_slang
from imgui_slang.render_targets.dockspace import Dockspace
from imgui_slang.imgui_adapter import ImguiAdapter
from imgui_slang.render_targets.render_target import RenderTarget


class App:
    # Window config.
    window_size = glm.ivec2(960, 540)
    window_title = "SlangPy Application"
    window_resizable = True

    # SGL config.
    device_type = spy.DeviceType.automatic
    enable_debug_layer = False
    shader_paths = [imgui_slang.GUI_SHADER_PATH]

    # Font config.
    font_path = BehaviorSubject[Path | None](None)
    font_size = BehaviorSubject[int](16)

    # Font state.
    _font_path: Path | None = None
    _font_size = 16
    _need_font_reload: bool = False

    # Render targets.
    _render_targets: List[RenderTarget] = []
    _dockspace: Dockspace | None = None

    # Application states.
    _start_time: float = 0.0
    _last_frame_time: float = 0.0
    _curr_window_size: BehaviorSubject[glm.ivec2] = BehaviorSubject(
        glm.ivec2(window_size)
    )
    _fb_scale: BehaviorSubject[int] = BehaviorSubject(1)

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
        self.adapter = ImguiAdapter(self.window, self.device, self._fb_scale.value)

        # Setup callbacks.
        self.window.on_resize = self.on_resize
        self.window.on_mouse_event = self.on_mouse_event
        self.window.on_keyboard_event = self.on_keyboard_event
        self.window.on_drop_files = self.on_drop_files
        self.window.on_gamepad_event = self.on_gamepad_event
        self.window.on_gamepad_state = self.on_gamepad_state

        # Load font.
        self._reload_font()

        # Create dockspace.
        self._dockspace = Dockspace(
            device=self.device,
            window_size=self._curr_window_size,
        )

        # Setup app states.
        self._start_time = time.time()
        self._last_frame_time = self._start_time

        # Subscribe to framebuffer scale changes.
        self._fb_scale.subscribe(self.on_fb_scale_changed)

        # Subscribe to font config changes.
        self.font_path.subscribe(self.on_font_path_changed)
        self.font_size.subscribe(self.on_font_size_changed)

    def _reload_font(self) -> None:
        if self._font_path is None:
            return
        self.io.fonts.clear()
        self.io.fonts.add_font_from_file_ttf(
            str(self._font_path), self._font_size * self._fb_scale.value
        )
        self.adapter.refresh_font_texture()
        self.io.font_global_scale = 1.0 / self._fb_scale.value

    def on_font_path_changed(self, font_path: Path | None) -> None:
        self._font_path = font_path
        self._need_font_reload = True

    def on_font_size_changed(self, font_size: int) -> None:
        self._font_size = font_size
        self._need_font_reload = True

    def on_fb_scale_changed(self, fb_scale: int) -> None:
        self.adapter.fb_scale = fb_scale
        self.adapter.resize(
            self._curr_window_size.value.x, self._curr_window_size.value.y
        )
        self._need_font_reload = True

    def on_resize(self, width: int, height: int) -> None:
        self.adapter.fb_scale = self._fb_scale.value
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

            # Handle font reload if needed.
            if self._need_font_reload:
                self._reload_font()
                self._need_font_reload = False

            # Yield to event loop.
            await asyncio.sleep(0)
