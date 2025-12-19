import json
import base64
import asyncio

from pathlib import Path

from typing import Optional
from nonebot import on_command, get_driver, logger
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters import Bot
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from bilibili_api import Credential, login_v2
from nonebot_plugin_apscheduler import scheduler

bili_credential = Credential()

driver = get_driver()

def build_bytes_image(img_bytes: bytes) -> MessageSegment:
    # 将bytes转换为base64字符串
    b64_str = base64.b64encode(img_bytes).decode()
    # 构造base64 URI
    uri = f"base64://{b64_str}"
    # 返回图片消息段
    return MessageSegment.image(uri)

def load_cookies(file_path: str = "./cache/bili_cookies.txt") -> dict:
    """
    加载指定路径的JSON文件为字典

    如果文件不存在、读取失败或解析失败，返回空字典
    """
    try:
        path = Path(file_path)
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass  # 静默处理所有异常
    return {}

def save_dict_to_json(data: dict, file_path: str = "./cache/bili_cookies.txt", ensure_ascii: bool = False, indent: int = 2) -> bool:
    """
    将字典保存为JSON文件
    
    参数:
        data: 要保存的字典数据
        file_path: 文件路径
        ensure_ascii: 是否确保ASCII编码，中文建议设为False
        indent: 缩进空格数
    
    返回:
        保存成功返回True，失败返回False
    """
    try:
        path = Path(file_path)
        
        # 创建父目录（如果不存在）
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入JSON文件
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        
        return True
        
    except TypeError as e:
        logger.error(f"数据类型错误，无法序列化为JSON: {e}")
        return False
    except IOError as e:
        logger.error(f"文件IO错误: {e}")
        return False
    except Exception as e:
        logger.error(f"保存文件时发生未知错误: {e}")
        return False

async def check_bili_credential_validity(bot: Bot) -> None:
    global bili_credential

    refreshed_credential = False
    try:
        if await bili_credential.check_refresh():
            await bili_credential.refresh()
            refreshed_credential = True
    except Exception as err:
        for user in driver.config.superusers:
            await bot.send_private_msg(user_id=user, message=MessageSegment.text(f'检测到Credential失效，但是刷新失败喵~\n{err}'))
        return
    
    if refreshed_credential:
        save_cookies_success = save_dict_to_json(bili_credential.get_cookies())
        for user in driver.config.superusers:
            await bot.send_private_msg(user_id=user, message=MessageSegment.text(f'检测到Credential失效，已成功刷新喵~\n保存到文件 [{"成功" if save_cookies_success else "失败"}]'))

async def bilibili_login_bot_connect_handler(bot: Bot) -> Optional[Message]:
    global bili_credential
    cookies = load_cookies()
    if cookies:
        bili_credential = Credential.from_cookies(cookies)
    else:
        qr_login = login_v2.QrCodeLogin()
        await qr_login.generate_qrcode()
        qr_pic = qr_login.get_qrcode_picture()

        for user in driver.config.superusers:
            await bot.send_private_msg(user_id=user, message=Message([
                MessageSegment.text("请扫码登陆B站！"),
                build_bytes_image(qr_pic.content)
            ]))

        for _ in range(180):
            if qr_login.has_done():
                break
            await qr_login.check_state()
            await asyncio.sleep(1)
        else:
            return Message([
                MessageSegment.text("B站扫码登陆超时，请通过命令重试喵~")
            ])

        bili_credential = qr_login.get_credential()
        if not save_dict_to_json(bili_credential.get_cookies()):
            logger.error("保存B站cookies失败！")

    await check_bili_credential_validity(bot)

    if not scheduler.get_job("job_check_bili_credential_validity"):
        scheduler.add_job(
            check_bili_credential_validity,
            "interval",
            days=1,
            id="job_check_bili_credential_validity",
            kwargs={"bot": bot}
        )

    return Message([
        MessageSegment.text("已成功获取B站验证信息喵~")
    ])

bili_login_command = on_command("bili_login", rule=to_me(), permission=SUPERUSER)
@bili_login_command.handle()
async def handle_bili_login_command(bot):
    global bili_credential
    if bili_credential and bili_credential.check_valid():
        await bili_login_command.finish(message=MessageSegment.text("B站当前已经登陆，请勿重复操作喵~"))
    else:
        qr_login = login_v2.QrCodeLogin()
        await qr_login.generate_qrcode()
        qr_pic = qr_login.get_qrcode_picture()

        await bot.send(message=Message([
                MessageSegment.text("请扫码登陆B站！"),
                build_bytes_image(qr_pic.content)
            ]))

        for _ in range(180):
            if qr_login.has_done():
                break
            await qr_login.check_state()
            await asyncio.sleep(1)
        else:
            await bili_login_command.finish(message=MessageSegment.text("B登陆登陆失败，请重试喵~"))

        bili_credential = qr_login.get_credential()
        save_dict_to_json(bili_credential.get_cookies())
        await bili_login_command.finish(message=MessageSegment.text("B站成功登陆喵~"))

bili_get_credential_command = on_command("bili_get_credential", rule=to_me(), permission=SUPERUSER)
@bili_get_credential_command.handle()
async def _():
    global bili_credential
    if bili_credential and bili_credential.check_valid():
        await bili_get_credential_command.finish(message=MessageSegment.text(f"B站当前Credential有效喵~\n{bili_credential.get_cookies()}"))
    else:
        await bili_get_credential_command.finish(message=MessageSegment.text("B站当前Credential无效喵~"))

__all__ = ["bili_credential"]