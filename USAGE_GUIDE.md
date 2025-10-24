# 大模型本地化系统使用指南

## 方式一：使用Docker封装包（推荐）

### 获取部署包

**当前可用的部署包：**
```bash
# 部署包位置
/media/cring/mydrive/llm-local-backend-20250117-220000.tar.gz (约50MB)

# 包含内容
✅ 完整的源代码（包含最新修复）
✅ Docker配置文件  
✅ 启动脚本
✅ 部署文档
✅ 自动安装脚本
✅ 测试脚本
✅ 混合模型管理器
✅ 前端滚动优化
✅ 流式聊天API修复
```

### 🚀 在任何机器上部署

**步骤1：传输部署包**
```bash
# 方法1：使用scp
scp /media/cring/mydrive/llm-local-backend-20250117-220000.tar.gz user@target-machine:/home/user/

# 方法2：使用U盘或其他方式复制
# 将文件复制到目标机器
```

**步骤2：在目标机器上部署**
```bash
# 1. 解压部署包
tar -xzf llm-local-backend-20250117-220000.tar.gz
cd llm-local-backend-20250117-220000

# 2. 一键安装（自动完成所有配置）
chmod +x install.sh
./install.sh
```

**步骤3：访问服务**
```bash
# 主页面
http://localhost:8080

# API文档
http://localhost:8000/docs
```

### 🎯 优势
- ✅ **零配置**：自动安装所有依赖
- ✅ **跨平台**：支持Linux、macOS、Windows
- ✅ **完整环境**：包含Ollama、模型、服务
- ✅ **一键部署**：无需手动配置
- ✅ **多模型支持**：同时支持Ollama和Transformers模型
- ✅ **流式聊天**：实时流式响应，更好的用户体验
- ✅ **前端优化**：自动滚动、响应式设计
- ✅ **混合管理**：智能模型类型检测和切换

---

## 🛠️ 方式二：直接使用已部署的大模型

### 📍 当前部署状态

**服务状态：**
- ✅ 后端服务：http://localhost:8000 （运行中）
- ✅ 前端服务：http://localhost:3001 （运行中）
- ✅ 混合模型管理器：支持Ollama和Transformers模型
- ✅ 可用模型：qwen2.5:7b, llama2:latest, DeepSeek-R1-Distill-Qwen-7B

### 🎨 1. Web界面使用

**访问地址：**
```bash
# 主页面
http://localhost:3001

# 功能模块
- 智能Agent：与模型对话（支持多模型切换、流式响应、自动滚动）
- 算力资源管理：GPU监控、任务管理
- 存储资源管理：文件管理、上传下载
- 系统资源管理：系统监控、性能分析
- 模型服务管理：模型管理、服务监控
```

### 🔌 2. API直接调用

**聊天对话API：**
```bash
# 普通对话
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "你好，请介绍一下你自己"}],
    "stream": false
  }'

# 流式对话
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "请写一首诗"}],
    "stream": true
  }'
```

**其他API：**
```bash
# 获取可用模型
curl http://localhost:8000/api/v1/models

# 获取系统信息
curl http://localhost:8000/api/v1/system/info

# 获取GPU信息
curl http://localhost:8000/api/v1/computing/gpus

# 模型管理API
curl http://localhost:8000/api/v1/models                    # 获取模型列表
curl http://localhost:8000/api/v1/models/current            # 获取当前模型
curl -X POST http://localhost:8000/api/v1/models/switch \   # 切换模型
  -H "Content-Type: application/json" \
  -d '{"model_name": "qwen2.5:7b"}'

# 健康检查
curl http://localhost:8000/api/v1/health
```

### 🐍 3. Python脚本调用

**使用示例脚本：**
```bash
# 运行完整示例
python3 example_usage.py

# 功能包括：
- 服务状态检查
- 模型列表获取和切换
- 系统信息查询
- 交互式对话
- 流式聊天测试
- 多模型支持验证
```

**自定义Python脚本：**
```python
import requests

# 发送消息
def chat(message):
    response = requests.post(
        "http://localhost:8000/api/v1/chat",
        json={"messages": [{"role": "user", "content": message}]}
    )
    return response.json()["message"]

# 获取模型列表
def get_models():
    response = requests.get("http://localhost:8000/api/v1/models")
    return response.json()

# 切换模型
def switch_model(model_name):
    response = requests.post(
        "http://localhost:8000/api/v1/models/switch",
        json={"model_name": model_name}
    )
    return response.json()

# 流式聊天
def chat_stream(message):
    response = requests.post(
        "http://localhost:8000/api/v1/chat/stream",
        json={"messages": [{"role": "user", "content": message}]},
        stream=True
    )
    for line in response.iter_lines():
        if line:
            print(line.decode('utf-8'), end='')

# 使用示例
models = get_models()
print("可用模型:", models)

switch_model("qwen2.5:7b")
result = chat("你好，请介绍一下你自己")
print(result)
```

### 💻 4. 命令行工具

**使用聊天工具：**
```bash
# 交互模式
python3 chat_cli.py -i

# 单次对话
python3 chat_cli.py "你好，请介绍一下你自己"

# 流式响应
python3 chat_cli.py -s "请写一首诗"

# 流式交互模式
python3 chat_cli.py -i -s

# 模型管理
python3 chat_cli.py --list-models          # 列出可用模型
python3 chat_cli.py --switch-model qwen2.5:7b  # 切换模型
python3 chat_cli.py --current-model        # 查看当前模型
```

### 🎯 优势
- ✅ **快速访问**：无需重新部署
- ✅ **灵活配置**：可自定义调用方式
- ✅ **开发友好**：适合开发和调试
- ✅ **多模型支持**：支持Ollama和Transformers模型
- ✅ **流式响应**：实时流式聊天体验
- ✅ **模型管理**：动态模型切换和管理
- ✅ **多种接口**：Web、API、命令行

---

## 🔧 管理命令

### 服务管理
```bash
# 启动服务
./start_all.sh

# 停止服务
./stop_all.sh

# 重启后端服务
./restart_backend.sh

# 测试后端服务
python3 test_backend.py

# 查看服务状态
ps aux | grep -E "(python3 start.py|npm run dev)"
```

### Docker管理（如果使用Docker）
```bash
# 构建和启动服务
./build_docker.sh

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f

# 停止服务
docker compose down

# 重启服务
docker compose restart
```

### 模型管理
```bash
# 查看Ollama模型
ollama list

# 下载新模型
ollama pull qwen2.5:7b
ollama pull llama2:latest

# 启动Ollama服务
ollama serve

# 通过API管理模型
curl http://localhost:8000/api/v1/models                    # 获取所有可用模型
curl http://localhost:8000/api/v1/models/current            # 获取当前模型
curl -X POST http://localhost:8000/api/v1/models/switch \   # 切换模型
  -H "Content-Type: application/json" \
  -d '{"model_name": "qwen2.5:7b"}'
```

---

## 🎯 使用建议

### 选择方式一（Docker封装包）的场景：
- 🆕 在新机器上部署
- 🏢 生产环境部署
- 👥 团队协作部署
- 🔄 需要完整环境隔离
- 🤖 需要多模型支持
- 📱 需要Web界面

### 选择方式二（直接使用）的场景：
- 🚀 快速测试和开发
- 🔧 需要自定义配置
- 📊 集成到现有系统
- 🎨 开发新功能
- 🔌 需要API集成
- 💻 命令行工具使用

---

## 🆘 常见问题

### Q1: 服务无法访问
```bash
# 检查服务状态
curl http://localhost:8000/api/v1/health

# 检查端口占用
netstat -tlnp | grep :8000
```

### Q2: 模型无响应
```bash
# 检查Ollama服务
curl http://localhost:11434/api/version

# 重启Ollama
pkill ollama && ollama serve &
```

### Q3: 前端页面空白
```bash
# 检查前端服务
curl http://localhost:3001

# 重启前端
cd frontend && npm run dev &
```

### Q4: 模型切换失败
```bash
# 检查模型列表
curl http://localhost:8000/api/v1/models

# 检查当前模型
curl http://localhost:8000/api/v1/models/current

# 重启后端服务
./restart_backend.sh
```

### Q5: 流式聊天无响应
```bash
# 测试流式API
curl -X POST http://localhost:8000/api/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"你好"}]}'

# 检查后端日志
tail -f logs/backend.log
```

### Q6: 混合模型管理器问题
```bash
# 测试后端服务
python3 test_backend.py

# 检查Ollama连接
curl http://localhost:11434/api/version

# 检查Transformers模型
ls -la models/
```

---

## 📞 技术支持

- 📋 查看日志：`logs/backend.log` 和 `logs/frontend.log`
- 🔍 检查服务状态：使用健康检查API
- 🧪 测试服务：运行 `python3 test_backend.py`
- 🔄 重启服务：使用 `./restart_backend.sh`
- 📚 查看文档：`README.md` 和 `DOCKER_DEPLOYMENT.md`
- 🐛 提交问题：项目仓库Issue
- 💡 新功能：混合模型管理器、流式聊天、前端优化

---

**🎉 现在你可以选择最适合的方式使用大模型系统了！**
