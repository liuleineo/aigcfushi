import os

# 豆包API配置
DOUBAO_API_KEY = "你的key"
DOUBAO_API_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
DOUBAO_MODEL = "doubao-seedream-4-5-251128"

# 生成图片配置
IMAGE_WIDTH = 2048  # 2k高清画质
IMAGE_HEIGHT = 2048  # 3:4比例
IMAGE_COUNT = 1  # 每次生成2张图片

# 输出目录
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

#填入key后，记得把example.config.py改为config.py

