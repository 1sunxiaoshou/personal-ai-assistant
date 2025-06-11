import sqlite3
from datetime import datetime

class MessageManager:
    def __init__(self, message_db_path = "./user_data/message.db"):
        self.conn = sqlite3.connect(message_db_path)
        self.cursor = self.conn.cursor()
        self._initialize_database()

    def _initialize_database(self):
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            user_id TEXT,
            created_at TEXT,
            title TEXT    -- 新增字段，用于存储对话的标题
        )
        ''')
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY,
            conversation_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
        ''')
        
        # 为 messages 表的 conversation_id 列创建索引
        self.cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages (conversation_id)
        ''')
        
        self.conn.commit()

    def create_conversation(self, user_id, first_message_role:str, first_message_content:str, max_title_length=10):
        """创建新的对话，并添加第一条消息"""
        created_at = datetime.now().isoformat()
        title = first_message_content[:max_title_length]
        self.cursor.execute('''
        INSERT INTO conversations (user_id, created_at, title) VALUES (?, ?, ?)
        ''', (user_id, created_at, title))
        conversation_id = self.cursor.lastrowid
        
        self.add_regular_message(conversation_id, first_message_role, first_message_content)
        
        self.conn.commit()
        return conversation_id

    def add_regular_message(self, conversation_id, role, content:str):
        """添加常规消息到当前对话"""
        self.cursor.execute('''
        INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)
        ''', (conversation_id, role, content, datetime.now().isoformat()))
        self.conn.commit()

    def get_regular_messages(self, conversation_id):
        """获取指定对话的常规消息"""
        self.cursor.execute('''
        SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at
        ''', (conversation_id,))
        messages = self.cursor.fetchall()
        return messages

    def get_conversation_title(self, conversation_id):
        """获取对话的标题"""
        self.cursor.execute('''
        SELECT title FROM conversations WHERE id = ?
        ''', (conversation_id,))
        title = self.cursor.fetchone()[0]
        return title

    def get_conversation_list(self, user_id):
        """获取用户的所有对话的 id 和 title"""
        self.cursor.execute('''
        SELECT id, title FROM conversations WHERE user_id = ? ORDER BY created_at DESC
        ''', (user_id,))
        conversation_list = self.cursor.fetchall()
        return conversation_list
    
    def delete_conversation(self, conversation_id):
        """根据 id 删除一个对话及其相关消息"""
        # 删除相关消息
        self.cursor.execute('''
        DELETE FROM messages WHERE conversation_id = ?
        ''', (conversation_id,))
        
        # 删除对话
        self.cursor.execute('''
        DELETE FROM conversations WHERE id = ?
        ''', (conversation_id,))
        
        self.conn.commit()

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __del__(self):
        """在对象销毁时自动关闭数据库连接"""
        self.close()

# 示例使用
if __name__ == '__main__':
    message_manager = MessageManager()

    # 创建新对话并添加第一条消息
    user_id = 'user1'
    first_message_role = 'human'
    first_message_content = 'Hello, how are you?'
    conversation_id = message_manager.create_conversation(user_id, first_message_role, first_message_content)
    print(f"Started new conversation with ID: {conversation_id}")

    # # 添加更多常规消息
    # message_manager.add_regular_message(conversation_id, 'ai', 'I am fine, thank you!')

    # 获取常规消息
    messages = message_manager.get_regular_messages(conversation_id)
    print("Messages in the conversation:", messages)

    # # 获取对话的标题
    # title = message_manager.get_conversation_title(conversation_id)
    # print("Conversation title:", title)
    
    # 获取用户的所有对话列表
    conversation_list = message_manager.get_conversation_list(user_id)
    print("User's conversation list:", conversation_list)

    # # 删除对话
    # message_manager.delete_conversation(conversation_id)
    # print(f"Deleted conversation with ID: {conversation_id}")

    # # 再次获取用户的所有对话列表
    # conversation_list = message_manager.get_conversation_list(user_id)
    # print("User's conversation list after deletion:", conversation_list)

    # 关闭数据库连接
    message_manager.close()