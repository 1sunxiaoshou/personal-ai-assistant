#coding: utf - 8
import os
import sys
import markdown
from PyQt5.QtCore import Qt,QDate
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import *
from dotenv import dotenv_values, set_key

# 启用高 DPI 缩放(用于适应不同分辨率的设备)
QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)

#  # 获取当前脚本的绝对路径
# current_dir = os.path.dirname(os.path.abspath(__file__))
# # 将项目的根目录添加到 sys.path
# project_root = os.path.join(current_dir, '..', '..')
# sys.path.append(project_root)

# 使用标准的导入语法
from backend.AI import ATRI
from backend.note import NoteManager
from backend.VectorStor import DocumentProcessor
from backend.Todo import TodoDatabase
from frontend.ui_design.Ui_untitled import Ui_Form
 #主窗口
class MyMainWindow(QWidget,Ui_Form):
    def __init__(self):
        super().__init__()
        self.env_path = ".env"
        self.config = dotenv_values(self.env_path)
        self.setupUi(self)
        self.setChat()
        self.setNote()
        self.setKnowledge()
        self.setup_todo_list()
        self.setup_settings()
        self.setup_search_interface()
        
        
    def setup_search_interface(self):
        """连接搜索界面功能"""
        # 连接查询按钮点击事件
        self.searchQuery.clicked.connect(self.perform_search)
        
        # 初始化搜索选项映射字典
        self.search_category_mapping = {
            "全部": 0,
            "对话": 1,  # 虽然对话暂时忽略，保留占位符
            "笔记": 2,
            "知识库": 3,
            "待办": 4
        }

    def perform_search(self):
        """执行综合搜索操作"""
        # 获取输入关键词和搜索类型
        query_text = self.searchInput.text().strip()
        if not query_text:
            QMessageBox.warning(self, "提示", "请输入搜索关键词")
            return
        
        # 根据选项获取搜索类型
        selected_option = self.searchOptions.currentText()
        search_type = self.search_category_mapping[selected_option]
        
        # 执行不同类别的搜索
        search_results = {}
        
        # 笔记搜索（类型2或全部）
        if search_type in [0, 2]:
            notes = self.note.search_notes(query_text)
            for note in notes:
                content_preview = note['content'][:200] + "..." if len(note['content']) > 200 else note['content']
                full_content = note['content']  # 完整内容
                search_results[f"note_{note['filename']}"] = (
                    f"【笔记】{note['title']}\n{content_preview}",
                    query_text,
                    2,  # 对应知识库类别
                    full_content  # 完整内容
                )

        # 知识库搜索（类型3或全部）
        if search_type in [0, 3]:
            knowledge_results = self.knowledge.keyword_search(query_text, doc_type='document')
            for idx, doc in enumerate(knowledge_results):
                content_preview = doc[:200] + "..." if len(doc) > 200 else doc
                full_content = doc  # 完整内容
                search_results[f"knowledge_{idx}"] = (
                    f"【文档】\n{content_preview}",
                    query_text,
                    3,  # 新增知识库类别
                    full_content  # 完整内容
                )

        # 待办搜索（类型4或全部）
        if search_type in [0, 4]:
            todos = self.todo_db.search_tasks_by_description(query_text)
            for task in todos:
                task_id, title, desc, created_at, due_date, completed = task
                due_info = f"截止：{due_date}" if due_date else ""
                status = "已完成" if completed else "未完成"
                full_content = f"{title} ({status})\n{desc}\n{due_info}"
                search_results[f"todo_{task_id}"] = (
                    f"【待办】{title} ({status})\n{desc}\n{due_info}",
                    query_text,
                    4,  # 待办类别
                    full_content  # 完整内容
                )

        # 更新查询结果列表
        self.QueryWidget.set_data(search_results)

    """对话部分"""
    # 初始化chat界面
    def setChat(self):
        self.user_id = "user1"
        self.atri = ATRI(model=self.config.get("CURRENT_MODEL", "qwen-max"))
        self.message_item = None
        
        self.send.clicked.connect(self.send_message)
        self.new_conversation.clicked.connect(lambda: self.messagelist.setCurrentItem(None))
        self.messagelist.currentItemChanged.connect(self.on_item_changed)
        self.messagelist.itemDoubleClicked.connect(self.confirm_delete)
        
        # 添加对话列表
        self.load_conversations()
    
    #更新对话列表
    def load_conversations(self):
        self.messagelist.clear()
        conversations = self.atri.get_conversation_list(self.user_id)
        for conv_id, title in conversations:
            item = QListWidgetItem(title)
            item.setData(Qt.UserRole, conv_id)  # 将对话ID存储在UserRole中
            self.messagelist.addItem(item)
    
    #发送消息
    def send_message(self):
        content =self.chatinput.text()
        if content: 
            self.chatinput.clear()
        else:
            return

        current_item = self.messagelist.currentItem()
        if current_item:
            print('发送')
            # 有选中的对话，发送消息
            conversation_id = current_item.data(Qt.UserRole)
            self.dialogue.add_message(content,True)
            QApplication.processEvents()
            output = self.atri.add_message(conversation_id, content)
            self.dialogue.add_message(output,False)
        else:
            print('创建')
            # 没有选中的对话，创建新的对话
            self.dialogue.clear()
            self.dialogue.add_message(content,True)
            
            self.messagelist.blockSignals(True)# 阻止信号发送
            item = QListWidgetItem(content[:10])
            self.messagelist.insertItem(0, item)
            self.messagelist.setCurrentItem(item)  # 设置新创建的对话为当前选中项
            self.messagelist.blockSignals(False)# 恢复信号发送
            QApplication.processEvents()
            
            conversation_id, output = self.atri.create_conversation(self.user_id, content)
            item.setData(Qt.UserRole, conversation_id)
            
            self.dialogue.add_message(output,False)
    
    #切换对话
    def on_item_changed(self, current_item, previous_item):
        if current_item is None:
            self.dialogue.clear()
        else:
            conversation_id = current_item.data(Qt.UserRole)
            messages = self.atri.get_conversation_messages(conversation_id)
            self.atri.updata_conversation(conversation_id)
            self.dialogue.update_messages(messages)
   
    #删除对话
    def confirm_delete(self, item):
        # 弹出确认对话框
        reply = QMessageBox.question(self, '删除对话', f'你想要删除  "{item.text()}" 吗?',QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            # 用户选择了确认删除
            self.delete_item(item)
        else:
            # 用户选择了取消
            print("取消删除对话")

    def delete_item(self, item):
        # 直接根据 item 移除项目
        self.messagelist.blockSignals(True)# 阻止信号发送
        conversation_id = item.data(Qt.UserRole)
        self.messagelist.takeItem(self.messagelist.row(item))
        self.messagelist.blockSignals(False)# 恢复信号发送
        QApplication.processEvents()
        self.atri.delete_conversation(conversation_id)

    """笔记"""
    #初始化Note界面
    def setNote(self):
        self.note = NoteManager()
        self.markdown_text = None
        self.noteList.clear()
        self.noteList.addItems(self.note.load_notes_list())
        
        self.editNote.clicked.connect(self.toggle_edit_mode)
        self.saveNote.clicked.connect(self.update_note)
        self.newNote.clicked.connect(self.new_note)
        self.delNote.clicked.connect(self.delete_note)
        self.noteList.currentItemChanged.connect(self.show_note_content)

    def show_note_content(self, current, previous):
        # 获取选中的笔记名称
        note_name = current.text()
        note_dict = self.note.get_note(note_name)
        self.markdown_text = note_dict['content']
        self.titleEdit.setText(note_dict['title'])
        self.tagsEdit.setText(','.join(note_dict['tags']))
        html = markdown.markdown(self.markdown_text)
        self.noteShow.setHtml(html)
        
    def toggle_edit_mode(self):
        if self.noteShow.isReadOnly():
            self.editNote.setText("切换到预览")
            # 禁用笔记列表
            self.noteList.setEnabled(False)
            
            self.noteShow.setReadOnly(False)
            self.titleEdit.setReadOnly(False)
            self.tagsEdit.setReadOnly(False)
            self.noteShow.setPlainText(self.markdown_text)
            self.saveNote.setEnabled(True)
        else:
            self.editNote.setText("切换到编辑")
            # 启用笔记列表
            self.noteList.setEnabled(True)
            
            self.noteShow.setReadOnly(True)
            self.titleEdit.setReadOnly(True)
            self.tagsEdit.setReadOnly(True)
            self.markdown_text = self.noteShow.toPlainText()
            html = markdown.markdown(self.markdown_text)
            self.noteShow.setHtml(html)
            self.saveNote.setEnabled(False)
    
    def update_note(self):
        #获取各个文本输入的值
        title = self.noteList.currentItem().text()
        new_title = self.titleEdit.text()
        # 同时处理英文逗号和中文逗号
        tags_text = self.tagsEdit.text()
        # 替换中文逗号为英文逗号
        tags_text = tags_text.replace('，', ',')
        # 使用 split 方法按逗号分割文本
        tags_list = [tag.strip() for tag in tags_text.split(",")]
        if title=="新笔记":
            self.note.save_note(new_title,self.noteShow.toPlainText(),tags_list)
        else:
            self.note.update_note(title,new_title,content=self.noteShow.toPlainText(),tags=tags_list)
        #更新列表
        self.noteList.currentItem().setText(new_title)
        # 切换到编辑模式
        self.toggle_edit_mode()
        
    def new_note(self):
        self.noteList.blockSignals(True)
        default_title = "新笔记"
        # 在 noteList 中添加一个新的条目
        new_item = QListWidgetItem(default_title)
        self.noteList.addItem(new_item)
        
        # 选择新添加的条目
        self.noteList.setCurrentItem(new_item)
        
        # 清空或重置编辑控件
        self.titleEdit.setText(default_title)  # 设置默认标题
        self.tagsEdit.clear()  # 清空标签编辑框
        self.markdown_text = ""  # 清空 Markdown 文本
        self.noteShow.setPlainText("")  # 清空显示区域
        
        # 切换到编辑模式
        if self.noteShow.isReadOnly():
            self.toggle_edit_mode()
        self.noteList.blockSignals(False)
    
    def delete_note(self):
        self.noteList.blockSignals(True)
        # 获取当前选中的笔记条目
        current_item = self.noteList.currentItem()
        
        if current_item is None:
            # 如果没有选中任何条目，则返回
            return

        note_title = current_item.text()
        self.note.delete_note(note_title)
        self.noteList.takeItem(self.noteList.row(current_item))
        
        # 清空或重置编辑控件
        self.titleEdit.clear()
        self.tagsEdit.clear()
        self.markdown_text = ""
        self.noteShow.setPlainText("")
        
        # 切换回预览模式（如果当前处于编辑模式）
        if not self.noteShow.isReadOnly():
            self.toggle_edit_mode()
        self.noteList.blockSignals(False)

    """知识库"""
    def setKnowledge(self):
        self.knowledge = DocumentProcessor()
        self.doc_type = 'all'
        document_list = self.knowledge.get_document_list(doc_type = 'all')
        self.listWidget.addItems(document_list)
        self.listWidget.itemDoubleClicked.connect(self.show_document_details)
        self.pushButton_2.clicked.connect(self.add_knowledge)
        self.radioButton.toggled.connect(self.on_radio_button_toggled)
        self.radioButton_2.toggled.connect(self.on_radio_button_toggled)
        self.radioButton_3.toggled.connect(self.on_radio_button_toggled)
    
    def on_radio_button_toggled(self):
        # 判断是哪个单选按钮被选中
        if self.radioButton.isChecked():
            self.doc_type = 'all'
        elif self.radioButton_2.isChecked():
            self.doc_type = 'document'
        elif self.radioButton_3.isChecked():
            self.doc_type = 'note'
        self.update_document_list()
        
    # 知识库内容展示
    def show_document_details(self, item):
        document_path = item.text()
        
        document_data = self.knowledge.get_document_content(document_path, doc_type=self.doc_type)
        
        if document_data['texts'] is not None:
            # 创建对话框
            dialog = QDialog(self)
            layout = QVBoxLayout()

            # 创建一个多行文本框并设置为只读
            text_edit = QTextEdit(dialog)
            text_edit.setReadOnly(True)
            details = "\n".join([f"Document Text {index}:\n{content}\n{'-'*38}" for index, content in enumerate(document_data['texts'])])
            text_edit.setText(details)

            # 使用QScrollArea包裹文本显示区域以支持滑动
            scroll_area = QScrollArea(dialog)
            scroll_area.setWidgetResizable(True)
            scroll_area.setWidget(text_edit)

            layout.addWidget(scroll_area)

            # 添加删除和退出按钮
            delete_button = QPushButton("删除", dialog)
            exit_button = QPushButton("退出", dialog)
            layout.addWidget(delete_button)
            layout.addWidget(exit_button)

            # 设置对话框的布局
            dialog.setLayout(layout)
            dialog.setWindowTitle("文档详情")

            def knowledge_delete(knowledge,listWidget,dialog):
                knowledge.delete_document(document_path,doc_type=document_data['metadatas'][-1]['type'])
                listWidget.clear()  # 清空列表
                listWidget.addItems(knowledge.get_document_list(self.doc_type))
                dialog.close()  # 关闭对话框
            # 连接按钮到相应的槽函数
            delete_button.clicked.connect(lambda:knowledge_delete(self.knowledge,self.listWidget,dialog))
            exit_button.clicked.connect(dialog.close)

            # 显示对话框
            dialog.exec_()
        else:
            QMessageBox.warning(self, "未找到文档", f"未找到文档: {document_path}")
    
    def add_knowledge(self):
        """
        打开文件对话框让用户选择文件，并将这些文件添加到知识库中。
        成功后更新 QListWidget 显示最新的文档列表。
        """
        # 打开文件对话框，允许用户选择多个文件
        options = QFileDialog.Options()
        document_paths, _ = QFileDialog.getOpenFileNames(self, "选择要添加的文件", "", "All Files (*);;Text Files (*.txt)", options=options)
        
        if document_paths:  # 如果选择了文件
            try:
                # 加载并嵌入文档
                self.knowledge.load_and_embed_documents(document_paths,"note" if self.doc_type == "note" else 'document')  # 假设所有文件都是'document'类型
                
                # 更新 QListWidget 显示
                self.update_document_list()
                
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法加载文件: {e}")
        else:
            print("未选择任何文件")

    def update_document_list(self):
        """
        更新 QListWidget 显示最新的文档列表。
        """
        # 清空当前列表
        self.listWidget.clear()
        
        # 获取所有文档列表
        documents = self.knowledge.get_document_list(self.doc_type)
        
        # 将每个文档添加到 QListWidget 中
        for doc in documents:
            self.listWidget.addItem(doc)
   
    """待办"""
    def setup_todo_list(self):
        """待办事项标签页（tab_5）界面构建"""
        tab = self.tab_5
        
        # 主布局
        main_layout = QVBoxLayout(tab)
        
        # 顶部输入栏（添加日期输入）
        input_layout = QHBoxLayout()
        self.todo_input = QLineEdit()
        self.todo_input.setPlaceholderText("添加新的待办事项标题")
        
        self.todo_input_2 = QLineEdit()
        self.todo_input_2.setPlaceholderText("新的待办事项内容")
        
        # 添加日期输入控件
        self.due_date_input = QDateEdit()
        self.due_date_input.setDisplayFormat("yyyy-MM-dd")
        self.due_date_input.setDate(QDate.currentDate())
        self.due_date_input.setCalendarPopup(True)
        
        self.add_todo_btn = QPushButton("添加")
        input_layout.addWidget(self.todo_input, 2)
        input_layout.addWidget(self.todo_input_2, 2)
        input_layout.addWidget(self.due_date_input, 2)
        input_layout.addWidget(self.add_todo_btn, 2)
        
        # 待办列表
        self.todo_list = QListWidget()
        
        # 底部过滤栏
        filter_bar = QHBoxLayout()
        self.show_all_radio = QRadioButton("全部")
        self.show_active_radio = QRadioButton("未完成")
        self.show_completed_radio = QRadioButton("已完成")
        self.show_all_radio.setChecked(True)
        filter_bar.addWidget(QLabel("筛选:"))
        filter_bar.addWidget(self.show_all_radio)
        filter_bar.addWidget(self.show_active_radio)
        filter_bar.addWidget(self.show_completed_radio)
        filter_bar.addStretch()
        
        # 组合布局
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.todo_list, 1)
        main_layout.addLayout(filter_bar)
        
        # 初始化数据库
        self.todo_db = TodoDatabase()
        
        # 连接信号
        self.add_todo_btn.clicked.connect(self.on_add_todo)
        self.show_all_radio.toggled.connect(self.refresh_todo_list)
        self.show_active_radio.toggled.connect(self.refresh_todo_list)
        self.show_completed_radio.toggled.connect(self.refresh_todo_list)
        
        # 初始加载数据
        self.refresh_todo_list()

    def on_add_todo(self):
        """处理添加新待办事项"""
        title = self.todo_input.text().strip()
        description = self.todo_input_2.text().strip()
        if not title:
            QMessageBox.warning(self, "输入错误", "待办事项标题不能为空")
            return
        
        due_date = self.due_date_input.date().toPyDate()
        self.todo_db.add_task(
            title=title,
            description = description,
            due_date=due_date
        )
        self.todo_input.clear()
        self.todo_input_2.clear()
        self.refresh_todo_list()

    def refresh_todo_list(self):
        """刷新待办事项列表"""
        # 获取筛选条件
        if self.show_all_radio.isChecked():
            tasks = self.todo_db.get_all_tasks()
        elif self.show_active_radio.isChecked():
            tasks = self.todo_db.get_incomplete_tasks()
        else:
            tasks = self.todo_db.get_completed_tasks()
        
        self.todo_list.clear()
        
        for task in tasks:
            task_id, title, description, created_at, due_date, completed = task
            item = QListWidgetItem()
            widget = QWidget()
            layout = QHBoxLayout(widget)
            
            # 完成状态复选框
            checkbox = QCheckBox()
            checkbox.setChecked(bool(completed))
            checkbox.stateChanged.connect(lambda state, id=task_id: 
                self.todo_db.mark_task_as_completed(id, state == Qt.Checked))
            checkbox.stateChanged.connect(self.refresh_todo_list)
            layout.addWidget(checkbox)
            
            # 任务信息显示
            info_label = QLabel()
            text = f"<b>{title}</b>"
            if due_date:
                text += f"<br>截止: {due_date}"
            if description:
                text += f"<br>{description}"
            info_label.setText(text)
            info_label.setWordWrap(True)
            layout.addWidget(info_label, 1)
            
            # 删除按钮
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda _, id=task_id: 
                self.on_delete_task(id))
            layout.addWidget(delete_btn)
            
            # 设置列表项
            item.setSizeHint(widget.sizeHint())
            self.todo_list.addItem(item)
            self.todo_list.setItemWidget(item, widget)

    def on_delete_task(self, task_id):
        """处理删除任务"""
        confirm = QMessageBox.question(
            self, "确认删除", "确定要删除这个任务吗？",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.todo_db.delete_task(task_id)
            self.refresh_todo_list()

    """设置"""
    def setup_settings(self):
        """设置标签页（tab_6）界面构建"""
        tab = self.tab_6

        # 主布局
        main_layout = QVBoxLayout(tab)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # 内容布局
        layout = QFormLayout(content)

        # 第一组：外观设置
        appearance_group = QGroupBox("外观设置")
        appearance_layout = QFormLayout(appearance_group)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色主题", "深色主题", "系统默认"])
        self.font_size = QSpinBox()
        self.font_size.setRange(8, 24)
        self.font_size.setValue(12)
        appearance_layout.addRow("主题方案:", self.theme_combo)
        appearance_layout.addRow("字体大小:", self.font_size)

        # 第二组：通知设置
        notify_group = QGroupBox("通知设置")
        notify_layout = QFormLayout(notify_group)

        self.enable_notify = QCheckBox("启用桌面通知")
        self.notify_interval = QComboBox()
        self.notify_interval.addItems(["即时提醒", "每30分钟", "每小时"])
        notify_layout.addRow(self.enable_notify)
        notify_layout.addRow("提醒频率:", self.notify_interval)

        # 第三组：账户设置
        account_group = QGroupBox("账户设置")
        account_layout = QFormLayout(account_group)

        # 从 .env 文件中加载用户名
        self.username = QLineEdit()
        self.username.setText(self.config.get("USERNAME", ""))  # 加载用户名
        account_layout.addRow("用户名:", self.username)

        # API 密钥使用密码控件
        self.api_key = QLineEdit()
        self.api_key.setEchoMode(QLineEdit.Password)  # 设置为密码模式
        self.api_key.setText(self.config.get("API_KEY", ""))  # 加载 API 密钥
        account_layout.addRow("API密钥:", self.api_key)

        # 第四组：模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout(model_group)

        # 从 .env 文件中读取模型列表
        model_list = self.config.get("MODEL_LIST", "模型1,模型2,模型3").split(",")
        current_model = self.config.get("CURRENT_MODEL", "模型1")

        self.model_combo = QComboBox()
        self.model_combo.addItems(model_list)
        self.model_combo.setCurrentText(current_model)
        model_layout.addRow("当前模型:", self.model_combo)

        # 保存按钮
        self.save_button = QPushButton("保存设置")
        self.save_button.clicked.connect(self.save_settings)
        model_layout.addRow(self.save_button)

        # 组合所有设置组
        layout.addWidget(appearance_group)
        layout.addWidget(notify_group)
        layout.addWidget(account_group)
        layout.addWidget(model_group)
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def save_settings(self):
        """保存设置到 .env 文件"""
        # 保存用户名和 API 密钥
        set_key(self.env_path, "USERNAME", self.username.text())
        set_key(self.env_path, "API_KEY", self.api_key.text())

        # 保存模型设置
        selected_model = self.model_combo.currentText()
        set_key(self.env_path, "CURRENT_MODEL", selected_model)

        print("设置已保存！")
        
        
if __name__ == "__main__":

    app = QApplication(sys.argv)
    myWin = MyMainWindow()
    myWin.show()
    sys.exit(app.exec_())