"""
A slangpy imgui render target that will be rendered every frame.
"""

from typing import NotRequired, TypedDict, Unpack
import slangpy as spy
from imgui_slang.imgui_adapter import ImguiAdapter


class RenderArgs(TypedDict):
    device: NotRequired[spy.Device | None]
    adapter: NotRequired[ImguiAdapter | None]


class RenderTarget:
    """A render target base class for slangpy imgui applications.

    :param device: The slangpy device setup by the application.
    """

    def __init__(self, **kwargs: Unpack[RenderArgs]) -> None:
        self._device = kwargs.get("device")
        self._adapter = kwargs.get("adapter")

    def render(self, time: float, delta_time: float) -> None:
        """Called every frame to render the target.

        :param time: Current time in seconds.
        :param delta_time: Time elapsed since last frame in seconds.
        """
        pass
