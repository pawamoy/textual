from __future__ import annotations

import logging

from rich.console import RenderableType
from rich.style import StyleType


from .. import events
from ..message import Message
from ..scrollbar import ScrollTo, ScrollBar
from ..geometry import clamp
from ..page import Page
from ..views import DockView
from ..reactive import Reactive


log = logging.getLogger("rich")


class ScrollView(DockView):
    def __init__(
        self,
        renderable: RenderableType | None = None,
        *,
        name: str | None = None,
        style: StyleType = "",
        fluid: bool = True,
    ) -> None:
        self.fluid = fluid
        self._vertical_scrollbar = ScrollBar(vertical=True)
        self._page = Page(renderable or "", style=style)
        super().__init__(name=name)

    x: Reactive[float] = Reactive(0)
    y: Reactive[float] = Reactive(0)

    target_y: Reactive[float] = Reactive(0)

    def validate_y(self, value: float) -> float:
        return clamp(value, 0, self._page.contents_size.height - self.size.height)

    def validate_target_y(self, value: float) -> float:
        return clamp(value, 0, self._page.contents_size.height - self.size.height)

    async def watch_y(self, new_value: float) -> None:
        self._page.y = round(new_value)
        self._vertical_scrollbar.position = round(new_value)

    async def update(self, renderabe: RenderableType) -> None:
        self._page.update(renderabe)
        self.require_repaint()

    async def on_mount(self, event: events.Mount) -> None:
        await self.dock(self._vertical_scrollbar, edge="right", size=1)
        await self.dock(self._page, edge="top")

    def scroll_up(self) -> None:
        self.target_y += 1.5
        self.animate("y", self.target_y, easing="out_cubic", speed=80)

    def scroll_down(self) -> None:
        self.target_y -= 1.5
        self.animate("y", self.target_y, easing="out_cubic", speed=80)

    def page_up(self) -> None:
        self.target_y -= self.size.height
        self.animate("y", self.target_y, easing="out_cubic")

    def page_down(self) -> None:
        self.target_y += self.size.height
        self.animate("y", self.target_y, easing="out_cubic")

    async def on_mouse_scroll_up(self, event: events.MouseScrollUp) -> None:
        self.scroll_up()

    async def on_mouse_scroll_down(self, event: events.MouseScrollUp) -> None:
        self.scroll_down()

    async def on_key(self, event: events.Key) -> None:
        await self.dispatch_key(event)

    async def key_down(self) -> None:
        self.target_y += 2
        self.animate("y", self.target_y, easing="linear", speed=100)

    async def key_up(self) -> None:
        self.target_y -= 2
        self.animate("y", self.target_y, easing="linear", speed=100)

    async def key_pagedown(self) -> None:
        self.target_y += self.size.height
        self.animate("y", self.target_y, easing="out_cubic")

    async def key_pageup(self) -> None:
        self.target_y -= self.size.height
        self.animate("y", self.target_y, easing="out_cubic")

    async def key_end(self) -> None:
        self.target_y = self._page.contents_size.height - self.size.height
        self.animate("y", self.target_y, duration=1, easing="out_cubic")

    async def key_home(self) -> None:
        self.target_y = 0
        self.animate("y", self.target_y, duration=1, easing="out_cubic")

    async def on_resize(self, event: events.Resize) -> None:
        await super().on_resize(event)
        if self.fluid:
            self._page.update()

    async def message_scroll_up(self, message: Message) -> None:
        self.page_up()

    async def message_scroll_down(self, message: Message) -> None:
        self.page_down()

    async def message_scroll_to(self, message: ScrollTo) -> None:
        if message.x is not None:
            self.target_x = message.x
        if message.y is not None:
            self.target_y = message.y
        self.animate("y", self.target_y, speed=150, easing="out_cubic")

    async def message_page_update(self, message: Message) -> None:
        self.y = self.validate_y(self.y)
        self._vertical_scrollbar.virtual_size = self._page.virtual_size.height
        self._vertical_scrollbar.window_size = self.size.height
