# 🤖 大模型本地化部署系统

一个完整的本地化大模型部署解决方案，支持GPU加速、多模型管理、资源监控等功能。

## ✨ 特性

- 🚀 **GPU加速**: 基于Ollama的GPU加速推理
- 🎯 **多模型支持**: Qwen、DeepSeek等多种模型
- 📊 **资源监控**: 实时监控GPU、存储、系统资源
- 🎨 **现代界面**: React + TypeScript + Ant Design
- 🐳 **Docker部署**: 一键部署，跨平台运行
- 🔧 **完整API**: RESTful API + WebSocket支持

## 🚀 快速开始

### 方式1: Docker部署（推荐）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd llm-local-backend

# 2. 一键部署
chmod +x build_docker.sh
./build_docker.sh

# 3. 访问服务
# 主页面: http://localhost:8080
```

### 方式2: 本地部署

```bash
# 1. 安装依赖
pip install -r requirements.txt
cd frontend && npm install

# 2. 启动服务
./start_all.sh

# 3. 访问服务
# 前端: http://localhost:3000
# 后端: http://localhost:8000
```

## 📱 功能模块

### 1. 智能Agent
- 与本地大模型对话
- 支持流式响应
- 多模型切换

### 2. 算力资源管理
- GPU状态监控
- 任务队列管理
- 性能指标展示

### 3. 存储资源管理
- 文件上传下载
- 存储空间监控
- 目录浏览

### 4. 系统资源管理
- 系统状态监控
- 进程管理
- 网络状态

### 5. 模型服务管理
- 多模型服务
- 服务健康检查
- 性能监控

## 🛠️ 技术栈

- **后端**: FastAPI + Python + Ollama
- **前端**: React + TypeScript + Ant Design + Vite
- **数据库**: SQLite
- **缓存**: Redis
- **部署**: Docker + Docker Compose
- **代理**: Nginx

## 📊 系统要求

### 最低要求
- CPU: 4核心
- 内存: 8GB
- 存储: 20GB
- 系统: Linux/macOS/Windows

### 推荐配置
- CPU: 8核心
- 内存: 16GB
- 存储: 50GB
- GPU: NVIDIA GPU (8GB+ VRAM)
- 系统: Ubuntu 20.04+

## 🔧 配置说明

### 环境变量
```bash
# Ollama配置
OLLAMA_HOST=localhost:11434

# 模型配置
DEFAULT_MODEL=qwen2.5:7b

# 安全配置
SECRET_KEY=your-secret-key
```

### 模型下载
```bash
# 安装Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 下载模型
ollama pull qwen2.5:7b
ollama pull deepseek-coder:6.7b
```

## 📁 项目结构

```
llm-local-backend/
├── 🐳 Docker部署
│   ├── Dockerfile              # 多阶段构建
│   ├── docker-compose.yml      # 服务编排
│   ├── build_docker.sh         # 一键部署脚本
│   └── DOCKER_DEPLOYMENT.md    # Docker部署文档
│
├── 🚀 启动脚本
│   ├── start_all.sh            # 一键启动前后端
│   ├── stop_all.sh             # 停止所有服务
│   └── quick_start.sh          # 快速启动
│
├── 🐍 后端核心
│   ├── main.py                 # FastAPI主程序
│   ├── requirements.txt        # Python依赖
│   └── config/settings.py      # 配置文件
│
├── 🔌 API接口
│   └── api/routes/
│       ├── chat.py             # 聊天对话API
│       ├── computing.py        # 算力资源管理API
│       ├── storage.py          # 存储资源管理API
│       ├── system.py           # 系统资源管理API
│       └── model_service.py    # 模型服务管理API
│
├── 🤖 模型服务
│   └── model_service/
│       ├── ollama_manager.py   # Ollama模型管理器
│       ├── model_manager.py    # 原始模型管理器
│       └── simple_model_manager.py # 简化模型管理器
│
├── 🎨 前端应用
│   └── frontend/
│       ├── package.json        # 前端依赖
│       └── src/
│           ├── App.tsx         # 主应用组件
│           ├── services/api.ts # API服务类
│           └── pages/          # 页面组件
│
└── 📊 数据目录
    ├── models/                 # 模型文件
    ├── uploads/                # 上传文件
    ├── logs/                   # 日志文件
    └── llm_backend.db          # 数据库
```

## 🔍 API文档

启动服务后访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 主要API端点

- `POST /api/v1/chat` - 聊天对话
- `GET /api/v1/computing/gpus` - 获取GPU信息
- `GET /api/v1/storage/devices` - 获取存储设备
- `GET /api/v1/system/info` - 获取系统信息
- `GET /api/v1/model-service/services` - 获取模型服务

## 🛠️ 开发指南

### 本地开发
```bash
# 后端开发
python3 start.py

# 前端开发
cd frontend
npm run dev
```

### 添加新功能
1. 在 `api/routes/` 中添加新的API路由
2. 在 `frontend/src/pages/` 中添加新的页面组件
3. 在 `frontend/src/services/api.ts` 中添加API调用

## 🔒 安全注意事项

1. **修改默认配置**: 更改默认密码和密钥
2. **网络访问**: 限制外部访问
3. **数据备份**: 定期备份模型和数据库
4. **日志监控**: 监控系统日志

## 📈 性能优化

1. **GPU加速**: 使用NVIDIA GPU进行推理加速
2. **模型量化**: 使用int8/int4量化减少内存占用
3. **缓存优化**: 配置Redis缓存
4. **负载均衡**: 使用Nginx进行负载均衡

## 🆘 故障排除

### 常见问题

1. **服务无法启动**
   - 检查端口占用
   - 查看日志文件
   - 验证依赖安装

2. **模型加载失败**
   - 检查Ollama服务
   - 验证模型文件
   - 查看GPU状态

3. **前端无法访问**
   - 检查前端服务状态
   - 验证API连接
   - 查看浏览器控制台

### 获取帮助

- 查看日志: `logs/backend.log` 和 `logs/frontend.log`
- 检查服务状态: `docker compose ps`
- 提交Issue到项目仓库

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎提交Issue和Pull Request！

---

**注意**: 这是一个本地化部署解决方案，请确保在安全的环境中运行。