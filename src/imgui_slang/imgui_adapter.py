"""
Slangpy adapter for ImGui Bundle
"""

import ctypes
import logging
import slangpy as spy
import numpy as np
from imgui_bundle import imgui


logger = logging.getLogger(__name__)


REVERSE_KEY_MAP = {
    spy.KeyCode.tab: imgui.Key.tab,
    spy.KeyCode.left: imgui.Key.left_arrow,
    spy.KeyCode.right: imgui.Key.right_arrow,
    spy.KeyCode.up: imgui.Key.up_arrow,
    spy.KeyCode.down: imgui.Key.down_arrow,
    spy.KeyCode.page_up: imgui.Key.page_up,
    spy.KeyCode.page_down: imgui.Key.page_down,
    spy.KeyCode.home: imgui.Key.home,
    spy.KeyCode.end: imgui.Key.end,
    spy.KeyCode.delete: imgui.Key.delete,
    spy.KeyCode.space: imgui.Key.space,
    spy.KeyCode.backspace: imgui.Key.backspace,
    spy.KeyCode.enter: imgui.Key.enter,
    spy.KeyCode.escape: imgui.Key.escape,
    spy.KeyCode.left_shift: imgui.Key.left_shift,
}


class ImguiAdapter:
    """
    The slangpy renderer adapter for ImGui Bundle.
    """

    fb_scale: float = 1.0

    def __init__(
        self, window: spy.Window, device: spy.Device, fb_scale: float = 1.0
    ) -> None:
        if not imgui.get_current_context():
            raise RuntimeError(
                "No valid ImGui context. Use imgui.create_context() first and/or "
                "imgui.set_current_context()."
            )

        # Registered textures.
        self._textures = {}
        self._texture_id = 0

        self.window = window
        self.device = device
        self.fb_scale = fb_scale

        # Create window surface.
        self.surface = self.device.create_surface(self.window)

        # Input layout.
        self.input_layout = self.device.create_input_layout(
            input_elements=[
                {
                    "semantic_name": "POSITION",
                    "semantic_index": 0,
                    "format": spy.Format.rg32_float,
                },
                {
                    "semantic_name": "TEXCOORD",
                    "semantic_index": 0,
                    "format": spy.Format.rg32_float,
                    "offset": 8,
                },
                {
                    "semantic_name": "COLOR",
                    "semantic_index": 0,
                    "format": spy.Format.rgba8_unorm,
                    "offset": 16,
                },
            ],
            vertex_streams=[{"stride": 20}],
        )
        # Load shader modules.
        self.program = self.device.load_program(
            "imgui_renderer.slang", ["vertexMain", "fragmentMain"]
        )
        self.pipeline = self.device.create_render_pipeline(
            program=self.program,
            input_layout=self.input_layout,
            targets=[
                {
                    "format": spy.Format.rgba16_float,
                    "enable_blend": True,
                    "color": spy.AspectBlendDesc(
                        {
                            "src_factor": spy.BlendFactor.src_alpha,
                            "dst_factor": spy.BlendFactor.inv_src_alpha,
                            "op": spy.BlendOp.add,
                        }
                    ),
                }
            ],
        )

        # Create vertex and index buffers.
        self.vbo = self.device.create_buffer(
            usage=spy.BufferUsage.vertex_buffer | spy.BufferUsage.shader_resource,
            label="imgui_vertex_buffer",
            size=imgui.VERTEX_SIZE * 65536,
        )
        self.ibo = self.device.create_buffer(
            usage=spy.BufferUsage.index_buffer | spy.BufferUsage.shader_resource,
            label="imgui_index_buffer",
            size=imgui.INDEX_SIZE * 65536,
        )

        # Get ImGui IO.
        self.io = imgui.get_io()
        # Font texture.
        self._font_texture = None
        self.refresh_font_texture()

        # Resize ImGui display size.
        self.resize(self.window.width, self.window.height)

    def register_texture(self, texture: spy.Texture) -> int:
        texture_id = self._texture_id
        self._texture_id += 1
        sampler = self.device.create_sampler()
        self._textures[texture_id] = (texture, sampler)
        return texture_id

    def unregister_texture(self, texture_id: int) -> None:
        if texture_id in self._textures:
            del self._textures[texture_id]

    def render(self, draw_data: imgui.ImDrawData) -> None:
        """Method to render ImGui draw data at the end of each frame.

        :param draw_data: The ImGui draw data to render.
        """
        # Acquire next surface texture.
        surface_texture = self.surface.acquire_next_image()

        # Rendering commands.
        command_encoder = self.device.create_command_encoder()

        # Projection matrix.
        width, height = self.io.display_size.x, self.io.display_size.y
        fb_w = int(width * self.io.display_framebuffer_scale.x)
        fb_h = int(height * self.io.display_framebuffer_scale.y)
        proj_matrix = np.array(
            [
                [2.0 / width, 0.0, 0.0, -1.0],
                [0.0, -2.0 / height, 0.0, 1.0],
                [0.0, 0.0, -1.0, 0.0],
                [0.0, 0.0, 0.0, 1.0],
            ]
        )

        # Scale clip rects
        draw_data.scale_clip_rects(imgui.ImVec2(*self.io.display_framebuffer_scale))

        # Clear frame buffer.
        with command_encoder.begin_render_pass(
            {
                "color_attachments": [
                    {
                        "view": self.frame_buffer.create_view({}),
                        "load_op": spy.LoadOp.clear,
                        "store_op": spy.StoreOp.store,
                        "clear_value": (0.0, 0.0, 0.0, 0.0),
                    }
                ]
            }
        ):
            pass

        for commands in draw_data.cmd_lists:
            vtx_type = ctypes.c_byte * commands.vtx_buffer.size() * imgui.VERTEX_SIZE
            idx_type = ctypes.c_byte * commands.idx_buffer.size() * imgui.INDEX_SIZE
            vtx_arr = (vtx_type).from_address(commands.vtx_buffer.data_address())
            idx_arr = (idx_type).from_address(commands.idx_buffer.data_address())
            # Convert to numpy arrays.
            vtx_arr_np = np.frombuffer(vtx_arr, dtype=np.uint8)
            idx_arr_np = np.frombuffer(idx_arr, dtype=np.uint32)
            # Update vertex buffer.
            command_encoder.upload_buffer_data(self.vbo, 0, vtx_arr_np)
            # Update index buffer.
            command_encoder.upload_buffer_data(self.ibo, 0, idx_arr_np)

            for command in commands.cmd_buffer:
                texture_sampler = self._textures.get(command.texture_id)
                if texture_sampler is None:
                    raise ValueError("Texture not registered with ImguiAdapter.")

                texture, sampler = texture_sampler

                # Render ImGui draw data to the frame buffer.
                with command_encoder.begin_render_pass(
                    {
                        "color_attachments": [
                            {
                                "view": self.frame_buffer.create_view({}),
                                "load_op": spy.LoadOp.load,
                                "store_op": spy.StoreOp.store,
                            }
                        ]
                    }
                ) as pass_encoder:
                    root = pass_encoder.bind_pipeline(self.pipeline)
                    root_cursor = spy.ShaderCursor(root)
                    root_cursor["uniforms"]["proj"].write(proj_matrix)
                    root_cursor["uniforms"]["texture"].write(texture)
                    root_cursor["uniforms"]["sampler"].write(sampler)

                    x, y, z, w = (
                        command.clip_rect.x,
                        command.clip_rect.y,
                        command.clip_rect.z,
                        command.clip_rect.w,
                    )
                    x = max(x, 0)
                    y = max(y, 0)
                    z = min(z, fb_w)
                    w = min(w, fb_h)

                    pass_encoder.set_render_state(
                        {
                            "viewports": [
                                spy.Viewport.from_size(
                                    self.frame_buffer.width, self.frame_buffer.height
                                )
                            ],
                            "scissor_rects": [
                                spy.ScissorRect(
                                    {
                                        "min_x": int(x),
                                        "min_y": int(y),
                                        "max_x": int(z),
                                        "max_y": int(w),
                                    }
                                )
                            ],
                            "vertex_buffers": [self.vbo],
                            "index_buffer": self.ibo,
                            "index_format": (
                                spy.IndexFormat.uint16
                                if imgui.INDEX_SIZE == 2
                                else spy.IndexFormat.uint32
                            ),
                        }
                    )
                    pass_encoder.draw_indexed(
                        {
                            "vertex_count": command.elem_count,
                            "start_index_location": command.idx_offset,
                        }
                    )

        # Blit to the surface texture.
        command_encoder.blit(surface_texture, self.frame_buffer)
        self.device.submit_command_buffer(command_encoder.finish())
        del surface_texture

        self.surface.present()

    def refresh_font_texture(self) -> None:
        """Method to refresh the font texture used by ImGui."""
        texture_data = self.io.fonts.get_tex_data_as_rgba32()  # pyright: ignore
        height, width, _ = texture_data.shape

        if self._font_texture is not None:
            self.unregister_texture(self.io.fonts.tex_id)

        self._font_texture = self.device.create_texture(
            type=spy.TextureType.texture_2d,
            format=spy.Format.rgba8_unorm,
            width=width,
            height=height,
            usage=spy.TextureUsage.shader_resource | spy.TextureUsage.unordered_access,
            label="imgui_font_texture",
            data=texture_data,
        )
        self.io.fonts.tex_id = self.register_texture(self._font_texture)
        self.io.fonts.clear_tex_data()

    def resize(self, width: int, height: int) -> None:
        """Method to handle window resizing.

        :param width: The new width of the window.
        :param height: The new height of the window.
        """
        # Update ImGui display size.
        self.io.display_size = imgui.ImVec2(width, height)
        self.io.display_framebuffer_scale = imgui.ImVec2(self.fb_scale, self.fb_scale)
        # Update framebuffer scale.
        self.device.wait()
        if width > 0 and height > 0:
            self.surface.configure(
                int(width * self.fb_scale), int(height * self.fb_scale)
            )
            self.frame_buffer = self._create_frame_buffer(
                int(width * self.fb_scale), int(height * self.fb_scale)
            )
        else:
            self.surface.unconfigure()

    def key_event(self, event: spy.KeyboardEvent) -> None:
        """Method to handle keyboard events.

        :param event: The keyboard event.
        """
        key = event.key
        if key in REVERSE_KEY_MAP:
            imgui_key = REVERSE_KEY_MAP[key]
            down = event.is_key_press()
            self.io.add_key_event(imgui_key, down)

    def mouse_event(self, event: spy.MouseEvent) -> None:
        """Method to handle mouse events.

        :param event: The mouse event.
        """
        # Mouse move event.
        if event.is_move():
            self.io.mouse_pos = imgui.ImVec2(*event.pos)
        if event.is_button_down() or event.is_button_up():
            down = event.is_button_down()
            if event.button == spy.MouseButton.left:
                self.io.mouse_down[0] = down
            elif event.button == spy.MouseButton.right:
                self.io.mouse_down[1] = down
            elif event.button == spy.MouseButton.middle:
                self.io.mouse_down[2] = down
        if event.is_scroll():
            self.io.mouse_wheel += event.scroll.y
            self.io.mouse_wheel_h += event.scroll.x

    def unicode_input(self, codepoint: int) -> None:
        """Method to handle unicode character input.

        :param codepoint: The unicode codepoint.
        """
        self.io.add_input_character(codepoint)

    def shutdown(self) -> None:
        """Method to shutdown the renderer and release resources."""
        pass

    def _create_frame_buffer(self, width: int, height: int) -> spy.Texture:
        return self.device.create_texture(
            format=spy.Format.rgba16_float,
            width=width,
            height=height,
            usage=spy.TextureUsage.render_target
            | spy.TextureUsage.shader_resource
            | spy.TextureUsage.unordered_access,
            label="output_texture",
        )
