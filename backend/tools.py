from .Todo import TodoDatabase
from .VectorStor import DocumentProcessor
from .note import NoteManager
from langchain.tools import BaseTool
import datetime
from typing import List, Any
import json

class TodoManagerTool(BaseTool):
    name: str = "todo_manager"
    description: str = (
        "用于管理待办事项的工具。\n"
        "支持的操作包括：\n"
        "- 添加新的待办事项\n"
        "- 标记指定ID的待办事项为已完成\n"
        "- 删除指定ID的待办事项\n"
        "- 获取所有待办事项\n"
        "- 获取所有未完成的待办事项\n"
        "- 通过描述模糊查询待办事项\n"
        "\n参数：\n"
        "- mode: 指定操作的模式，包括add、mark_completed、delete、get_all、get_incomplete和search_by_description。\n"
        "- title: 待办事项的任务标题（仅用于add操作）。\n"
        "- description: 待办事项的描述（可选，仅用于add和search_by_description操作）。\n"
        "- due_date: 待办事项的截止日期（可选，仅用于add操作,格式为'YYYY-MM-DD'.）。\n"
        "- task_id: 待办事项的ID（仅用于mark_completed和delete操作）。\n"
        "- description_pattern: 描述模式，使用SQL LIKE语法（仅用于search_by_description操作）。"
    )
    
    db: TodoDatabase  # 定义db字段，并指定其类型为TodoDatabase

    def _run(self, input: str) -> str:
        input_dict = eval(input)
        if 'mode' not in input_dict:
            return "缺少必要的mode参数"

        mode = input_dict['mode']

        try:
            if mode == 'add':
                if 'title' not in input_dict:
                    return "添加待办事项需要title参数"
                
                title = input_dict['title']
                description = input_dict.get('description')
                due_date = input_dict.get('due_date')
                if due_date:
                    due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
                
                self.db.add_task(title, description, due_date)
                return f"已添加待办事项: {title}"
            
            elif mode == 'mark_completed':
                if 'task_id' not in input_dict:
                    return "标记待办事项为已完成需要task_id参数"
                
                task_id = input_dict['task_id']
                self.db.mark_task_as_completed(task_id)
                return f"已将待办事项ID {task_id} 标记为已完成"
            
            elif mode == 'delete':
                if 'task_id' not in input_dict:
                    return "删除待办事项需要task_id参数"
                
                task_id = input_dict['task_id']
                self.db.delete_task(task_id)
                return f"已删除待办事项ID {task_id}"
            
            elif mode == 'get_all':
                all_tasks = self.db.get_all_tasks()
                return "\n".join([str(task) for task in all_tasks]) if all_tasks else "没有待办事项"
            
            elif mode == 'get_incomplete':
                incomplete_tasks = self.db.get_incomplete_tasks()
                return "\n".join([str(task) for task in incomplete_tasks]) if incomplete_tasks else "没有未完成的待办事项"
            
            elif mode == 'search_by_description':
                if 'description_pattern' not in input_dict:
                    return "通过描述模糊查询待办事项需要description_pattern参数"
                
                description_pattern = input_dict['description_pattern']
                matching_tasks = self.db.search_tasks_by_description(description_pattern)
                return "\n".join([str(task) for task in matching_tasks]) if matching_tasks else "没有匹配的待办事项"
            
            else:
                return "未知的命令模式"
        
        except Exception as e:
            return f"执行操作时发生错误: {str(e)}"

class GetCurrentTimeTool(BaseTool):
    name: str = "get_current_time"
    description: str = "一个用来获取当前系统时间的工具"

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """Actual method that runs when the tool is called."""
        # 获取当前时间
        now = datetime.datetime.now()
        # 格式化时间字符串
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        return f"当前时间为: {formatted_now}."

class KnowledgeTool(BaseTool):
    name: str = "知识库检索"
    description: str = "一个用来检索知识库中相似文本的工具"
    knowledge_base:DocumentProcessor

    def _run(self, query: str) -> List[str]:
        """
        执行知识库搜索。
        
        :param query: 查询的问题
        :return: 匹配的文档片段列表
        """
        documents = self.knowledge_base.query(query,'all')
        
        return [doc.page_content for doc in documents]

class GetCurrentTimeTool(BaseTool):
    name: str = "get_current_time"
    description: str = "一个用来获取当前系统时间的工具"

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """Actual method that runs when the tool is called."""
        # 获取当前时间
        now = datetime.datetime.now()
        # 格式化时间字符串
        formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        return f"当前时间为: {formatted_now}."

class NoteSaveTool(BaseTool):
    name: str = "note_save"
    description: str = "根据传入的json来解析title、content、tags并保存到笔记库中.其中content是markdown格式的笔记文本"
    note_manager: NoteManager

    def _run(self, input_json: str) -> str:
        """
        执行笔记保存。
        
        :param input_json: 包含title、content和tags的JSON字符串
        :return: 成功或失败的消息
        """
        try:
            # 解析JSON输入
            data = json.loads(input_json)
            
            # 提取参数
            title = data.get('title')
            content = data.get('content')
            tags = data.get('tags', [])
            
            # 检查必需的参数
            if not title or not content:
                return "缺少必要的参数: title 或 content"
            
            # 保存笔记
            self.note_manager.save_note(title, content, tags=tags)
            return "保存成功"
        except json.JSONDecodeError:
            return "无效的JSON格式"
        except Exception as e:
            return f"保存失败: {str(e)}"