from typing import Callable, List, Unpack

from imgui_bundle import imgui
from imgui_slang.render_targets.render_target import RenderTarget, RenderArgs


class SimplePopupArgs(RenderArgs):
    name: str
    title: str
    content: List[str]


class SimplePopup(RenderTarget):
    def __init__(self, **kwargs: Unpack[SimplePopupArgs]) -> None:
        super().__init__(**kwargs)

        self._name = kwargs["name"]
        self._title = kwargs["title"]
        self._content = kwargs["content"]

        self._should_open = False

    def open(self) -> None:
        self._should_open = True

    def render(self, time: float, delta_time: float) -> None:
        if self._should_open:
            imgui.open_popup(self._name)
            self._should_open = False

        if imgui.begin_popup_modal(
            self._name, flags=imgui.WindowFlags_.always_auto_resize.value
        )[0]:
            imgui.text(self._title)
            for line in self._content:
                imgui.text(line)
            if imgui.button("OK"):
                imgui.close_current_popup()
            imgui.end_popup()
