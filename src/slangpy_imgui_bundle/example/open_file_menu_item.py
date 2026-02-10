import asyncio
import logging
from pathlib import Path
from typing import Unpack
from imgui_bundle import portable_file_dialogs as pfd
from slangpy_imgui_bundle.render_targets.menu import SimpleMenuItem, SimpleMenuItemArgs
from slangpy_imgui_bundle.render_targets.render_target import RenderArgs
from slangpy_imgui_bundle.utils.file_dialog import async_open_file_dialog


logger = logging.getLogger(__name__)


class OpenFileMenuItem(SimpleMenuItem):
    def __init__(self, **kwargs: Unpack[RenderArgs]) -> None:
        def on_clicked() -> None:
            asyncio.create_task(self.file_dialog())

        super_kwargs: SimpleMenuItemArgs = {
            "device": kwargs.get("device"),
            "adapter": kwargs.get("adapter"),
            "name": "Open",
            "on_clicked": on_clicked,
        }
        super().__init__(**super_kwargs)

    async def file_dialog(self):
        files = await async_open_file_dialog(
            title="Open File",
            default_path=str(Path.home()),
            filters=["All Files", "*.*"],
            options=pfd.opt.multiselect,
        )

        if files:
            logger.info(f"Selected files: {files}")
        else:
            logger.info("No file selected.")
