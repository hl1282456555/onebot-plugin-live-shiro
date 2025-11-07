import atexit
from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Optional, TypedDict

from jinja2 import Environment, FileSystemLoader
from PIL import Image
from playwright.sync_api import sync_playwright

current_dir = Path(__file__).resolve().parent
file_loader = FileSystemLoader(current_dir / "templates")

_browser = None
_playwright_instance = None

class NormalData(TypedDict):
    user_name: str
    avatar_url: str
    time: str
    title: str
    link: str
    content: str
    image_urls: Optional[list[str]] # Optional

class RenderPageType(Enum):
    NORMAL = "normal.html"

RenderPageParams = {
    RenderPageType.NORMAL: NormalData
}

def get_browser():
    global _browser, _playwright_instance
    if _browser is None:
        _playwright_instance = sync_playwright().start()
        _browser = _playwright_instance.chromium.launch(
            headless=True,
            args=['--disable-gpu', '--no-sandbox', '--disable-dev-shm-usage']
        )
    return _browser


@atexit.register
def cleanup():
    global _browser, _playwright_instance
    if _browser:
        _browser.close()
        _browser = None
    if _playwright_instance:
        _playwright_instance.stop()
        _playwright_instance = None


def crop_transparent_edges(img: Image.Image, border: int = 10) -> Image.Image:
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    pix = img.load()
    width, height = img.size
    x_min, y_min = width, height
    x_max, y_max = 0, 0

    for y in range(height):
        for x in range(width):
            if pix[x, y][3] != 0:
                x_min = min(x_min, x)
                y_min = min(y_min, y)
                x_max = max(x_max, x)
                y_max = max(y_max, y)

    if x_max < x_min or y_max < y_min:
        return img

    left = max(0, x_min - border)
    upper = max(0, y_min - border)
    right = min(width, x_max + border)
    lower = min(height, y_max + border)

    return img.crop((left, upper, right, lower))


def _render_png_from_html(html_str: str, width: int = 800) -> bytes:
    browser = get_browser()
    page = browser.new_page(viewport={"width": width, "height": 2000}, device_scale_factor=2)
    page.set_content(html_str)
    page.wait_for_load_state("networkidle")

    content = page.query_selector(".content-wrapper")
    clip = None
    if content:
        box = content.bounding_box()
        clip = {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]}

    screenshot = page.screenshot(clip=clip, type="png", omit_background=True)
    page.close()

    img = Image.open(BytesIO(screenshot))
    img = crop_transparent_edges(img, border=10)
    output = BytesIO()
    img.save(output, format="PNG")
    return output.getvalue()


def render_png_from_template(render_type: RenderPageType, data: dict, width: int = 800) -> bytes:
    expected_type = RenderPageParams.get(render_type)
    if expected_type is not None:
        missing_keys = [k for k in expected_type.__annotations__.keys() if k not in data]
        if missing_keys:
            raise ValueError(f"{render_type} requires keys: {missing_keys}")

    env = Environment(loader=file_loader)
    template = env.get_template(render_type.value)
    html_str = template.render(data)
    return _render_png_from_html(html_str, width=width)

__all__ = [
    "NormalData",
    "RenderPageType",
    "render_png_from_template",
]

# —— 测试展示函数 —— #
def test_render_template_show():
    import io
    data = {
        "user_name": "夜澄シロShiro",
        "avatar_url": "https://i2.hdslb.com/bfs/face/f7330a03906fb612f6e6812b67b7885d27899781.jpg",
        "time": "2025-02-01 11:30",
        "title": "测试动态标题",
        "link": "https://www.example.com",
        "content": "シロ的开播通知群号：1036401996\n只用于开播提醒，不开放聊天哦！！\n进群后「昵称_UID」\n\n 此皮为菜菜爱吃饭ovo的量贩皮。",
        "image_urls": [
            "https://i0.hdslb.com/bfs/live/new_room_cover/754eaf70cb673a8e90220e8df9947b2114650711.jpg",
            "https://i0.hdslb.com/bfs/live/new_room_cover/754eaf70cb673a8e90220e8df9947b2114650711.jpg"
        ]  # 可以为空列表
    }

    png_bytes = render_png_from_template(RenderPageType.NORMAL, data, width=700)
    img = Image.open(io.BytesIO(png_bytes))
    img.show()
    print("✅ 渲染完成（支持多图）")


if __name__ == "__main__":
    test_render_template_show()
