---
content: "# 个人AI助手\n\n## 项目概述\n这是一个个人AI助手项目，提供多种功能，如智能问答、笔记生成、待办事项管理等。\n\n### 说明\n\
  \n- **README.md**: 项目说明文档，提供项目的概述、目录结构、安装步骤和运行指南。\n- **requirements.txt**: 列出所有Python依赖包及其版本。\n\
  - **.env**: 存储环境变量，如API密钥、数据库连接字符串等。\n- **.gitignore**: 指定Git应该忽略的文件和目录，例如虚拟环境、缓存文件等。\n\
  \n### 其他文件和目录\n\n- **frontend/**: 前端代码目录，包含PyQt5界面和相关组件。\n  - **assets/**: 静态资源文件，如图片、样式表等。\n\
  \  - **src/**: 源代码目录。\n    - **components/**: UI组件。\n    - **utils/**: 工具函数。\n \
  \   - **main.py**: 主程序入口。\n  - **config.py**: 配置文件。\n  - **ui_design/**: UI设计图。\n\
  \n- **backend/**: 后端代码目录，包含Flask应用和API接口。\n  - **app.py**: Flask应用主文件。\n  - **api/**:\
  \ API接口定义。\n    - **__init__.py**: 初始化API蓝图。\n    - **qa_api.py**: 智能问答API。\n  \
  \  - **note_api.py**: 文档笔记生成API。\n    - **todo_api.py**: 待办事项管理API。\n    - **kb_api.py**:\
  \ 本地知识库API。\n    - **search_api.py**: 快速检索API。\n  - **models/**: 数据库模型。\n  - **services/**:\
  \ 业务逻辑层。\n    - **qa_service.py**: 智能问答服务。\n    - **note_service.py**: 文档笔记生成服务。\n\
  \    - **todo_service.py**: 待办事项管理服务。\n    - **kb_service.py**: 本地知识库服务。\n    -\
  \ **search_service.py**: 快速检索服务。\n  - **utils/**: 工具函数。\n  - **config.py**: 配置文件。\n\
  \n- **data/**: 数据存储目录。\n  - **user_data/**: 用户数据。\n  - **model_data/**: AI模型数据。\n\
  \n- **tests/**: 测试代码目录。\n  - **test_frontend/**: 前端测试。\n  - **test_backend/**: 后端测试。\n\
  \    - **test_api.py**: API测试。\n    - **test_services/**: 服务层测试。\n\n希望这个文档对你有帮助！如果有任何进一步的问题或需要更多的详细信息，请告诉我。"
created_at: '2024-11-10T12:42:20.228375+00:00'
filename: README.md
tags:
- 文档
- 项目说明
title: README
updated_at: '2024-11-28T11:37:02.147281+00:00'
---
# 个人AI助手

## 项目概述
这是一个个人AI助手项目，提供多种功能，如智能问答、笔记生成、待办事项管理等。

### 说明

- **README.md**: 项目说明文档，提供项目的概述、目录结构、安装步骤和运行指南。
- **requirements.txt**: 列出所有Python依赖包及其版本。
- **.env**: 存储环境变量，如API密钥、数据库连接字符串等。
- **.gitignore**: 指定Git应该忽略的文件和目录，例如虚拟环境、缓存文件等。

### 其他文件和目录

- **frontend/**: 前端代码目录，包含PyQt5界面和相关组件。
  - **assets/**: 静态资源文件，如图片、样式表等。
  - **src/**: 源代码目录。
    - **components/**: UI组件。
    - **utils/**: 工具函数。
    - **main.py**: 主程序入口。
  - **config.py**: 配置文件。
  - **ui_design/**: UI设计图。

- **backend/**: 后端代码目录，包含Flask应用和API接口。
  - **app.py**: Flask应用主文件。
  - **api/**: API接口定义。
    - **__init__.py**: 初始化API蓝图。
    - **qa_api.py**: 智能问答API。
    - **note_api.py**: 文档笔记生成API。
    - **todo_api.py**: 待办事项管理API。
    - **kb_api.py**: 本地知识库API。
    - **search_api.py**: 快速检索API。
  - **models/**: 数据库模型。
  - **services/**: 业务逻辑层。
    - **qa_service.py**: 智能问答服务。
    - **note_service.py**: 文档笔记生成服务。
    - **todo_service.py**: 待办事项管理服务。
    - **kb_service.py**: 本地知识库服务。
    - **search_service.py**: 快速检索服务。
  - **utils/**: 工具函数。
  - **config.py**: 配置文件。

- **data/**: 数据存储目录。
  - **user_data/**: 用户数据。
  - **model_data/**: AI模型数据。

- **tests/**: 测试代码目录。
  - **test_frontend/**: 前端测试。
  - **test_backend/**: 后端测试。
    - **test_api.py**: API测试。
    - **test_services/**: 服务层测试。

希望这个文档对你有帮助！如果有任何进一步的问题或需要更多的详细信息，请告诉我。