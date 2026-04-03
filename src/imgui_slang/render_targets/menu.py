from typing import Callable, Unpack

from imgui_bundle import imgui
from reactivex import Observable
from imgui_slang.render_targets.render_target import (
    RenderArgs,
    RenderTarget,
)


class MenuItemArgs(RenderArgs):
    name: str
    open: Observable[bool]
    on_open_changed: Callable[[bool], None]


class MenuItem(RenderTarget):

    _open: bool
    _on_open_changed: Callable[[bool], None]

    def __init__(self, **kwargs: Unpack[MenuItemArgs]) -> None:
        super().__init__(**kwargs)

        self.name = kwargs["name"]

        def update_open(open: bool) -> None:
            self._open = open

        kwargs["open"].subscribe(update_open)
        self._on_open_changed = kwargs["on_open_changed"]

    def render(self, time: float, delta_time: float) -> None:
        changed, new_open = imgui.menu_item(self.name, "", self._open)
        if changed:
            self._on_open_changed(new_open)


class SimpleMenuItemArgs(RenderArgs):
    name: str
    on_clicked: Callable[[], None]


class SimpleMenuItem(RenderTarget):
    def __init__(self, **kwargs: Unpack[SimpleMenuItemArgs]) -> None:
        super().__init__(**kwargs)
        self.name = kwargs["name"]
        self._on_clicked = kwargs["on_clicked"]

    def render(self, time: float, delta_time: float) -> None:
        if imgui.menu_item_simple(self.name):
            self._on_clicked()


class MenuArgs(RenderArgs):
    name: str
    children: list[RenderTarget]


class Menu(RenderTarget):
    _name: str
    _children: list[RenderTarget]

    def __init__(self, **kwargs: Unpack[MenuArgs]) -> None:
        super().__init__(**kwargs)
        self._name = kwargs["name"]
        self._children = kwargs["children"]

    def render(self, time: float, delta_time: float) -> None:
        if imgui.begin_menu(self._name):
            for child in self._children:
                child.render(time, delta_time)
            imgui.end_menu()
