from PIL import Image

from nonebot import on_shell_command
from nonebot.adapters.onebot.v11 import MessageEvent, Message, MessageSegment
from nonebot.rule import to_me, ArgumentParser
from nonebot.params import ShellCommandArgs

parser = ArgumentParser()
parser.add_argument("-c", "--cols", type=int, default=4, help="表情包列数，默认为4")
parser.add_argument("-r", "--rows", type=int, default=6, help="表情包行数，默认为4")

cut_meme_command = on_shell_command("cut_meme", rule=to_me(), parser=parser)
@cut_meme_command.handle()
async def handle_cut_meme(event: MessageEvent, shell_args = ShellCommandArgs()):
    arg_dict = vars(shell_args)
    await cut_meme_command.finish(
        Message([
            MessageSegment.reply(event.message_id),
            MessageSegment.text(f"接收到参数{arg_dict}")
        ])
    )

# from PIL import Image
# import os

# def split_image_to_grid(image_path, rows, cols, output_dir="output"):
#     """
#     将图片按照指定行列拆分成小图片。
    
#     :param image_path: 输入图片路径
#     :param rows: 拆分的行数
#     :param cols: 拆分的列数
#     :param output_dir: 输出文件夹
#     """
#     # 打开图片
#     img = Image.open(image_path)
#     img_width, img_height = img.size
    
#     # 每个小格的宽高
#     tile_width = img_width // cols
#     tile_height = img_height // rows
    
#     # 创建输出文件夹
#     os.makedirs(output_dir, exist_ok=True)
    
#     count = 0
#     for row in range(rows):
#         for col in range(cols):
#             left = col * tile_width
#             upper = row * tile_height
#             right = left + tile_width
#             lower = upper + tile_height
            
#             # 裁剪图片
#             cropped_img = img.crop((left, upper, right, lower))
            
#             # 保存图片
#             output_path = os.path.join(output_dir, f"tile_{row}_{col}.png")
#             cropped_img.save(output_path)
#             count += 1
    
#     print(f"已生成 {count} 张图片，保存在 {output_dir} 文件夹中。")

# # 示例调用
# split_image_to_grid(R"C:\Users\Administrator\Pictures\77689C4DABB29FBB9B1D7B03A30FEA37.png", 4, 6)  # 将 example.jpg 拆成 4x4 的棋盘格

