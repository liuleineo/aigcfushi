import sys
import os
import requests
import base64
import time
import uuid
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QGridLayout, QPushButton, QLabel, QFileDialog, QScrollArea,
    QMenu, QAction, QMessageBox, QInputDialog, QSizePolicy, QDialog
)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QFont, QColor, QDesktop
from PyQt5.QtCore import Qt, QMimeData, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QDrag

# 导入配置
from config import DOUBAO_API_KEY, DOUBAO_API_URL, DOUBAO_MODEL, IMAGE_WIDTH, IMAGE_HEIGHT, IMAGE_COUNT

class ImageCanvas(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.image_path = None
        self.is_selected = False
        self.setFixedSize(80, 80)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setText('拖放')
        self.label.setStyleSheet('border: 1px dashed #aaa; font-size: 10px; color: #999;')
        self.label.setMinimumSize(76, 76)
        layout.addWidget(self.label)

        # 右键菜单（移除图片）
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._showContextMenu)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            self.setImage(path)
    
    def setImage(self, path):
        self.image_path = path
        self.is_selected = False
        self._updateDisplay()

    def clear(self):
        self.image_path = None
        self.is_selected = False
        self.label.clear()
        self.label.setText('拖放')
        self.label.setStyleSheet('border: 1px dashed #aaa; font-size: 10px; color: #999;')

    def _updateDisplay(self):
        """更新显示，包含选中对号"""
        if not self.image_path:
            return
        pixmap = QPixmap(self.image_path)
        if pixmap.isNull():
            return
        scaled_pixmap = pixmap.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if self.is_selected:
            # 绘制对号覆盖层
            canvas = QPixmap(scaled_pixmap.size())
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.drawPixmap(0, 0, scaled_pixmap)
            # 半透明绿色遮罩
            painter.fillRect(canvas.rect(), QColor(0, 180, 80, 60))
            # 右下角绿色圆形背景
            check_size = 22
            cx = canvas.width() - check_size // 2 - 3
            cy = canvas.height() - check_size // 2 - 3
            painter.setBrush(QColor(0, 180, 80))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(cx - check_size // 2, cy - check_size // 2, check_size, check_size)
            # 白色对号
            painter.setPen(QPen(QColor(255, 255, 255), 2.5))
            painter.setFont(QFont('Arial', 12, QFont.Bold))
            painter.drawText(cx - 6, cy + 5, '✓')
            painter.end()
            self.label.setPixmap(canvas)
            self.label.setStyleSheet('border: 2px solid #00b450;')
        else:
            self.label.setPixmap(scaled_pixmap)
            self.label.setStyleSheet('border: 1px solid #ccc;')

    def mouseDoubleClickEvent(self, event):
        """双击选择本地图片"""
        if event.button() == Qt.LeftButton:
            file_path, _ = QFileDialog.getOpenFileName(
                self, '选择图片', '',
                '图片文件 (*.png *.jpg *.jpeg *.bmp *.webp)'
            )
            if file_path:
                self.setImage(file_path)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.image_path:
            self.is_selected = not self.is_selected
            self._updateDisplay()

    def _showContextMenu(self, position):
        """右键菜单 - 移除图片"""
        if not self.image_path:
            return
        menu = QMenu(self)
        remove_action = QAction('移除图片', self)
        remove_action.triggered.connect(self.clear)
        menu.addAction(remove_action)
        menu.exec_(self.mapToGlobal(position))

class GalleryItem(QLabel):
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.image_path = image_path
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(88, 88, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
        self.setFixedSize(90, 90)
        self.setStyleSheet('border: 1px solid #eee; background: #f5f5f5; margin: 0px; padding: 0px;')
        self.setAlignment(Qt.AlignCenter)
        self.setContentsMargins(0, 0, 0, 0)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            mime_data = QMimeData()
            mime_data.setUrls([QUrl.fromLocalFile(self.image_path)])
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec_(Qt.CopyAction)

class PreviewDialog(QDialog):
    """窗口大小预览图片对话框"""
    def __init__(self, image_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle('图片预览')
        self.setStyleSheet('background: #1a1a1a;')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        label = QLabel()
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            # 以父窗口大小为基准缩放图片
            if parent:
                max_w = parent.width() - 20
                max_h = parent.height() - 20
            else:
                screen = QApplication.primaryScreen().geometry()
                max_w = screen.width() - 20
                max_h = screen.height() - 20
            scaled = pixmap.scaled(max_w, max_h,
                                   Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled)
            # 根据图片大小调整对话框尺寸
            self.resize(scaled.width() + 20, scaled.height() + 20)
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Escape, Qt.Key_Space, Qt.Key_Return):
            self.close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.close()


class ResultImageLabel(QLabel):
    """可点击的结果图片标签"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_path = None
        self.on_left_click = None  # 回调函数

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.on_left_click:
            self.on_left_click()
        elif event.button() == Qt.RightButton:
            # 让右键菜单正常工作
            super().mousePressEvent(event)

class GenerateThread(QThread):
    """后台线程调用豆包API生成图片"""
    result_ready = pyqtSignal(list)   # 参数: [image_path, ...]
    error_occurred = pyqtSignal(str)  # 参数: error_message

    def __init__(self, prompt, images, output_dir, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.images = images
        self.output_dir = output_dir

    def run(self):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DOUBAO_API_KEY}"
            }
            payload = {
                "model": DOUBAO_MODEL,
                "prompt": self.prompt,
                "image": self.images,
                "sequential_image_generation": "disabled",
                "response_format": "b64_json",
                "size": "4K",
                "stream": False,
                "watermark": False
            }
            resp = requests.post(DOUBAO_API_URL, headers=headers, json=payload, timeout=180)
            resp.raise_for_status()
            data = resp.json()

            # 确保输出目录存在
            os.makedirs(self.output_dir, exist_ok=True)

            result_paths = []
            for item in data.get("data", []):
                b64_data = item.get("b64_json")
                if b64_data:
                    # 直接从base64解码保存，避免JPEG压缩损失
                    img_data = base64.b64decode(b64_data)
                    filename = f"gen_{int(time.time())}_{uuid.uuid4().hex[:6]}.png"
                    save_path = os.path.join(self.output_dir, filename)
                    with open(save_path, 'wb') as f:
                        f.write(img_data)
                    result_paths.append(save_path)

            if result_paths:
                self.result_ready.emit(result_paths)
            else:
                self.error_occurred.emit("API未返回图片数据")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"网络请求失败: {str(e)}")
        except Exception as e:
            self.error_occurred.emit(f"生成失败: {str(e)}")

class AICanvasApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('服装AI创作画布')
        self.setGeometry(100, 100, 1200, 800)
        self.output_dir = None          # 输出目录，首次生成时选择
        self.gen_queue = []           # 批量生成队列
        self.gen_total = 0            # 总任务数
        self.gen_current = 0          # 已完成任务数
        self.gen_active = 0           # 当前活跃线程数
        self.max_concurrent = 3       # 最大并发数
        self.active_threads = []      # 活跃线程列表
        self.initUI()
    
    def initUI(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(4)
        main_layout.setContentsMargins(4, 4, 4, 4)
        
        # ===== 左侧图库 =====
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(2)
        left_layout.setContentsMargins(2, 2, 2, 2)

        # 文件夹选择按钮
        #文字提示“ 选择文件夹后，将文件夹下所有图片添加到图库中“
        label = QLabel("选择文件夹后，将文件夹下所有图片添加到图库中")
        label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(label)

        
        select_folder_btn = QPushButton('选择文件夹')
        select_folder_btn.clicked.connect(self.selectFolder)
        left_layout.addWidget(select_folder_btn)
        
        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.gallery_widget = QWidget()
        self.gallery_layout = QGridLayout(self.gallery_widget)
        self.gallery_layout.setSpacing(0)
        self.gallery_layout.setContentsMargins(0, 0, 0, 0)
        self.gallery_layout.setColumnMinimumWidth(0, 90)
        self.gallery_layout.setColumnMinimumWidth(1, 90)
        self.gallery_layout.setColumnMinimumWidth(2, 90)
        # 内容靠顶排列，不随窗口拉伸
        self.gallery_layout.setAlignment(Qt.AlignTop)
        # 禁止 gallery_widget 纵向拉伸
        self.gallery_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.gallery_scroll.setWidget(self.gallery_widget)
        left_layout.addWidget(self.gallery_scroll)
        
        # 左侧面板固定宽度 = 3张图(90*3) + 边距
        left_panel.setFixedWidth(270)
        main_layout.addWidget(left_panel)
        
        # ===== 右侧内容 =====
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(4)
        right_layout.setContentsMargins(4, 4, 4, 4)
        
        # 图片网格区域 - 四个9宫格一行排列
        grid_container = QWidget()
        grid_layout = QHBoxLayout(grid_container)
        grid_layout.setSpacing(8)
        grid_layout.setContentsMargins(0, 0, 0, 0)

        # 产品图网格
        product_grid = QWidget()
        product_grid.setStyleSheet('border: 1px solid #ccc; border-radius: 4px; background: #fff;')
        product_layout = QVBoxLayout(product_grid)
        product_layout.setSpacing(2)
        product_layout.setContentsMargins(4, 4, 4, 4)
        product_label = QLabel('产品图')
        product_label.setAlignment(Qt.AlignCenter)
        product_label.setStyleSheet('font-weight: bold; font-size: 12px; color: #333;')
        product_layout.addWidget(product_label)
        self.product_canvases = []
        product_grid_layout = QGridLayout()
        product_grid_layout.setSpacing(2)
        for i in range(3):
            for j in range(3):
                canvas = ImageCanvas()
                self.product_canvases.append(canvas)
                product_grid_layout.addWidget(canvas, i, j)
        product_layout.addLayout(product_grid_layout)
        grid_layout.addWidget(product_grid)

        # 模特图网格
        model_grid = QWidget()
        model_grid.setStyleSheet('border: 1px solid #ccc; border-radius: 4px; background: #fff;')
        model_layout = QVBoxLayout(model_grid)
        model_layout.setSpacing(2)
        model_layout.setContentsMargins(4, 4, 4, 4)
        model_label = QLabel('模特图')
        model_label.setAlignment(Qt.AlignCenter)
        model_label.setStyleSheet('font-weight: bold; font-size: 12px; color: #333;')
        model_layout.addWidget(model_label)
        self.model_canvases = []
        model_grid_layout = QGridLayout()
        model_grid_layout.setSpacing(2)
        for i in range(3):
            for j in range(3):
                canvas = ImageCanvas()
                self.model_canvases.append(canvas)
                model_grid_layout.addWidget(canvas, i, j)
        model_layout.addLayout(model_grid_layout)
        grid_layout.addWidget(model_grid)

        # 姿势参考图网格
        pose_grid = QWidget()
        pose_grid.setStyleSheet('border: 1px solid #ccc; border-radius: 4px; background: #fff;')
        pose_layout = QVBoxLayout(pose_grid)
        pose_layout.setSpacing(2)
        pose_layout.setContentsMargins(4, 4, 4, 4)
        pose_label = QLabel('姿势参考图')
        pose_label.setAlignment(Qt.AlignCenter)
        pose_label.setStyleSheet('font-weight: bold; font-size: 12px; color: #333;')
        pose_layout.addWidget(pose_label)
        self.pose_canvases = []
        pose_grid_layout = QGridLayout()
        pose_grid_layout.setSpacing(2)
        for i in range(3):
            for j in range(3):
                canvas = ImageCanvas()
                self.pose_canvases.append(canvas)
                pose_grid_layout.addWidget(canvas, i, j)
        pose_layout.addLayout(pose_grid_layout)
        grid_layout.addWidget(pose_grid)
        
        # 场景参考图网格
        scene_grid = QWidget()
        scene_grid.setStyleSheet('border: 1px solid #ccc; border-radius: 4px; background: #fff;')
        scene_layout = QVBoxLayout(scene_grid)
        scene_layout.setSpacing(2)
        scene_layout.setContentsMargins(4, 4, 4, 4)
        scene_label = QLabel('场景参考图')
        scene_label.setAlignment(Qt.AlignCenter)
        scene_label.setStyleSheet('font-weight: bold; font-size: 12px; color: #333;')
        scene_layout.addWidget(scene_label)
        self.scene_canvases = []
        scene_grid_layout = QGridLayout()
        scene_grid_layout.setSpacing(2)
        for i in range(3):
            for j in range(3):
                canvas = ImageCanvas()
                self.scene_canvases.append(canvas)
                scene_grid_layout.addWidget(canvas, i, j)
        scene_layout.addLayout(scene_grid_layout)
        grid_layout.addWidget(scene_grid)
        
        right_layout.addWidget(grid_container)
        
        # 生成按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        generate_btn = QPushButton('立即生成')
        generate_btn.setStyleSheet('background-color: #4a90d9; color: white; padding: 6px 20px; border-radius: 4px; font-weight: bold;')
        generate_btn.clicked.connect(self.generateImage)
        button_layout.addWidget(generate_btn)
        
        batch_generate_btn = QPushButton('批量生成')
        batch_generate_btn.setStyleSheet('background-color: #5cb85c; color: white; padding: 6px 20px; border-radius: 4px; font-weight: bold;')
        batch_generate_btn.clicked.connect(self.batchGenerate)
        button_layout.addWidget(batch_generate_btn)
        
        right_layout.addLayout(button_layout)
        
        # 生成图片展示 - 使用 ScrollArea
        result_scroll = QScrollArea()
        result_scroll.setWidgetResizable(True)
        result_scroll.setMinimumHeight(180)
        self.result_widget = QWidget()
        self.result_layout = QGridLayout(self.result_widget)
        self.result_layout.setSpacing(4)
        self.result_layout.setContentsMargins(2, 2, 2, 2)
        self.result_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        result_scroll.setWidget(self.result_widget)
        right_layout.addWidget(result_scroll, 1)
        
        main_layout.addWidget(right_panel, 3)
        
        self.setCentralWidget(central_widget)
    
    def selectFolder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择图片文件夹')
        if folder:
            self.loadGallery(folder)
    
    def loadGallery(self, folder):
        # 清空现有图库
        for i in reversed(range(self.gallery_layout.count())):
            widget = self.gallery_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        # 加载新图片
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        images = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    images.append(os.path.join(root, file))
        
        # 添加图片到图库
        row = 0
        col = 0
        for image_path in images:
            gallery_item = GalleryItem(image_path)
            self.gallery_layout.addWidget(gallery_item, row, col)
            self.gallery_layout.setRowStretch(row, 0)
            col += 1
            if col >= 3:
                col = 0
                row += 1
    
    def generateImage(self):
        # 获取选中的图片
        selected_product = None
        selected_model = None
        selected_pose = None
        selected_scene = None
        
        for canvas in self.product_canvases:
            if canvas.is_selected:
                selected_product = canvas.image_path
                break
        
        for canvas in self.model_canvases:
            if canvas.is_selected:
                selected_model = canvas.image_path
                break
        
        for canvas in self.pose_canvases:
            if canvas.is_selected:
                selected_pose = canvas.image_path
                break
        
        for canvas in self.scene_canvases:
            if canvas.is_selected:
                selected_scene = canvas.image_path
                break
        
        # 检查必选图片
        if not selected_product or not selected_model:
            QMessageBox.warning(self, '警告', '请至少选择一张产品图和一张模特图')
            return
        
        # 调用豆包生图API生成图片（异步）
        self.callDoubaoAPI(selected_product, selected_model, selected_pose, selected_scene)
    
    def batchGenerate(self):
        # 获取选中的图片
        selected_products = []
        selected_models = []
        selected_poses = []
        selected_scenes = []
        
        for canvas in self.product_canvases:
            if canvas.is_selected:
                selected_products.append(canvas.image_path)
        
        for canvas in self.model_canvases:
            if canvas.is_selected:
                selected_models.append(canvas.image_path)
        
        for canvas in self.pose_canvases:
            if canvas.is_selected:
                selected_poses.append(canvas.image_path)
        
        for canvas in self.scene_canvases:
            if canvas.is_selected:
                selected_scenes.append(canvas.image_path)
        
        # 检查必选图片
        if not selected_products or not selected_models:
            QMessageBox.warning(self, '警告', '请至少选择一张产品图和一张模特图')
            return
        
        # 生成所有组合
        combinations = []
        pose_list = selected_poses if selected_poses else [None]
        scene_list = selected_scenes if selected_scenes else [None]
        for product in selected_products:
            for model in selected_models:
                for pose in pose_list:
                    for scene in scene_list:
                        combinations.append((product, model, pose, scene))
        
        # 确认批量生成
        total = len(combinations)
        reply = QMessageBox.question(
            self, '批量生成确认',
            f'共 {total} 种组合，是否开始批量生成？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply != QMessageBox.Yes:
            return
        
        # 初始化生成队列
        self.gen_queue = combinations
        self.gen_total = total
        self.gen_current = 0
        self._processQueue()
    
    def _processQueue(self):
        """处理批量生成队列，保持最多 max_concurrent 个并发"""
        while self.gen_queue and self.gen_active < self.max_concurrent:
            product, model, pose, scene = self.gen_queue.pop(0)
            self.gen_active += 1
            self._updateBatchTitle()
            self.callDoubaoAPI(product, model, pose, scene, is_batch=True)

    def _updateBatchTitle(self):
        """更新批量生成进度标题"""
        done = self.gen_current
        total = self.gen_total
        active = self.gen_active
        waiting = len(self.gen_queue)
        self.setWindowTitle(f'服装AI创作画布 by 公子鱼 - 批量生成 完成{done}/{total} 执行中{active} 等待{waiting}')

    def getOutputDir(self):
        """获取输出目录，首次使用时让用户选择"""
        if self.output_dir and os.path.isdir(self.output_dir):
            return self.output_dir
        # 提示用户选择输出目录
        folder = QFileDialog.getExistingDirectory(self, '请选择图片保存目录')
        if folder:
            self.output_dir = folder
            return self.output_dir
        return None

    def callDoubaoAPI(self, product_path, model_path, pose_path=None, scene_path=None, is_batch=False):
        """调用豆包生图API，在后台线程中执行"""
        # 获取输出目录
        output_dir = self.getOutputDir()
        if not output_dir:
            if is_batch:
                self.gen_queue.clear()
                self.gen_active = 0
                self.setWindowTitle('服装AI创作画布')
            return

        # 构建prompt - 商业拍摄级画质
        quality_suffix = "，商业摄影级别画质，超高清细节，8K分辨率，专业影棚灯光，锐利清晰，服装纹理细节完整保留，肤色自然真实，画面干净通透"
        prompt = "将图1的服装精准穿在图2的模特身上，完美保留服装的面料质感和纹理细节，保持模特姿态自然、脸部特征和图2一致" + quality_suffix
        if pose_path:
            prompt = "将图1的服装精准穿在图2的模特身上，参考图3的姿势但是不要采用参考图3的人脸，完美保留服装面料质感，保持姿势和服装细节高度一致" + quality_suffix
        if scene_path:
            prompt += "，背景参考图4的场景"

        # 收集图片
        images = []
        for path in [product_path, model_path, pose_path, scene_path]:
            if path:
                images.append(self.imageToBase64(path))

        if len(images) < 2:
            QMessageBox.warning(self, '错误', '至少需要产品图和模特图')
            return None

        # 添加占位标签
        placeholder = self.addPlaceholder()

        # 启动后台线程
        thread = GenerateThread(prompt, images, output_dir)
        thread.result_ready.connect(lambda paths, ph=placeholder, batch=is_batch: self.onGenerateResult(paths, ph, batch))
        thread.error_occurred.connect(lambda msg, ph=placeholder, batch=is_batch: self.onGenerateError(msg, ph, batch))
        self.active_threads.append(thread)
        thread.start()

    def onGenerateResult(self, image_paths, placeholder=None, is_batch=False):
        """生成完成回调"""
        # 移除占位标签
        if placeholder:
            self.result_layout.removeWidget(placeholder)
            placeholder.deleteLater()
        # 将所有生成的图片添加到结果区最前面
        for path in image_paths:
            self._insertResultImageAtFront(path)
        # 重新紧凑排列所有元素
        self._compactItems()
        # 自动打开输出文件夹
        if self.output_dir and os.path.isdir(self.output_dir):
            QDesktop.openUrl(QUrl.fromLocalFile(self.output_dir))
        # 批量模式下处理并发逻辑
        if is_batch:
            self.gen_active -= 1
            self.gen_current += 1
            # 清理已完成的线程
            self.active_threads = [t for t in self.active_threads if t.isRunning()]
            if self.gen_queue:
                self._processQueue()
            elif self.gen_active == 0:
                self.setWindowTitle('服装AI创作画布 - 批量生成完成')
                QMessageBox.information(self, '完成', f'批量生成完成，共 {self.gen_total} 组')

    def onGenerateError(self, error_msg, placeholder=None, is_batch=False):
        """生成出错回调"""
        # 移除占位标签
        if placeholder:
            self.result_layout.removeWidget(placeholder)
            placeholder.deleteLater()
            self._compactItems()
        QMessageBox.warning(self, '生成失败', error_msg)
        # 批量模式下处理并发逻辑
        if is_batch:
            self.gen_active -= 1
            self.gen_current += 1
            # 清理已完成的线程
            self.active_threads = [t for t in self.active_threads if t.isRunning()]
            if self.gen_queue:
                self._processQueue()
            elif self.gen_active == 0:
                self.setWindowTitle('服装AI创作画布 - 批量生成完成')
                QMessageBox.information(self, '完成', f'批量生成完成，共 {self.gen_total} 组')

    def _compactItems(self):
        """紧凑排列结果区元素，新图片排在最前面"""
        cols = 4
        # 收集暂存的新图片（最新生成的）
        new_items = getattr(self, '_pending_images', [])
        self._pending_images = []
        # 收集现有的图片
        existing_items = []
        for i in range(self.result_layout.count()):
            item = self.result_layout.itemAt(i)
            if item and item.widget():
                existing_items.append(item.widget())
        # 移除所有现有元素
        for w in existing_items:
            self.result_layout.removeWidget(w)
        # 新图片在前，旧图片在后，统一紧凑排列
        all_items = new_items + existing_items
        for idx, w in enumerate(all_items):
            r = idx // cols
            c = idx % cols
            self.result_layout.addWidget(w, r, c)

    @staticmethod
    def imageToBase64(image_path):
        """将本地图片转为base64 data URI"""
        with open(image_path, 'rb') as f:
            img_data = f.read()
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {'.jpg': 'jpeg', '.jpeg': 'jpeg', '.png': 'png', '.bmp': 'bmp', '.webp': 'webp'}
        mime = mime_map.get(ext, 'png')
        b64 = base64.b64encode(img_data).decode('utf-8')
        return f"data:image/{mime};base64,{b64}"
    
    def addPlaceholder(self):
        """添加生成中占位标签到最前面"""
        # 收集现有元素
        existing_items = []
        for i in range(self.result_layout.count()):
            item = self.result_layout.itemAt(i)
            if item and item.widget():
                existing_items.append(item.widget())
        # 移除所有现有元素
        for w in existing_items:
            self.result_layout.removeWidget(w)
        # 在 (0,0) 位置插入占位
        placeholder = QLabel()
        placeholder.setFixedSize(300, 400)
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet('border: 1px dashed #4a90d9; background: #f0f4fa; color: #4a90d9; font-size: 13px;')
        placeholder.setText('正在生成...')
        self.result_layout.addWidget(placeholder, 0, 0)
        # 重新排列现有元素到占位之后
        cols = 4
        for idx, w in enumerate(existing_items):
            new_idx = idx + 1
            r = new_idx // cols
            c = new_idx % cols
            self.result_layout.addWidget(w, r, c)
        return placeholder

    def _insertResultImageAtFront(self, image_path):
        """创建结果图片标签并插入到列表最前面（暂存到 self._pending_images）"""
        result_label = ResultImageLabel()
        result_label.setFixedSize(300, 400)  # 3:4比例
        result_label.setStyleSheet('border: 1px solid #ddd; background: #fafafa;')
        result_label.setAlignment(Qt.AlignCenter)
        result_label.image_path = image_path
        result_label.setCursor(Qt.PointingHandCursor)
        result_label.on_left_click = lambda path=image_path: self.showFullScreenImage(path)
        
        # 加载图片 - 填满整个标签区域
        pixmap = QPixmap(image_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(298, 398, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            result_label.setPixmap(scaled_pixmap)

        # 设置右键菜单
        result_label.setContextMenuPolicy(Qt.CustomContextMenu)
        result_label.customContextMenuRequested.connect(lambda pos, label=result_label: self.showContextMenu(pos, label))
        
        # 暂存，后续由 _compactItems 统一排列
        if not hasattr(self, '_pending_images'):
            self._pending_images = []
        self._pending_images.insert(0, result_label)

    def showFullScreenImage(self, image_path):
        """点击图片预览查看"""
        if image_path and os.path.exists(image_path):
            dialog = PreviewDialog(image_path, self)
            dialog.exec_()
    
    def showContextMenu(self, position, label):
        # 显示右键菜单
        menu = QMenu(self)
        
        fine_tune_action = QAction('微调图片', self)
        front_view_action = QAction('生成正面图', self)
        side_view_action = QAction('生成侧面图', self)
        white_background_action = QAction('生成白底图', self)
        transparent_action = QAction('生成透明图', self)
        line_drawing_action = QAction('生成线稿图', self)
        flat_layout_action = QAction('生成平铺图', self)
        matching_action = QAction('生成搭配图', self)
        
        menu.addAction(fine_tune_action)
        menu.addAction(front_view_action)
        menu.addAction(side_view_action)
        menu.addAction(white_background_action)
        menu.addAction(transparent_action)
        menu.addAction(line_drawing_action)
        menu.addAction(flat_layout_action)
        menu.addAction(matching_action)
        
        # 连接菜单项到处理函数
        fine_tune_action.triggered.connect(lambda: self.processImage(label, 'fine_tune'))
        front_view_action.triggered.connect(lambda: self.processImage(label, 'front_view'))
        side_view_action.triggered.connect(lambda: self.processImage(label, 'side_view'))
        white_background_action.triggered.connect(lambda: self.processImage(label, 'white_background'))
        transparent_action.triggered.connect(lambda: self.processImage(label, 'transparent'))
        line_drawing_action.triggered.connect(lambda: self.processImage(label, 'line_drawing'))
        flat_layout_action.triggered.connect(lambda: self.processImage(label, 'flat_layout'))
        matching_action.triggered.connect(lambda: self.processImage(label, 'matching'))
        
        menu.exec_(label.mapToGlobal(position))
    
    def processImage(self, label, process_type):
        """右键菜单处理图片，调用豆包API"""
        image_path = getattr(label, 'image_path', None)
        if not image_path or not os.path.exists(image_path):
            QMessageBox.warning(self, '错误', '找不到源图片')
            return

        # 各功能的prompt映射 - 商业级画质
        q = "，商业摄影级别画质，超高清细节，8K分辨率，专业灯光，锐利清晰"
        prompt_map = {
            'fine_tune': '对图1进行细节微调优化，提升画质和整体效果，保持原图构图和内容不变' + q,
            'front_view': '根据图1生成模特正面视角的展示图，完美保留服装面料质感和细节，专业模特姿态' + q,
            'side_view': '根据图1生成模特侧面视角的展示图，完美保留服装面料质感和细节，专业模特姿态' + q,
            'white_background': '将图1生成白底商品展示图，去除背景保留服装，白色纯净背景，商品细节锐利清晰' + q,
            'transparent': '将图1生成透明背景的商品图，去除背景只保留服装本身，边缘干净利落，细节锐利' + q,
            'line_drawing': '根据图1生成服装的铅笔彩绘线稿图，清晰精准的线条勾勒，专业设计稿质量，无填充色，只对人物主体做线稿，不对背景做线稿。' + q,
            'flat_layout': '根据图1生成服装平铺展示图，服装平整展开铺在平面上，俯视角度，面料纹理清晰可见' + q,
            'matching': '根据图1中的服装生成搭配推荐图，展示完整专业的穿搭搭配效果，时尚杂志风格' + q,
        }

        # 微调图片需要用户输入提示词
        if process_type == 'fine_tune':
            user_prompt, ok = QInputDialog.getText(
                self, '微调图片', '请输入微调提示词：', text=''
            )
            if not ok or not user_prompt.strip():
                return
            prompt = f'对图1进行微调：{user_prompt.strip()}，保持原图整体构图不变' + q
        else:
            prompt = prompt_map.get(process_type, '优化图1')
        image_b64 = self.imageToBase64(image_path)

        # 获取输出目录
        output_dir = self.getOutputDir()
        if not output_dir:
            return

        # 添加占位标签
        placeholder = self.addPlaceholder()

        # 启动后台线程生成
        thread = GenerateThread(prompt, [image_b64], output_dir)
        thread.result_ready.connect(lambda paths, ph=placeholder: self.onGenerateResult(paths, ph))
        thread.error_occurred.connect(lambda msg, ph=placeholder: self.onGenerateError(msg, ph))
        self.active_threads.append(thread)
        thread.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AICanvasApp()
    window.show()
    sys.exit(app.exec_())
