from PyQt5 import QtWidgets, QtCore, QtGui

class DetailDialog(QtWidgets.QDialog):
    """详情展示对话框"""
    def __init__(self, title, content, category, parent=None):
        super().__init__(parent)
        self.setWindowTitle("详情内容")
        self.setMinimumSize(600, 400)
        
        # 主布局
        layout = QtWidgets.QVBoxLayout(self)
        self.setStyleSheet("""
        QDialog {
            background-color: #F5F5F5; /* 使用浅灰色作为背景色，看起来更干净 */
            border: 1px solid #E0E0E0; /* 添加轻微边框，增加层次感 */
        }
        QLabel {
            font-size: 14px; /* 稍微减小字体大小，使信息更加紧凑 */
            color: #333333; /* 使用深灰色文字，提高可读性 */
        }
        QTextEdit {
            font-size: 18px; /* 调整为适中的字体大小 */
            background-color: #FFFFFF; /* 使用纯白色背景，保持简洁 */
            color: #333333; /* 与标签一致的文字颜色 */
            border: 1px solid #CCCCCC; /* 给文本编辑框加上淡淡的边框 */
            padding: 10px; /* 增加内边距，让内容不紧贴边缘 */
        }
        """)

        # 标题栏
        title_layout = QtWidgets.QHBoxLayout()
        self.title_label = QtWidgets.QLabel(title)
        title_layout.addWidget(self.title_label)
        
        # 分类标签
        self.category_label = QtWidgets.QLabel()
        self._set_category_style(category)
        title_layout.addWidget(self.category_label)
        layout.addLayout(title_layout)
        
        # 内容区域
        self.content_area = QtWidgets.QScrollArea()
        self.content_area.setWidgetResizable(True)
        
        content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QVBoxLayout(content_widget)
        
        self.content_text = QtWidgets.QTextEdit()
        self.content_text.setReadOnly(True)
        self.content_text.setHtml(content)
        
        self.content_layout.addWidget(self.content_text)
        self.content_area.setWidget(content_widget)
        layout.addWidget(self.content_area)
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, 0, QtCore.Qt.AlignRight)

    def _set_category_style(self, category):
        """设置分类标签样式"""
        style_map = {
            1: ("对话", "blue"),
            2: ("笔记", "green"),
            3: ("知识库", "purple"),
            4: ("待办事项", "orange")
        }
        text, color = style_map.get(category, ("未知", "gray"))
        self.category_label.setText(text)
        self.category_label.setStyleSheet(f"""
            color: {color}; 
            font: 18px; /* 增大字体 */
            padding: 4px 10px; /* 调整padding来统一高度 */
            border: none;
            border-radius: 5px; /* 稍微增加圆角半径 */
        """)


class HighlightableListWidget(QtWidgets.QListWidget):
    """支持双击弹出详情窗口的自定义列表"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSpacing(5)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setResizeMode(QtWidgets.QListWidget.Adjust)
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _highlight_text(self, text, keywords):
        """高亮关键词处理"""
        if not keywords:
            return text
        return text.replace(
            keywords, 
            f'<span style="color:red; font-weight:600;">{keywords}</span>'
        )

    def add_items_from_dict(self, data):
        for item_id, (text, highlight, category, full_content) in data.items():
            item = QtWidgets.QListWidgetItem(self)
            
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(widget)
            layout.setContentsMargins(5, 5, 5, 5)
            
            text_label = QtWidgets.QLabel()
            preview_text = text[:200] + "..." if len(text) > 200 else text
            text_label.setTextFormat(QtCore.Qt.RichText)
            text_label.setWordWrap(True)
            text_label.setText(self._highlight_text(preview_text, highlight))
            
            category_label = QtWidgets.QLabel()
            category_label.setAlignment(QtCore.Qt.AlignRight)
            self._set_category_style(category_label, category)
            
            layout.addWidget(text_label)
            layout.addWidget(category_label)
            
            item.setSizeHint(widget.sizeHint())
            self.setItemWidget(item, widget)
            # 存储完整内容和其他数据
            item.setData(QtCore.Qt.UserRole, (full_content, highlight, category))

    def _set_category_style(self, label, category):
        """设置分类标签样式"""
        style_map = {
            1: ("对话", "blue"),
            2: ("笔记", "green"),
            3: ("知识库", "purple"),
            4: ("待办事项", "orange")
        }
        text, color = style_map.get(category, ("未知", "gray"))
        label.setText(text)
        label.setStyleSheet(f"""
            color: {color}; 
            font: 12px; /* 增大字体 */
            border: none;
            border-radius: 5px; /* 稍微增加圆角半径 */
        """)

    def _on_item_double_clicked(self, item):
        full_content, highlight, category = item.data(QtCore.Qt.UserRole)
        highlighted_content = self._highlight_text(full_content, highlight)
        
        dialog = DetailDialog(
            title="详细信息",
            content=highlighted_content,
            category=category,
            parent=self
        )
        dialog.exec_()

    def set_data(self, data):
        """设置数据并刷新列表"""
        self.clear()
        self.add_items_from_dict(data)


# 测试代码保持不变
if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)

    main_window = QtWidgets.QWidget()
    main_layout = QtWidgets.QVBoxLayout(main_window)

    custom_list_widget = HighlightableListWidget()

    test_data = {
        1: ("啊，前辈！Ciallo,初次见面我是美咕噜，请多多关照", "Ciallo", 2,"啊，前辈！Ciallo,初次见面我是美咕噜，请多多关照"),
        2: ("这是一个对话示例", "示例", 1,"啊，前辈！Ciallo,初次见面我是美咕噜，请多多关照"),
        3: ("这是另一个待办事项", "待办事项", 4,"啊，前辈！Ciallo,初次见面我是美咕噜，请多多关照"),
        4: ("""《魔女的夜宴》（日语：サノバウィッチ，英文：SABBAT OF THE WITCH）是由日本游戏公司柚子社（YUZU SOFT）开发的一款美少女游戏，首次发布于2015年2月27日。这款游戏结合了学园、魔法少女、恋爱、喜剧等元素，通过精美的画面、丰富的剧情以及多元化的玩法，吸引了大量玩家的喜爱。
            故事背景
            游戏的故事发生在一个充满魔法与奇幻色彩的校园里，主角保科柊史拥有读取他人感情的能力。在一次偶然的机会下，他遇到了正与魔女签订契约的绫地宁宁，并被迫加入超自然研究社。从那时起，柊史不仅要与宁宁一同收集被称为“心之碎片”的重要物品，还会与其他几位女主角相遇，展开一系列浪漫而又奇幻的冒险。
            """, "柚子社", 3,"啊，前辈！Ciallo,初次见面我是美咕噜，请多多关照"),
    }

    custom_list_widget.set_data(test_data)
    main_layout.addWidget(custom_list_widget)
    main_window.setLayout(main_layout)
    main_window.show()
    sys.exit(app.exec_())