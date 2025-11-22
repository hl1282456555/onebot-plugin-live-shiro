from nonebot import on_command, logger
from nonebot.rule import to_me
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Message, MessageSegment, MessageEvent

import subprocess
import os
import asyncio

repo_path = os.path.expanduser("~/onebot-plugin-live-shiro")
script_path = os.path.expanduser("~/napcat_onebot/update_self.sh")

def pull_latest_repo(repo_path, branch="main"):
    """
    拉取指定仓库最新代码，返回执行结果
    """
    try:
        # 确保仓库路径存在
        if not os.path.isdir(repo_path):
            return False, f"仓库路径不存在: {repo_path}"

        # 执行 git pull
        result = subprocess.run(
            ["git", "pull", "origin", branch],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def new_commit_count(repo_path, branch="main"):
    # 拉取远程信息
    subprocess.run(["git", "fetch"], cwd=repo_path)

    # 统计本地与远程的差异 commit 数
    result = subprocess.run(
        ["git", "rev-list", f"HEAD..origin/{branch}", "--count"],
        cwd=repo_path,
        stdout=subprocess.PIPE,
        text=True
    )

    count = int(result.stdout.strip())
    return count

async def run_script_detached(script_path: str):
    # 使用 asyncio 异步启动脱离式进程
    # stdout/stderr 指向 DEVNULL，避免阻塞
    await asyncio.create_subprocess_exec(
        "bash", script_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        preexec_fn=os.setsid  # 关键：让子进程脱离父进程
    )

update_self_command = on_command("update_self", rule=to_me(), permission=SUPERUSER)

@update_self_command.handle()
async def handle_update_self(bot, event: MessageEvent):
    commit_count = new_commit_count(repo_path)
    if commit_count <= 0:
        await update_self_command.finish(message=Message([
                MessageSegment.reply(event.message_id),
                MessageSegment.text("主人，已经是最新版本了喵~")
            ]))

    success, output = pull_latest_repo(repo_path)
    if not success:
        await update_self_command.finish(message=Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(f"更新失败！\n错误信息：\n{output}")
        ]))

    await update_self_command.send(message=Message([
        MessageSegment.reply(event.message_id),
        MessageSegment.text(f"正在更新代码，请稍等片刻喵~")
    ]))

    asyncio.create_task(run_script_detached(script_path))
