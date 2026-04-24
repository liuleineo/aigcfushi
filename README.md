# 服装AI创作画布

基于豆包 Seedream 4.5 大模型的服装 AI 换装创作工具，支持产品图+模特图智能融合生成，以及多种图片后处理功能。

## 功能特性

### 核心功能
- **AI 换装生成**：将产品图中的服装精准穿到模特身上，商业摄影级画质
- **多图参考**：支持产品图 + 模特图 + 姿势参考图 + 场景参考图组合生成
- **4K 高清输出**：使用 `b64_json` 无损传输，4K 分辨率，无水印

### 右键菜单后处理
- **微调图片**：自定义提示词对图片进行精准调整
- **生成正面图**：生成模特正面视角展示图
- **生成侧面图**：生成模特侧面视角展示图
- **生成白底图**：去除背景生成白底商品展示图
- **生成透明图**：去除背景生成透明背景商品图
- **生成线稿图**：生成服装专业线稿图
- **生成平铺图**：生成服装平铺俯视展示图
- **生成搭配图**：生成穿搭搭配推荐图

### 交互功能
- 左侧图库：选择文件夹加载图片，拖放到9宫格
- 9宫格画布：双击选择本地图片，右键移除图片，单击选中
- 结果展示：点击图片全屏预览，右键菜单后处理
- 生成占位：生成时显示"正在生成..."占位，新图片插到最前面

## 环境要求

- Python 3.10+
- 依赖库：PyQt5、requests

## 快速开始

### 1. 安装依赖

```bash
cd aigcfushi
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows
pip install PyQt5 requests
```

### 2. 配置 API Key

编辑 `config.py`，填入你的豆包 API Key：

```python
DOUBAO_API_KEY = "你的API Key"
```

API Key 获取方式：
1. 注册 [火山引擎](https://www.volcengine.com/) 账号
2. 开通豆包大模型服务
3. 在控制台创建推理接入点，获取 API Key

### 3. 运行

```bash
python main.py
```

## 使用说明

1. **加载图片**：点击左侧"选择文件夹"按钮，选择包含服装/模特图片的文件夹
2. **拖放图片**：从左侧图库拖拽图片到右侧9宫格对应区域，或双击9宫格选择本地图片
3. **选中图片**：在产品图和模特图9宫格中，单击已放入的图片进行选中（蓝色边框高亮）
4. **生成图片**：至少选中一张产品图和一张模特图，点击"立即生成"
5. **查看结果**：点击生成的图片可全屏预览，右键可进行后处理操作
6. **移除图片**：右键9宫格中的图片，选择"移除图片"

## 项目结构

```
aigcfushi/
├── main.py            # 主程序（UI + 业务逻辑）
├── config.py          # 配置文件（API Key、模型、参数）
├── build_mac.sh       # macOS 打包脚本
├── build_win.bat      # Windows 打包脚本
├── output/            # 生成的图片输出目录
├── dev-log/           # 开发日志
├── 界面.png            # 界面截图
└── venv/              # Python 虚拟环境
```

## 打包部署

### macOS

```bash
pip install pyinstaller
bash build_mac.sh
# 产物在 dist/女装AI创作画布.app
```

### Windows

```bash
pip install pyinstaller
build_win.bat
# 产物在 dist\女装AI创作画布.exe
```

> 注意：PyInstaller 不支持跨平台打包，需在对应系统上执行。

## 配置说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `DOUBAO_API_KEY` | - | 豆包 API 密钥（必填） |
| `DOUBAO_API_URL` | 火山引擎 API 地址 | API 请求地址 |
| `DOUBAO_MODEL` | `doubao-seedream-4-5-251128` | 使用的模型版本 |
| `IMAGE_WIDTH` | 2048 | 生成图片宽度 |
| `IMAGE_HEIGHT` | 2048 | 生成图片高度 |
| `IMAGE_COUNT` | 1 | 每次生成图片数量 |
| `OUTPUT_DIR` | `./output` | 图片输出目录 |

## 技术栈

- **UI 框架**：PyQt5
- **AI 模型**：豆包 Seedream 4.5（火山引擎）
- **异步生成**：QThread 后台线程，避免 UI 卡顿
- **图片传输**：base64 编码输入 + b64_json 无损输出
- **图片分辨率**：4K（最大 4096×4096）

## License

MIT
