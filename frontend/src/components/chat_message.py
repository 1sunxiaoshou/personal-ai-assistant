from PyQt5.QtWidgets import QApplication, QListWidget, QListWidgetItem, QHBoxLayout, QLabel, QSizePolicy,QWidget
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtCore import Qt, QSize
import markdown2

class MessageItem(QWidget):
    def __init__(self, message, is_user=True, parent=None):
        super().__init__(parent)
        self.is_user = is_user

        # 创建主布局
        main_layout = QHBoxLayout()

        # 创建头像
        avatar_label = QLabel(self)
        
        #根据is_user选则不同的头像
        if is_user:
            avatar_pixmap = QPixmap("./frontend/assets/猫猫.png") 
        else:
            avatar_pixmap = QPixmap("./frontend/assets/第24帧.png")
        avatar_pixmap = avatar_pixmap.scaled(60, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        avatar_label.setPixmap(avatar_pixmap)

        # 创建消息内容
        label = QLabel(self.format_message(message), wordWrap=True)
        label.setTextFormat(Qt.RichText)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setOpenExternalLinks(True)
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)  # 水平方向扩展，垂直方向最小
        label.setMinimumHeight(40)  # 设置最小高度

        # 设置字体大小
        font = QFont("宋体", 10)  # 设置字体和大小
        label.setFont(font)

        if self.is_user:
            label.setStyleSheet("background-color: #c7a3ff; border-radius: 10px; padding: 10px; height: auto;")
            main_layout.addStretch(1)  # 推动头像和消息靠右
            main_layout.addWidget(label)
            main_layout.addWidget(avatar_label)
        else:
            label.setStyleSheet("background-color: #a3eaff; border-radius: 10px; padding: 10px; height: auto;")
            main_layout.addWidget(avatar_label)
            main_layout.addWidget(label)
            main_layout.addStretch(1)  # 推动头像和消息靠左

        self.setLayout(main_layout)

    def format_message(self, message):
        message = markdown2.markdown(message, extras=["fenced-code-blocks"])
        return message

class MessageListWidget(QListWidget):
    def __init__(self, parent=None, messages=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.NoSelection)  # 去除选中事件
        self.setAlternatingRowColors(False)  # 去除交替行颜色
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)  # 允许像素级别的滚动
        self.setDragDropMode(QListWidget.NoDragDrop)  # 禁用拖放
        self.setFocusPolicy(Qt.NoFocus)  # 禁用焦点
        self.messages = messages or [
        {"message": "用户输入的消息将会在此显示","is_user": True},
        {"message": "atri的回答将会在此显示", "is_user": False}
    ]
        self.update_messages(self.messages)

    def update_messages(self, messages):
        self.messages = messages
        self.clear()
        if messages:
            for message in messages:
                self.add_message(**message)

    def add_message(self, message, is_user=True):
        # 创建 MessageItem
        message_item = MessageItem(message, is_user, self)

        # 创建 QListWidgetItem 并设置其 widget
        list_item = QListWidgetItem(self)
        list_item.setSizeHint(message_item.sizeHint())
        self.setItemWidget(list_item, message_item)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)

    # 创建主窗口
    main_window = MessageListWidget()
    main_window.setWindowTitle("Message List Example")
    main_window.resize(400, 600)
    main_window.show()

    # 添加一些示例消息
    messages = [
        {"message": "Hello, this is a user message.", "is_user": True},
        {"message": "This is a bot response.", "is_user": False},
        {"message": "Another user message with some **bold** text.", "is_user": True},
        {"message": "Bot response with a [link](https://example.com).", "is_user": False}
    ]
    main_window.update_messages(messages)

    sys.exit(app.exec_())