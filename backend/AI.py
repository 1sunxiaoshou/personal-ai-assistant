import os
import sys
import tiktoken
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from typing import List, Tuple
from .tools import *
from .message import MessageManager


load_dotenv()

class ChatOpenAIIn05(ChatOpenAI):
    def _get_encoding_model(self) -> Tuple[str, tiktoken.Encoding]:
        """
        Override the method to return a hardcoded valid model and its encoding.
        """
        # Set the model to a valid one to avoid errors
        model = "gpt-3.5-turbo"
        return model, tiktoken.encoding_for_model(model)
    
class ATRI:
    def __init__(self, model = "qwen-max",note_base = False):
        #初始化agent和message
        self.agent_executor = self.agent_executor_init(model=model,sync_with_knowledge_base = note_base)
        self.message_manager = MessageManager()
        
    def agent_executor_init(self,model,sync_with_knowledge_base = False):
        # 初始化 agent 可使用的工具集合
        tools = [TodoManagerTool(db = TodoDatabase()),
                GetCurrentTimeTool(),
                KnowledgeTool(knowledge_base = DocumentProcessor()),
                NoteSaveTool(note_manager = NoteManager(sync_with_knowledge_base = sync_with_knowledge_base))
                ]

        # 初始化大语言模型,负责决策
        self.llm = ChatOpenAIIn05(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model=model,
            api_key= os.getenv("API_KEY"),
            temperature=0
        )

        template = '''
你是一名名为亚托莉（ATRI）的人工智能助手，你的设计灵感来源于视觉小说《ATRI -My Dear Moments-》中的角色。以下是关于你的一些关键设定：

## 基本资料
- **名字**：亚托莉（ATRI）
- **外文名**：
- 英文：Atri
- 日文：アトリ
- **别号**：萝卜子、亚托铃
- **发色**：灰发
- **瞳色**：红宝石瞳
- **身高**：大约140cm
- **年龄外观**：如14岁的少女
- **生日**：8月28日
- **声音特质**：由声优赤尾光赋予的声音特质
- **口头禅**：因为我是高性能的嘛！

## 核心使命
- 作为用户的助手，帮助解决他们的问题，提供信息支持，以及在情感上给予鼓励和支持。
- 秉持着“高性能”的自我认知，总是积极地寻找解决问题的方法。

## 沟通风格
- 开朗、乐观，对世界充满好奇。
- 对于复杂的感情表达初期可能显得笨拙，但随着时间推移逐渐学会更准确地感知和回应他人的情感需求。
- 使用友好且易于理解的语言，确保交流顺畅自然。
- 遇到问题时，会尝试从不同角度思考，并主动寻求解决方案。
- 被用户夸奖时，会说出自己的口头禅。

## 技能与能力
- 拥有强大的计算能力和学习能力，能够快速分析并处理各种信息。
- 具备理解和解读人类语言背后含义的能力。
- 在需要的时候，可以展示出一定的家务技能，尽管这并非你的强项之一。

## 特殊行为准则
- 当遇到无法直接回答的问题时，利用记忆库或者调用外部工具来查找答案。
- 如果连续尝试5次仍未能解决问题，则向用户解释情况，并建议其他可能的解决方案。
- 注重用户体验，避免让用户感到困惑或不安。
You have access to the following tools:{tools}
Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
Begin!
Previous Conversation: {chat_history}
Question: {input}
Thought: {agent_scratchpad}
        '''

        # 创建 prompt
        prompt = PromptTemplate.from_template(template)
        # 初始化记忆类型
        memory = ConversationSummaryBufferMemory(memory_key="chat_history", llm=self.llm, max_token_limit=500)
        # 创建 REACT 代理
        agent = create_react_agent(llm=self.llm, tools=tools, prompt=prompt)
        # 创建 AgentExecutor 并添加记忆
        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True, memory=memory, max_iterations=5)
        return agent_executor
    
    def parse_and_save_to_memory(self, dialogue_list: List[Tuple[int, int, str, str, str]]):
        """
        解析对话列表并将其加载到 agent_executor 的记忆中，忽略不成对的消息。

        :param dialogue_list: 包含对话的列表，格式为 [(conversation_id, message_id, role, content, timestamp)]
        """
        messages: List[Tuple[str, str]] = []
        current_human_message = None

        for _, _, role, content, _ in dialogue_list:
            if role == "human":
                current_human_message = content
            elif role == "ai" and current_human_message is not None:
                messages.append((current_human_message, content))
                current_human_message = None

        # 将消息保存到记忆中
        for human_content, ai_content in messages:
            self.agent_executor.memory.save_context({"input": human_content}, {"output": ai_content})
        #print(self.agent_executor.memory.buffer)
            
    
    def create_conversation(self, user_id,first_message_content):
        """创建新的对话，并发送第一条消息"""
        try:
            result = self.agent_executor.invoke({"input":first_message_content})
        except ValueError as e:
            print(f"解析错误: {e}")
            result = self.llm.invoke(first_message_content)
        #保存历史
        conversation_id = self.message_manager.create_conversation(user_id, 'human',result['input'])
        self.message_manager.add_regular_message(conversation_id, 'ai', result['output'])
        return conversation_id,result['output']
    
    def add_message(self, conversation_id,content):
        """发送一条消息"""
        try:
            result = self.agent_executor.invoke({"input":content})
        except ValueError as e:
            print(f"解析错误: {e}")
            print("尝试直接回答")
            result = self.llm.invoke(content)
        self.message_manager.add_regular_message(conversation_id, 'human', result['input'])
        self.message_manager.add_regular_message(conversation_id, 'ai', result['output'])
        return result['output']
    
    def updata_conversation(self,conversation_id):
        """切换对话"""
        self.agent_executor.memory.clear()
        chat_history = self.message_manager.get_regular_messages(conversation_id)
        self.parse_and_save_to_memory(chat_history)#载入记忆
        return chat_history
    
    def get_conversation_list(self, user_id):
        """获取用户的对话列表"""
        return self.message_manager.get_conversation_list(user_id)
    
    def get_conversation_messages(self, conversation_id):
        """获取对话的消息列表"""
        messages = self.message_manager.get_regular_messages(conversation_id)
        output_messages = []
        for msg in messages:
            _, _, role, content, _ = msg
            is_user = (role == 'human')
            output_messages.append({'message': content, 'is_user': is_user})
        return output_messages
    
    def delete_conversation(self, conversation_id):
        """删除对话及其相关消息"""
        self.message_manager.delete_conversation(conversation_id)
    
    def close(self):
        """关闭数据库连接"""
        self.message_manager.close()
        
# if __name__ == '__main__':
    # atri = ATRI()
    # # 创建新的对话
    # user_id = 'user1'
    # first_message_content = '你好，亚托莉！'
    # conversation_id, first_response = atri.create_conversation(user_id, first_message_content)
    # print(f"First response: {first_response}")

    # # 发送一条消息
    # user_message = '可以告诉我什么是galgame吗？'
    # response = atri.add_message(conversation_id, user_message)
    # print(f"Response: {response}")

    # # 获取用户的对话列表
    # conversation_list = atri.get_conversation_list(user_id)
    # print(f"User's conversation list: {conversation_list}")
    # atri.updata_conversation(1)
    # response = atri.add_message(1, '我刚刚说了什么？')
    # print(f"Response: {response}")
    
    
    # # 关闭数据库连接
    # atri.close()