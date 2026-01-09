from dataclasses import dataclass, field
from typing import Dict, Optional
from playwright.async_api import BrowserContext, Page
from .state import TabState
import uuid

@dataclass
class Tab:
    id: str
    url: str
    state: TabState = TabState.IDLE
    context: Optional[BrowserContext] = None
    page: Optional[Page] = None

class TabManager:
    def __init__(self):
        self.tabs: Dict[str, Tab] = {}

    def create_tab(self, url: str, context: BrowserContext) -> Tab:
        """建立新任務"""
        tab_id = str(uuid.uuid4())[:8]
        tab = Tab(id=tab_id, url=url, context=context)
        self.tabs[tab_id] = tab
        return tab

    def get_tab(self, tab_id: str) -> Optional[Tab]:
        return self.tabs.get(tab_id)

    def update_state(self, tab_id: str, state: TabState):
        if tab_id in self.tabs:
            self.tabs[tab_id].state = state

    def set_page(self, tab_id: str, page: Optional[Page]):
        if tab_id in self.tabs:
            self.tabs[tab_id].page = page

    async def close_tab(self, tab_id: str):
        if tab_id in self.tabs:
            tab = self.tabs[tab_id]
            if tab.page:
                await tab.page.close()
            if tab.context:
                await tab.context.close()
            del self.tabs[tab_id]

    def list_tabs(self) -> list:
        return list(self.tabs.values())
