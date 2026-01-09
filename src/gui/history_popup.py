"""
History Popup - 顯示瀏覽歷史縮圖的彈出視窗
長按返回鍵時顯示
"""
from typing import List, Optional
from dataclasses import dataclass
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QPushButton
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QPoint
from PySide6.QtGui import QPixmap, QImage, QPainter, QColor, QFont


@dataclass
class HistoryItem:
    """歷史記錄項目"""
    url: str
    title: str
    thumbnail: Optional[QPixmap] = None
    index: int = 0  # 在歷史中的位置（負數為返回，正數為前進）


class HistoryThumbnail(QFrame):
    """單個歷史縮圖項目"""
    clicked = Signal(int)  # 發送歷史 index

    def __init__(self, item: HistoryItem, parent=None):
        super().__init__(parent)
        self.item = item
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedSize(160, 120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("""
            HistoryThumbnail {
                background-color: #2d2d2d;
                border: 2px solid #3c3c3c;
                border-radius: 8px;
            }
            HistoryThumbnail:hover {
                border: 2px solid #007acc;
                background-color: #37373d;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 縮圖
        self.thumb_label = QLabel()
        self.thumb_label.setFixedSize(152, 85)
        self.thumb_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumb_label.setStyleSheet("""
            background-color: #1e1e1e;
            border-radius: 4px;
        """)

        if self.item.thumbnail:
            scaled = self.item.thumbnail.scaled(
                152, 85,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.thumb_label.setPixmap(scaled)
        else:
            self.thumb_label.setText("No Preview")
            self.thumb_label.setStyleSheet("""
                background-color: #1e1e1e;
                border-radius: 4px;
                color: #6d6d6d;
                font-size: 10px;
            """)

        layout.addWidget(self.thumb_label)

        # 標題
        title_label = QLabel(self._truncate_text(self.item.title or self.item.url, 20))
        title_label.setStyleSheet("color: #d4d4d4; font-size: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

    def _truncate_text(self, text: str, max_len: int) -> str:
        if len(text) > max_len:
            return text[:max_len-3] + "..."
        return text

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.item.index)
        super().mousePressEvent(event)


class HistoryPopup(QFrame):
    """歷史記錄彈出視窗"""
    history_selected = Signal(int)  # 選擇的歷史 index

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.Popup |
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet("""
            HistoryPopup {
                background-color: #252526;
                border: 1px solid #3c3c3c;
                border-radius: 12px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 標題
        title = QLabel("History")
        title.setStyleSheet("""
            color: #569cd6;
            font-weight: bold;
            font-size: 12px;
        """)
        layout.addWidget(title)

        # 滾動區域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #252526;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background-color: #5a5a5a;
                border-radius: 4px;
                min-height: 20px;
            }
        """)

        # 內容容器
        self.content = QWidget()
        self.content_layout = QHBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self.content_layout.addStretch()

        scroll.setWidget(self.content)
        layout.addWidget(scroll)

    def show_history(self, items: List[HistoryItem], anchor_widget: QWidget):
        """顯示歷史記錄"""
        # 清除舊項目
        while self.content_layout.count() > 1:
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 添加新項目
        for hist_item in items:
            thumb = HistoryThumbnail(hist_item)
            thumb.clicked.connect(self._on_item_clicked)
            self.content_layout.insertWidget(self.content_layout.count() - 1, thumb)

        # 調整大小
        item_count = len(items)
        width = min(item_count * 168 + 24, 700)  # 最大寬度 700
        self.setFixedSize(width, 160)

        # 定位到按鈕下方
        pos = anchor_widget.mapToGlobal(QPoint(0, anchor_widget.height()))
        self.move(pos)
        self.show()

    def _on_item_clicked(self, index: int):
        self.history_selected.emit(index)
        self.hide()


class LongPressButton(QPushButton):
    """支援長按的按鈕"""
    long_pressed = Signal()
    LONG_PRESS_TIME = 500  # 長按時間 (ms)

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self._long_press_timer = QTimer(self)
        self._long_press_timer.setSingleShot(True)
        self._long_press_timer.timeout.connect(self._on_long_press)
        self._is_long_press = False

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_long_press = False
            self._long_press_timer.start(self.LONG_PRESS_TIME)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._long_press_timer.stop()
        if self._is_long_press:
            # 長按已處理，不觸發普通 click
            self._is_long_press = False
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _on_long_press(self):
        self._is_long_press = True
        self.long_pressed.emit()
