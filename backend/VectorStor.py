import os
import uuid
import markdown
import dashscope

from pathlib import Path
from http import HTTPStatus
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.chat_models import ChatTongyi
from typing import Optional,Dict, List, Generator, Any,Union
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader,PyPDFLoader,Docx2txtLoader


# 加载环境变量
load_dotenv()
dashscope.api_key = os.getenv("API_KEY")

# markdown加载器
class MarkdownLoader(TextLoader):
    def __init__(self, file_path: Union[str, Path], encoding: Optional[str] = None, autodetect_encoding: bool = False):
        """Initialize with file path and optional encoding and autodetection flag."""
        super().__init__(file_path, encoding=encoding, autodetect_encoding=autodetect_encoding)

    @staticmethod
    def _remove_markdown(text: str) -> str:
        """ 将Markdown文本转换为HTML，然后从中提取纯文本。 """
        html = markdown.markdown(text)
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text()

    def load(self) -> List[Document]:
        """ 加载文件并将Markdown转换为纯文本。 """
        documents = []
        for doc in self.lazy_load():
            text_content = self._remove_markdown(doc.page_content)
            metadata = doc.metadata
            documents.append(Document(page_content=text_content, metadata=metadata))
        return documents

# 嵌入api-自动批处理
class QwenEmbeddingFunction:
    DASHSCOPE_MAX_BATCH_SIZE = 25  # 最多支持25条，每条最长支持2048tokens
    
    def __call__(self, input: List[str], text_type: str = "document") -> List[List[float]]:
        embeddings = []
        for batch in self.batched(input, batch_size=self.DASHSCOPE_MAX_BATCH_SIZE):
            resp = self.embed_with_list_of_str(batch, text_type)
            if resp and resp.status_code == HTTPStatus.OK:
                embeddings.extend([emb['embedding'] for emb in resp.output['embeddings']])
            else:
                print(f"Error in embedding: {resp}")
        return embeddings
    
    @staticmethod
    def batched(inputs: List[Any], batch_size: int = DASHSCOPE_MAX_BATCH_SIZE) -> Generator[List[Any], None, None]:
        for i in range(0, len(inputs), batch_size):
            yield inputs[i:i + batch_size]
    
    def embed_with_list_of_str(self, inputs: List[str], text_type: str) -> Any:
        result = None
        for batch in self.batched(inputs, batch_size=self.DASHSCOPE_MAX_BATCH_SIZE):
            resp = dashscope.TextEmbedding.call(
                model=dashscope.TextEmbedding.Models.text_embedding_v2,
                input=batch,
                text_type=text_type  # 指定文本类型
            )
            if resp.status_code == HTTPStatus.OK:
                if result is None:
                    result = resp
                else:
                    for emb in resp.output['embeddings']:
                        emb['text_index'] += len(result.output['embeddings'])
                        result.output['embeddings'].append(emb)
                    result.usage['total_tokens'] += resp.usage['total_tokens']
            else:
                print(f"Error in embedding batch: {resp}")
        return result

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self(texts, text_type="document")

    def embed_query(self, texts: List[str]) -> List[List[float]]:
        return self(texts, text_type="query")[0]

# 知识库管理
class DocumentProcessor:
    def __init__(self, persist_directory: str = os.getenv("vector_db_path")):
        self.persist_directory = persist_directory
        self.llm = ChatTongyi(model="qwen2.5-3b-instruct", api_key=os.getenv("API_KEY"))
        self.embedding_function = QwenEmbeddingFunction()
        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=0)
        
        # 初始化三个集合
        self.summary_client = Chroma(
            collection_name="summaries",
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )
        self.document_client = Chroma(
            collection_name="documents",
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )
        self.note_client = Chroma(
            collection_name="notes",
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function
        )

    def validate_doc_type(self, doc_type: str) -> None:
        """
        验证 doc_type 是否合法。
        
        :param doc_type: 文档类型，'note' 或 'document' 或 'all'
        :raises ValueError: 如果 doc_type 不合法
        """
        valid_types = ['note', 'document','all']
        if doc_type not in valid_types:
            raise ValueError(f"无效的 doc_type: {doc_type}. 合法的值有: {', '.join(valid_types)}")
        
    # 生成摘要
    def generate_summary(self, text: str) -> str:
        """
        使用提示词生成文本的摘要。
        
        :param text: 需要生成摘要的文本
        :return: 生成的摘要
        """
        prompt = f"请为以下文本生成一个简明扼要的摘要，概括主要观点和关键信息。摘要长度通常150字左右，可以根据实际情况调整：\n{text}"
        response = self.llm.invoke(prompt).content
        return response

    # 获取文档列表
    def get_document_list(self, doc_type: str) -> List[str]:
        """
        获取所有文档的源路径列表。
        
        :param doc_type: 文档类型，'note' 或 'document' 或 'all'
        :return: 文档源路径列表
        """
        self.validate_doc_type(doc_type)
        
        if doc_type == "all":
            results = self.summary_client.get(include=["metadatas"])
        else:
            results = self.summary_client.get(include=["metadatas"], where={'type': doc_type})
        document_list = [metadata['source'] for metadata in results.get("metadatas", [])]
        return document_list
    
    # 插入文档列表
    def load_and_embed_documents(self, document_paths: List[str], doc_type: str) -> None:
        
        self.validate_doc_type(doc_type)
        
        for document_path in document_paths:
            try:
                # 检查是否已存在相同文档名的文档
                if self.document_exists(document_path, doc_type):
                    print(f"文档已存在于{doc_type}: {document_path}")
                    continue
                
                # 根据文件类型选择合适的加载器
                if document_path.endswith('.md'):
                    loader = MarkdownLoader(document_path, autodetect_encoding=True)
                elif document_path.endswith('.txt'):
                    loader = TextLoader(document_path, autodetect_encoding=True)
                elif document_path.endswith('.pdf'):
                    loader = PyPDFLoader(document_path)
                elif document_path.endswith('.docx'):
                    loader = Docx2txtLoader(document_path)
                else:
                    raise ValueError("未知类型文档. 当前仅支持 .md, .txt, .pdf 和 .docx 格式的文档")

                documents = loader.load()
                text = documents[0].page_content

                # 生成摘要
                summary = self.generate_summary(text)
                
                # 存储摘要
                self.summary_client.add_texts(texts=[summary], metadatas=[{'source': document_path, 'type': doc_type}], ids=[str(uuid.uuid4())])

                # 分割文本
                split_texts = self.text_splitter.split_text(text)
                document_ids = [str(uuid.uuid4()) for _ in range(len(split_texts))]
                metadatas = [{'source': document_path, 'type': doc_type}] * len(split_texts)

                # 存储文档切分
                client = self.note_client if doc_type == 'note' else self.document_client
                client.add_texts(texts=split_texts, metadatas=metadatas, ids=document_ids)
                print(f"成功处理文档: {document_path}")

            except Exception as e:
                print(f"处理文档时出错: {document_path}, 错误: {e}")

    # 检查文档是否存在
    def document_exists(self, document_path: str, doc_type: str) -> bool:
        """
        检查文档是否已存在于数据库中。
        
        :param document_path: 文档路径
        :param doc_type: 文档类型，'note' 或 'document' 或 'all'
        :return: 如果文档已存在，返回True；否则返回False
        """
        if doc_type == "all":
            results = self.summary_client.get(where={'source': document_path})
        else:
            results = self.summary_client.get(where={'$and': [{'source': document_path}, {'type': doc_type}]})
        return len(results['ids']) > 0
    
    # 删除指定文档及其摘要
    def delete_document(self, document_paths: Union[str, List[str]], doc_type: str) -> None:
            """
            删除指定文档及其摘要。
            
            :param document_paths: 要删除的文档的路径，可以是单个路径（str）或多个路径（list）
            :param doc_type: 文档类型，'note' 或 'document'
            """
            self.validate_doc_type(doc_type)
            
            if isinstance(document_paths, str):
                document_paths = [document_paths]

            for document_path in document_paths:
                try:
                    # 获取要删除的摘要的ID
                    summary_results = self.summary_client.get(where={'$and': [{'source': document_path}, {'type': doc_type}]}, include=[])
                    summary_ids = summary_results.get('ids', [])

                    # 获取要删除的文档切分的ID
                    client = self.note_client if doc_type == 'note' else self.document_client
                    document_results = client.get(where={'source': document_path}, include=[])
                    document_ids = document_results.get('ids', [])

                    # 删除摘要和切分
                    if summary_ids or document_ids:
                        if summary_ids:
                            self.summary_client.delete(ids=summary_ids)
                        if document_ids:
                            client.delete(ids=document_ids)
                        print(f"成功删除文档: {document_path}")
                    else:
                        print(f"未找到文档: {document_path}")
                except Exception as e:
                    print(f"删除文档时出错: {document_path}, 错误: {e}")
                    
    def query(self, query: str, doc_type: str = 'all') -> List[dict]:
        """
        查询文档。
        
        :param query: 查询字符串
        :param doc_type: 文档类型，'all', 'note' 或 'document'
        :return: 查询结果
        """
        self.validate_doc_type(doc_type)
        
        try:
            document_results = []
            if doc_type == 'all':
                # 全局查询
                summary_results = self.summary_client.search(query, search_type="similarity", k=1)
                for result in summary_results:
                    source = result.metadata['source']
                    if result.metadata['type'] == 'document':
                        document_results.extend (self.document_client.similarity_search(query,filter = {'source':source}))
                    else:
                        document_results.extend(self.note_client.similarity_search(query,filter = {'source':source}))

            else:
                # 特定类型查询
                client = self.note_client if doc_type == 'note' else self.document_client
                summary_results = self.summary_client.search(query, search_type="similarity", k=1, where={'type': doc_type})
                sources = [result.metadata['source'] for result in summary_results]
                for source in sources:
                    document_results.extend(client.similarity_search(query, filter={'source': source}))

            return document_results
        except Exception as e:
            print(f"查询时出错: {e}")
            return []
    
    def get_document_content(self, document_path: str, doc_type: str = 'all') -> Dict:
        """
        根据文档路径获取文档内容。
        
        :param document_path: 要检索的文档路径
        :param doc_type: 文档类型，'all', 'note' 或 'document'
        :return: 文档内容列表，每个元素包含文档片段及其元数据
        """
        self.validate_doc_type(doc_type)
        
        try:
            # 获取文档的摘要信息
            if doc_type == 'all':
                summary_results = self.summary_client.get(where={'source': document_path}, include=["metadatas"])
            else:
                summary_results = self.summary_client.get(where={'$and': [{'source': document_path}, {'type': doc_type}]}, include=["metadatas"])
            
            # 如果没有找到摘要，说明文档不存在
            if not summary_results.get("metadatas", []):
                print(f"未找到文档: {document_path}")
                return []

            # 获取文档片段
            document_results = []
            for summary in summary_results["metadatas"]:
                source = summary['source']
                if summary['type'] == 'document':
                    client = self.document_client
                else:
                    client = self.note_client
                results = client.get(where={'source': source}, include=["documents", "metadatas"])
                document_results.extend(results.get("documents", []))

            return {'texts':document_results,'metadatas':summary_results["metadatas"]}

        except Exception as e:
            print(f"获取文档内容时出错: {e}")
            return {'texts':None,'metadatas':None}
    
    # 关键字检索
    def keyword_search(self, keyword: str, doc_type: str = 'all') -> List[dict]:
        """
        根据关键字检索文档。
        
        :param keyword: 关键字
        :param doc_type: 文档类型，'all', 'note' 或 'document'
        :return: 匹配的文档列表
        """
        try:
            if doc_type == 'all':
                # 全局查询
                document_results = self.document_client.get(where_document={"$contains": keyword}, include=["metadatas", "documents"])
                note_results = self.note_client.get(where_document={"$contains": keyword}, include=["metadatas", "documents"])
                results = document_results['documents']+ note_results['documents']
            else:
                self.validate_doc_type(doc_type)
                # 特定类型查询
                client = self.note_client if doc_type == 'note' else self.document_client
                results = client.get(where_document={"$contains": keyword}, include=["metadatas", "documents"])['documents']

            return results
        except Exception as e:
            print(f"关键字检索时出错: {e}")
            return []


# 示例用法
if __name__ == "__main__":
    # 初始化文档处理器
    doc_processor = DocumentProcessor()

    # 加载并嵌入多个文档
    document_paths = ['自然语言处理（NLP）简介.docx','自然语言处理（NLP）入门指南.pdf']  # 请替换为实际的文档路径
    doc_processor.load_and_embed_documents(document_paths,doc_type='document')

    # # 查询
    # query_text = "情感分析"
    # results = doc_processor.query(query_text,'all')
    # for result in results:
    #     print(f"Document Text: {result.page_content}")
    #     # print(f"Metadata: {result.metadata}")
    #     print("-" * 50)
    
    # 获取文档列表
    document_list = doc_processor.get_document_list(doc_type = 'note')
    print(document_list)
    
    # # 删除文档
    # doc_processor.delete_document(document_list,"note")
    # doc_processor.delete_document(document_list,'document')

    # # 关键字检索
    # results = doc_processor.keyword_search(query_text,'all')
    # [print(i) for i in results]


"""
修改建议： 
    1.对每一个分块生成查询问题用来匹配
    2.改为直接查询
    3.查询优化-在进行文档总结时也提炼一些关键字进行正则匹配，可以加快查询，但准确率是上升还是下降未知，得进行评估
    4.修改分割方法，采用更好的分割来提高文本间的独立性，去除冗余
    5.寻找评估方式，来评估检索、生成
"""
