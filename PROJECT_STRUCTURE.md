# 大模型本地化项目结构

## 📁 核心文件结构

```
llm-local-backend/
├── 📄 启动脚本
│   ├── start_all.sh          # 一键启动前后端
│   ├── stop_all.sh           # 停止所有服务
│   ├── quick_start.sh        # 快速启动脚本
│   └── start.py              # 后端启动脚本
│
├── 🐍 后端核心
│   ├── main.py               # FastAPI主程序
│   ├── requirements.txt      # Python依赖
│   └── config/
│       └── settings.py       # 配置文件
│
├── 🔌 API接口
│   └── api/routes/
│       ├── chat.py           # 聊天对话API
│       ├── computing.py      # 算力资源管理API
│       ├── storage.py        # 存储资源管理API
│       ├── system.py         # 系统资源管理API
│       ├── model_service.py  # 模型服务管理API
│       ├── model_management.py # 模型管理API
│       ├── health.py         # 健康检查API
│       └── training.py       # 训练API
│
├── 🤖 模型服务
│   └── model_service/
│       ├── ollama_manager.py     # Ollama模型管理器（GPU加速）
│       ├── model_manager.py      # 原始模型管理器
│       └── simple_model_manager.py # 简化模型管理器
│
├── 🛠️ 工具类
│   └── utils/
│       ├── database.py       # 数据库工具
│       └── logger.py         # 日志工具
│
├── 🎨 前端应用
│   └── frontend/
│       ├── package.json      # 前端依赖
│       ├── vite.config.ts    # Vite配置
│       ├── tsconfig.json     # TypeScript配置
│       └── src/
│           ├── App.tsx       # 主应用组件
│           ├── main.tsx      # 入口文件
│           ├── services/
│           │   └── api.ts    # API服务类
│           └── pages/
│               ├── AgentChatPage.tsx        # 智能Agent页面
│               ├── ComputingResourcePage.tsx # 算力资源管理页面
│               ├── StorageResourcePage.tsx   # 存储资源管理页面
│               ├── SystemResourcePage.tsx    # 系统资源管理页面
│               ├── ModelServicePage.tsx      # 模型服务管理页面
│               └── LoginPage.tsx             # 登录页面
│
├── 📊 数据目录
│   ├── models/               # 模型文件目录
│   ├── uploads/              # 上传文件目录
│   ├── logs/                 # 日志文件目录
│   └── llm_backend.db        # SQLite数据库
│
└── 📚 文档
    ├── README.md             # 项目说明
    └── PROJECT_STRUCTURE.md  # 项目结构说明（本文件）
```

## 🚀 快速启动

### 方法1：一键启动
```bash
./start_all.sh
```

### 方法2：快速启动
```bash
./quick_start.sh
```

### 方法3：手动启动
```bash
# 启动后端
source .env.optimized && python3 start.py &

# 启动前端
cd frontend && npm run dev &
```

## 📱 访问地址

- **前端页面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🎯 核心功能

1. **智能Agent**: 与本地大模型对话
2. **算力资源管理**: 监控GPU和任务
3. **存储资源管理**: 管理文件和存储
4. **系统资源管理**: 查看系统状态
5. **模型服务管理**: 管理多个模型

## 🔧 技术栈

- **后端**: FastAPI + Python + Ollama
- **前端**: React + TypeScript + Ant Design + Vite
- **模型**: Qwen2.5:7b (GPU加速)
- **数据库**: SQLite
- **部署**: 本地部署

## 📝 注意事项

- 确保已安装Node.js和Python3
- 确保Ollama服务正在运行
- 首次启动前端需要运行 `npm install`
- 所有API接口都已实现并测试通过
