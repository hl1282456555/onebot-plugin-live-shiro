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

    except Exception as e:
        await install_pip.finish(f"❌ 运行脚本失败: {e}")
    
    await install_pip.finish(
        f"✅ 脚本已生成并后台运行。\n"
        f"📄 路径: {script_path}\n"
        f"🔧 指令: {pip_command}"
    )

# 注册命令 /install_nb
install_nb = on_command("install_nb", permission=SUPERUSER, block=True)

@install_nb.handle()
async def handle_nb_install(args: Message = CommandArg()):
    # 1. 获取插件名称
    plugin_name = args.extract_plain_text().strip()
    
    if not plugin_name:
        await install_nb.finish("❌ 请提供插件名称，例如：/install_nb nonebot-plugin-alconna")

    # 2. 获取当前工作目录 (项目根目录)
    # 假设你是在项目根目录下运行的 nb run，os.getcwd() 就是正确的
    cwd = os.getcwd()

    # 3. 准备环境变量 (关键步骤)
    # 我们复制当前系统的环境变量，并强制注入代理设置
    # 因为 nb plugin install 内部调用 pip，pip 会读取这些环境变量
    env = os.environ.copy()
    env["HTTP_PROXY"] = "http://127.0.0.1:10808"
    env["HTTPS_PROXY"] = "http://127.0.0.1:10808"
    
    # 确保 PATH 包含当前 Python 环境的 bin 目录，以便能找到 'nb' 命令
    # 如果是在 venv 下运行，sys.prefix 就是 venv 的路径
    if sys.platform == "win32":
        bin_dir = os.path.join(sys.prefix, "Scripts")
    else:
        bin_dir = os.path.join(sys.prefix, "bin")
    
    # 将 bin 目录加到 PATH 最前面，确保使用的是当前环境的 nb
    env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")

    # 4. 构建命令
    # 使用 shell=True 允许直接运行 nb 命令，就像在终端输入一样
    cmd = f"nb plugin install {plugin_name}"

    try:
        # 5. 独立运行 (非阻塞)
        subprocess.Popen(
            cmd,
            shell=True,
            cwd=cwd,      # 在当前项目目录下执行
            env=env,      # 使用带有代理和正确PATH的环境
            stdout=subprocess.DEVNULL, # 隐藏输出，或者重定向到文件
            stderr=subprocess.DEVNULL
        )

    except Exception as e:
        await install_nb.finish(f"❌ 启动安装进程失败: {e}")
    
    await install_nb.finish(
        f"✅ 已开始安装插件: {plugin_name}\n"
        f"🚀 命令: {cmd}\n"
        f"⚙️ 模式: 独立进程运行 (带代理)\n\n"
        f"⚠️ 注意: 安装完成后，nb-cli 会修改配置文件，Bot 将会自动重启加载新插件。"
    )
