from enum import Enum
from io import BytesIO
from pathlib import Path
from typing import Optional, TypedDict

from jinja2 import Environment, FileSystemLoader
from PIL import Image
from .browser import browser_manager  # 修改为单例管理器

current_dir = Path(__file__).resolve().parent
env = Environment(loader=FileSystemLoader(current_dir / "templates"))


class NormalData(TypedDict):
    user_name: str
    avatar_url: str
    time: str
    title: str
    link: str
    content: str
    image_urls: Optional[list[str]]

class ForwardData(TypedDict):
    user_name: str
    avatar_url: str
    time: str
    title: str
    content: str
    forwarded_card_url: str

class RenderPageType(Enum):
    NORMAL = "normal.html"
    FORWARD = "forward.html"


def crop_transparent_edges(img: Image.Image, border: int = 10) -> Image.Image:
    """裁剪透明边缘"""
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


async def _render_png_from_html(html_str: str, width: int = 800) -> bytes:
    """渲染 HTML → PNG 截图"""
    # 使用单例管理器安全获取浏览器
    browser = await browser_manager.get_browser()
    page = await browser.new_page(
        viewport={"width": width, "height": 2000},
        device_scale_factor=2,
    )
    await page.set_content(html_str)
    await page.wait_for_load_state("networkidle")

    # 仅截 content-wrapper
    clip = None
    content = await page.query_selector(".content-wrapper")
    if content:
        box = await content.bounding_box()
        if box:
            clip = box

    screenshot = await page.screenshot(
        type="png",
        omit_background=True,
        clip=clip,
    )
    await page.close()

    img = Image.open(BytesIO(screenshot))
    img = crop_transparent_edges(img, border=10)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def render_png_from_template(render_type: RenderPageType, data: dict, width: int = 800) -> bytes:
    """从模板数据生成 PNG"""
    if render_type == RenderPageType.NORMAL:
        # 保证 content 是字符串，替换换行符
        data["content"] = data.get("content", "") or ""
        data["content"] = data["content"].replace("\r\n", "\n").replace("\r", "\n")
        # 过滤空图片链接
        data["image_urls"] = [url for url in data.get("image_urls", []) if url]

    elif render_type == RenderPageType.FORWARD:
        # 保证 content 是字符串
        data["content"] = data.get("content", "") or ""
        data["content"] = data["content"].replace("\r\n", "\n").replace("\r", "\n")
        # forwarded_card_url 必须存在，否则给个空字符串兜底
        data["forwarded_card_url"] = data.get("forwarded_card_url", "")

    else:
        raise ValueError(f"Unsupported render_type: {render_type}")

    template = env.get_template(render_type.value)
    html_str = template.render(data)
    return await _render_png_from_html(html_str, width)
