import os
import yaml
from datetime import datetime, timezone
from .VectorStor import DocumentProcessor

class NoteManager:
    def __init__(self, notes_directory='./notes', sync_with_knowledge_base=False):
        self.notes_directory = notes_directory
        os.makedirs(self.notes_directory, exist_ok=True)
        
        self.doc_processor = DocumentProcessor()
        self.sync_with_knowledge_base = sync_with_knowledge_base
        if self.sync_with_knowledge_base:
            self.sync_notes_with_knowledge_base()

    def sync_notes_with_knowledge_base(self):
        """
        同步本地笔记与知识库中的笔记。
        删除知识库中不存在的笔记，并添加本地存在的但未同步的笔记。
        """
        local_notes = {filename: os.path.join(self.notes_directory, filename) 
                       for filename in os.listdir(self.notes_directory) if filename.endswith('.md')}
        knowledge_base_notes = self.doc_processor.get_document_list(doc_type='note')
        
        # 删除知识库中不存在的笔记
        to_delete = set(knowledge_base_notes) - set(local_notes.values())
        # print(f'删除的知识库：{list(to_delete)}')
        if to_delete:
            self.doc_processor.delete_document(list(to_delete), doc_type='note')
        
        # 添加未同步的笔记
        to_add = set(local_notes.values()) - set(knowledge_base_notes)
        # print(f'添加未同步的：{list(to_add)}')
        if to_add:
            self.doc_processor.load_and_embed_documents(list(to_add), doc_type='note')

    # 加载笔记列表
    def load_notes_list(self):
        notes_list = []
        
        # 遍历指定目录下的所有文件
        for filename in os.listdir(self.notes_directory):
            if filename.endswith('.md'):
                # 去掉 .md 扩展名后添加到列表
                note_name = os.path.splitext(filename)[0]
                notes_list.append(note_name)
        
        return notes_list

    # 保存新的笔记
    def save_note(self, title, content, tags=None):
        if self.note_exists(title):
            raise ValueError(f"笔记标题： '{title}' 已存在.")
        
        metadata = {
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat(),
            'tags': tags if tags else [],
            'title': title
        }
        full_content = self._create_full_content(metadata, content)
        file_name = f"{title}.md"
        file_path = os.path.join(self.notes_directory, file_name)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        if self.sync_with_knowledge_base:
            self.doc_processor.load_and_embed_documents([file_path], doc_type='note')
        
        return title

    # 删除指定标题的笔记
    def delete_note(self, title) -> bool:
        file_name = f"{title}.md"
        file_path = os.path.join(self.notes_directory, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            if self.sync_with_knowledge_base:
                self.doc_processor.delete_document(file_path, doc_type='note')
            return True
        return False

    # 搜索包含指定关键字的笔记
    def search_notes(self, query):
        query_lower = query.lower()
        notes = []
        for filename in os.listdir(self.notes_directory):
            if filename.endswith('.md'):
                metadata, body = self._read_note_metadata_and_body(filename)
                if query_lower in body.lower() or query_lower in metadata.get('title', '').lower():
                    notes.append({
                        'title': metadata.get('title', ''),
                        'content': body,
                        'created_at': metadata.get('created_at', ''),
                        'updated_at': metadata.get('updated_at', ''),
                        'tags': metadata.get('tags', []),
                        'filename': filename
                    })
        return notes
    
    # 获取指定标题的笔记
    def get_note(self, title):
        file_name = f"{title}.md"
        file_path = os.path.join(self.notes_directory, file_name)
        if os.path.exists(file_path):
            metadata, body = self._read_note_metadata_and_body(file_name)
            return {
                'title': metadata.get('title', ''),
                'content': body,
                'created_at': metadata.get('created_at', ''),
                'updated_at': metadata.get('updated_at', ''),
                'tags': metadata.get('tags', []),
                'filename': file_name
            }
        return None
    
    # 更新指定标题的笔记
    def update_note(self, title, new_title, content, tags=None):
        if title != new_title and self.note_exists(new_title):
            raise ValueError(f"笔记标题'{new_title}' 已存在. ")
        
        note = self.get_note(title)
        if note:
            old_file_name = f"{title}.md"
            old_file_path = os.path.join(self.notes_directory, old_file_name)
            
            note['title'] = new_title
            note['content'] = content
            note['tags'] = tags if tags else note['tags']
            note['updated_at'] = datetime.now(timezone.utc).isoformat()
            full_content = self._create_full_content(note, content)
            
            new_file_name = f"{new_title}.md"
            new_file_path = os.path.join(self.notes_directory, new_file_name)
            
            if old_file_name != new_file_name:
                os.rename(old_file_path, new_file_path)
            if self.sync_with_knowledge_base:
                self.doc_processor.delete_document(old_file_path, doc_type='note')
                self.doc_processor.load_and_embed_documents([new_file_path], doc_type='note')
            
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            return True
        raise ValueError(f"Note with title '{title}' not found")

    # 检查指定标题的笔记是否存在
    def note_exists(self, title):
        file_name = f"{title}.md"
        return os.path.exists(os.path.join(self.notes_directory, file_name))

    def _read_note_metadata_and_body(self, filename):
        """
        从文件中读取笔记的元数据和正文。
        
        :param filename: 笔记文件名
        :return: 元数据和正文的元组
        """
        file_path = os.path.join(self.notes_directory, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            metadata, body = self._parse_metadata_and_body(content)
        return metadata, body

    def _parse_metadata_and_body(self, content):
        """
        解析笔记内容，分离元数据和正文。
        
        :param content: 笔记的完整内容
        :return: 元数据和正文的元组
        """
        lines = content.splitlines()
        if lines[0] == '---':
            metadata_end_index = lines.index('---', 1)
            metadata_str = '\n'.join(lines[1:metadata_end_index])
            metadata = yaml.safe_load(metadata_str)
            body = '\n'.join(lines[metadata_end_index + 1:])
            return metadata, body
        return {}, content

    def _create_full_content(self, metadata, body):
        """
        创建包含元数据和正文的完整笔记内容。
        
        :param metadata: 笔记的元数据
        :param body: 笔记的正文
        :return: 完整的笔记内容字符串
        """
        metadata_str = yaml.dump(metadata, allow_unicode=True)
        return f"---\n{metadata_str}---\n{body}"

    # def query_notes(self, query, doc_type='note'):
    #     """
    #     使用 DocumentProcessor 查询笔记。
        
    #     :param query: 查询条件
    #     :param doc_type: 文档类型，默认为 'note'
    #     :return: 查询结果
    #     """
    #     return self.doc_processor.query(query, doc_type)

    # def keyword_search_notes(self, keyword, doc_type='note'):
    #     """
    #     使用 DocumentProcessor 进行关键字搜索。
        
    #     :param keyword: 搜索关键字
    #     :param doc_type: 文档类型，默认为 'note'
    #     :return: 搜索结果
    #     """
    #     return self.doc_processor.keyword_search(keyword, doc_type)
    
if __name__ == "__main__":
    # 初始化 NoteManager 实例
    note_manager = NoteManager(sync_with_knowledge_base=False)

    # 保存笔记
    title1 = "Test Note 1"
    content1 = "This is the first test note."
    tags1 = ["test", "first"]

    print(f"Saving note: {title1}")
    note_manager.save_note(title1, content1, tags1)


    # 更新笔记
    new_title1 = "Updated Test Note 1"
    new_content1 = "This is the updated first test note."
    new_tags1 = ["updated", "first"]

    print(f"\nUpdating note: {title1}")
    try:
        updated_note = note_manager.update_note(title1, new_title1, new_content1, new_tags1)
        print(f"Updated note: {updated_note}")
    except ValueError as e:
        print(e)

    # 删除笔记
    print(f"\nDeleting note: {new_title1}")
    deleted1 = note_manager.delete_note(new_title1)
    print(f"Note deleted: {deleted1}")
