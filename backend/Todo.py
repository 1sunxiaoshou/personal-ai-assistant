import os
import sqlite3
import datetime
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class TodoDatabase:
    def __init__(self, db_path=os.getenv("todo_db_path")):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table_if_not_exists()

    def _create_table_if_not_exists(self):
        # 创建任务表（如果不存在）
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                due_date DATE,
                completed BOOLEAN DEFAULT 0
            )
        ''')
        self.conn.commit()

    #添加一条待办
    def add_task(self, title, description=None, due_date=None):
        """
        向数据库中添加任务。

        参数:
        - title (str): 任务标题，必填。
        - description (str, 可选): 任务描述，默认为None。
        - due_date (date, 可选): 任务截止日期，默认为None。

        此函数将任务信息插入到数据库的tasks表中。如果指定了截止日期，
        则将其转换为ISO格式字符串再插入数据库。
        """
        if due_date and isinstance(due_date, datetime.date):
            due_date = due_date.isoformat()
        # 删除下面这行错误的赋值
        # if description:
        #     description = title

        self.cursor.execute(
            "INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)",
            (title, description, due_date)
        )
        self.conn.commit()

    #获取所有待办
    def get_all_tasks(self):
        self.cursor.execute("SELECT * FROM tasks ORDER BY due_date, created_at")
        return self.cursor.fetchall()

    #获取未完成待办
    def get_incomplete_tasks(self):
        self.cursor.execute("SELECT * FROM tasks WHERE completed = 0 ORDER BY due_date, created_at")
        return self.cursor.fetchall()

    #根据id来将任务标记为已完成
    def mark_task_as_completed(self, task_id):
        self.cursor.execute(
            "UPDATE tasks SET completed = 1 WHERE id = ?",
            (task_id,)
        )
        self.conn.commit()

    #删除指定任务
    def delete_task(self, task_id):
        self.cursor.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )
        self.conn.commit()

    def search_tasks_by_description(self, description_pattern):
        """
        通过模糊的描述来查询对应的待办事项。

        参数:
        - description_pattern (str): 描述模式，使用SQL LIKE语法。

        返回:
        - list: 匹配的待办事项列表。
        """
        # 使用LIKE运算符进行模糊匹配
        query = "SELECT * FROM tasks WHERE title LIKE ? OR description LIKE ?"
        pattern = '%' + description_pattern + '%'
        self.cursor.execute(query, (pattern, pattern))
        return self.cursor.fetchall()

    def close(self):
        self.conn.close()
        
    # 在TodoDatabase类中添加以下方法
    def get_completed_tasks(self):
        self.cursor.execute("SELECT * FROM tasks WHERE completed = 1 ORDER BY due_date, created_at")
        return self.cursor.fetchall()

    def mark_task_as_completed(self, task_id, completed=True):
        self.cursor.execute(
            "UPDATE tasks SET completed = ? WHERE id = ?",
            (1 if completed else 0, task_id)
        )
        self.conn.commit()