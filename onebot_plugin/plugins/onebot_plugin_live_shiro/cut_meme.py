from PIL import Image
from pathlib import Path
import shutil
import aiohttp
import py7zr
import os

from nonebot import on_shell_command, on_command
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, Message, MessageSegment, GroupMessageEvent
from nonebot.rule import to_me, ArgumentParser
from nonebot.params import ShellCommandArgs
from nonebot.permission import SUPERUSER

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}

def extract_images_and_files(msg: Message):
    results = []

    for seg in msg:
        # 1. 图片 segment
        if seg.type == "image":
            url = seg.data.get("url") or seg.data.get("file")
            if url:
                results.append({
                    "type": "image",
                    "url": url
                })
            continue

        # 2. 文件 segment 且是图片类型
        if seg.type == "file":
            file_name = seg.data.get("name", "").lower()
            if any(file_name.endswith(ext) for ext in IMAGE_EXTS):
                file_id = seg.data.get("file_id")
                if file_id:
                    results.append({
                        "type": "file",
                        "file_name": file_name,
                        "file_id": file_id
                    })

    return results

async def download_images(bot: Bot, message_id: int, items: list):
    """
    items：extract_images_and_files() 返回的对象数组
    bot：当前 Bot 实例
    return：下载后的文件路径数组（Path 对象列表）
    """

    # 目标目录 ./cache/cut_meme/{message_id}/
    base_dir = Path("./cache/cut_meme") / str(message_id)

    # 若存在则删除
    if base_dir.exists():
        shutil.rmtree(base_dir)

    # 创建目录
    base_dir.mkdir(parents=True, exist_ok=True)

    saved_paths = []  # 保存最终返回的文件路径列表

    async with aiohttp.ClientSession() as session:
        for index, item in enumerate(items):

            # 1. image segment 下载 URL 图片
            if item["type"] == "image":
                url = item["url"]
                async with session.get(url) as resp:
                    img_data = await resp.read()

                file_path = base_dir / f"img_{index}.jpg"
                file_path.write_bytes(img_data)
                saved_paths.append(file_path)
                continue

            # 2. file segment —— 使用 file_id 下载真实图片
            if item["type"] == "file":
                file_id = item["file_id"]
                file_name = item["file_name"]

                # 通过 OneBot API 获取下载链接
                file_info = await bot.call_api("get_file", file_id=file_id)
                download_url = file_info["url"]

                async with session.get(download_url) as resp:
                    file_data = await resp.read()

                file_path = base_dir / file_name
                file_path.write_bytes(file_data)
                saved_paths.append(file_path)

    return saved_paths

async def split_images(message_id: int, image_paths: list, rows: int = 6, cols: int = 4):
    """
    image_paths: Path对象列表
    rows, cols: 拆分行列
    """
    # 创建临时拆分目录
    temp_dir = Path("./cache/cut_meme") / f"{message_id}_split"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)

    split_count = 0
    for img_path in image_paths:
        img = Image.open(img_path)
        w, h = img.size
        tile_w = w // cols
        tile_h = h // rows

        for r in range(rows):
            for c in range(cols):
                box = (c*tile_w, r*tile_h, (c+1)*tile_w, (r+1)*tile_h)
                tile = img.crop(box)
                split_filename = temp_dir / f"{img_path.stem}_r{r}_c{c}.png"
                tile.save(split_filename)
                split_count += 1

    # 打包成 7z 文件
    archive_path = Path("./cache/cut_meme") / f"{message_id}.7z"
    if archive_path.exists():
        archive_path.unlink()  # 删除已存在文件

    with py7zr.SevenZipFile(archive_path, 'w') as archive:
        archive.writeall(temp_dir, arcname='.')

    return archive_path

async def upload_group_file(bot: Bot, group_id: int, file_path: Path):
    """
    上传本地文件到群文件

    :param bot: Bot 实例
    :param group_id: 群号
    :param file_path: 本地文件路径
    """
    file_path = Path(file_path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    # 调用 OneBot v11 API 上传群文件
    await bot.call_api(
        "upload_group_file",
        group_id=group_id,
        file=str(file_path.resolve()),  # 使用绝对路径
        name=file_path.name
    )

def remove_cut_meme_cache(message_id: int):
    cache_dir = Path("./cache/cut_meme") / str(message_id)
    if cache_dir.exists() and cache_dir.is_dir():
        shutil.rmtree(cache_dir)

    cache_dir = Path("./cache/cut_meme") / f"{str(message_id)}_split"
    if cache_dir.exists() and cache_dir.is_dir():
        shutil.rmtree(cache_dir)

    archive_file = Path("./cache/cut_meme") / f"{str(message_id)}.7z"
    if archive_file.exists() and archive_file.is_file():
        archive_file.unlink()

parser = ArgumentParser()
parser.add_argument("-c", "--cols", type=int, default=4, help="表情包列数，默认为4")
parser.add_argument("-r", "--rows", type=int, default=6, help="表情包行数，默认为6")

cut_meme_command = on_shell_command("cut_meme", rule=to_me(), parser=parser)
@cut_meme_command.handle()
async def handle_cut_meme(bot: Bot, event: MessageEvent, shell_args = ShellCommandArgs()):
    if not isinstance(event, GroupMessageEvent):
        await cut_meme_command.finish(Message([
            MessageSegment.text("表情包拆分功能仅支持群聊使用喵~")
        ]))

    try:
        arg_dict = vars(shell_args)
        if "status" in arg_dict:
            await cut_meme_command.finish(
                Message([
                    MessageSegment.reply(event.message_id),
                    MessageSegment.text(arg_dict["message"])
                ])
            )

        message_contents = extract_images_and_files(event.message)

        if not message_contents:
            if event.reply:
                message_contents = extract_images_and_files(event.reply.message)

            if not message_contents:
                await cut_meme_command.finish(Message([
                    MessageSegment.reply(event.message_id),
                    MessageSegment.text("请给我一张图，引用或直接发送都可以喵~")
                ]))

        image_paths = await download_images(bot, event.message_id, message_contents)
        archive_path = await split_images(event.message_id, image_paths, rows=arg_dict["rows"], cols=arg_dict["cols"])
        await upload_group_file(bot, event.group_id, archive_path)

        await cut_meme_command.finish(
            Message([
                MessageSegment.reply(event.message_id),
                MessageSegment.text("表情包拆分完成，已上传到群文件喵~")
            ])
        )
    finally:
        remove_cut_meme_cache(event.message_id)

clear_meme_cache_command = on_command("clear_cut_meme_cache", rule=to_me(), permission=SUPERUSER)
@clear_meme_cache_command.handle()
async def handle_clear_meme_cache(event: MessageEvent):
    base_cache_dir = Path("./cache/cut_meme")
    if base_cache_dir.exists() and base_cache_dir.is_dir():
        shutil.rmtree(base_cache_dir)
        await clear_meme_cache_command.finish(
            Message([
                MessageSegment.reply(event.message_id),
                MessageSegment.text("表情包缓存已清理喵~")
            ])
        )
    else:
        await clear_meme_cache_command.finish(
            Message([
                MessageSegment.reply(event.message_id),
                MessageSegment.text("当前没有表情包缓存喵~")
            ])
        )
