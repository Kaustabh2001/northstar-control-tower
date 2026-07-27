from collections import Counter
from html.parser import HTMLParser
from pathlib import Path


class BlueprintParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.tabs: list[str] = []
        self.views: list[str] = []
        self.scripts = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if element_id := attributes.get("id"):
            self.ids.append(element_id)
        if tab := attributes.get("data-view"):
            self.tabs.append(tab)
        if tag == "section" and "view" in (attributes.get("class") or "").split():
            view_id = attributes.get("id") or ""
            if view_id.startswith("view-"):
                self.views.append(view_id.removeprefix("view-"))
        if tag == "script":
            self.scripts += 1


path = Path(__file__).resolve().parents[1] / "docs" / "serviceops-exact-implementation-plan.html"
html = path.read_text(encoding="utf-8")
parser = BlueprintParser()
parser.feed(html)

duplicate_ids = [element_id for element_id, count in Counter(parser.ids).items() if count > 1]
result = {
    "bytes": path.stat().st_size,
    "doctype": html.lower().startswith("<!doctype html>"),
    "duplicate_ids": duplicate_ids,
    "tabs": parser.tabs,
    "views": parser.views,
    "tabs_match_views": set(parser.tabs) == set(parser.views),
    "scripts": parser.scripts,
}

print(result)
if (
    not result["doctype"]
    or duplicate_ids
    or not result["tabs_match_views"]
    or result["scripts"] != 1
):
    raise SystemExit(1)
