import os
import stat
import subprocess
import sys
from pathlib import Path

from nonebot import logger, on_command
from nonebot.adapters import Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

# 注册命令，仅允许超级用户使用，避免安全风险
install_pip = on_command("install_pip", rule=to_me(), permission=SUPERUSER, block=True)

@install_pip.handle()
async def handle_install(args: Message = CommandArg()):
    # 1. 获取参数（包名）
    pkg_names = args.extract_plain_text().strip()
    
    if not pkg_names:
        await install_pip.finish("❌ 请提供需要安装的包名，例如：/install_pip numpy pandas")

    # 2. 定义目录和文件路径
    # 使用 absolute() 获取绝对路径，确保执行时路径正确
    cache_dir = Path("./cache").absolute() 
    script_path = cache_dir / "install_pip.sh"
    
    # 确保 cache 目录存在
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)

    # 3. 如果文件存在则删除 (满足需求: 先删除再创建)
    if script_path.exists():
        try:
            script_path.unlink()
            logger.info(f"Old script removed: {script_path}")
        except Exception as e:
            await install_pip.finish(f"❌ 删除旧脚本失败: {e}")

    # 4. 构建命令内容
    # 使用 sys.executable 确保安装到当前 Bot 运行的 Python 环境中
    current_python = sys.executable
    proxy_url = "http://127.0.0.1:10808"
    
    # 拼装核心命令: python -m pip install <pkgs> --proxy <url>
    pip_command = f'"{current_python}" -m pip install {pkg_names} --proxy {proxy_url}'
    
    # SH 脚本内容
    sh_content = (
        "#!/bin/bash\n"
        "echo 'Starting pip installation...'\n"
        f"echo 'Command: {pip_command}'\n"
        f"{pip_command}\n"
        "echo 'Installation finished.'\n"
    )

    # 5. 写入文件
    try:
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(sh_content)
    except Exception as e:
        await install_pip.finish(f"❌ 写入脚本失败: {e}")

    # 6. 赋予执行权限 (chmod +x)
    try:
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)
    except Exception as e:
        await install_pip.finish(f"❌ 修改权限失败: {e}")

    # 7. 以独立模式运行脚本
    try:
        # 使用 Popen 而不是 run/call，这样不会阻塞 Bot 响应
        # stdout 和 stderr 重定向，防止向终端大量输出干扰 Bot 日志（根据需要调整）
        subprocess.Popen(
            [str(script_path)], 
            shell=False, # 因为我们直接执行的是可执行文件
            cwd=str(cache_dir), # 在 cache 目录下执行
            stdout=subprocess.DEVNULL, # 或者重定向到日志文件
            stderr=subprocess.DEVNULL
        )
        
        await install_pip.finish(
            f"✅ 脚本已生成并后台运行。\n"
            f"📄 路径: {script_path}\n"
            f"🔧 指令: {pip_command}"
        )
        
    except Exception as e:
        await install_pip.finish(f"❌ 运行脚本失败: {e}")