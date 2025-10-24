# 🐳 大模型本地化Docker部署指南

## 📋 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 至少 8GB 可用内存
- 至少 20GB 可用磁盘空间
- NVIDIA GPU（可选，用于GPU加速）

## 🚀 快速部署

### 1. 克隆项目
```bash
git clone <your-repo-url>
cd llm-local-backend
```

### 2. 一键部署
```bash
chmod +x build_docker.sh
./build_docker.sh
```

### 3. 访问服务
- **主页面**: http://localhost:8080
- **前端页面**: http://localhost:80
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 🔧 手动部署

### 1. 构建镜像
```bash
docker compose build
```

### 2. 启动服务
```bash
docker compose up -d
```

### 3. 查看状态
```bash
docker compose ps
```

## 📊 服务架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│   Frontend      │    │   Backend       │
│   Port: 8080    │    │   Port: 80      │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │     Redis       │
                    │   Port: 6379    │
                    └─────────────────┘
```

## 🗂️ 数据持久化

### 目录映射
- `./models` → `/app/models` - 模型文件
- `./uploads` → `/app/uploads` - 上传文件
- `./logs` → `/app/logs` - 日志文件
- `./llm_backend.db` → `/app/llm_backend.db` - 数据库

### 创建必要目录
```bash
mkdir -p models uploads logs
```

## 🔧 配置说明

### 环境变量
编辑 `docker.env` 文件：
```bash
# Ollama配置
OLLAMA_HOST=host.docker.internal:11434

# 模型配置
DEFAULT_MODEL=qwen2.5:7b

# 安全配置
SECRET_KEY=your-secret-key-here
```

### Ollama集成
1. 在宿主机安装Ollama
2. 下载模型：
   ```bash
   ollama pull qwen2.5:7b
   ```
3. 启动Ollama服务：
   ```bash
   ollama serve
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

## 🛠️ 管理命令

### 查看服务状态
```bash
docker compose ps
```

### 查看服务日志
```bash
# 查看所有服务日志
docker compose logs -f

# 查看特定服务日志
docker compose logs -f backend
docker compose logs -f frontend
```

### 重启服务
```bash
# 重启所有服务
docker compose restart

# 重启特定服务
docker compose restart backend
```

### 停止服务
```bash
docker compose down
```

### 更新服务
```bash
# 重新构建并启动
docker compose up -d --build
```

## 🔍 故障排除

### 1. 服务无法启动
```bash
# 检查Docker状态
docker info

# 检查端口占用
netstat -tlnp | grep :8080
```

### 2. 前端无法访问
```bash
# 检查前端容器状态
docker compose ps frontend

# 查看前端日志
docker compose logs frontend
```

### 3. 后端API无响应
```bash
# 检查后端容器状态
docker compose ps backend

# 查看后端日志
docker compose logs backend

# 测试API
curl http://localhost:8000/api/v1/health
```

### 4. Ollama连接问题
```bash
# 检查Ollama服务
curl http://localhost:11434/api/version

# 检查模型列表
curl http://localhost:11434/api/tags
```

## 📈 性能优化

### 1. 资源限制
在 `docker-compose.yml` 中添加资源限制：
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### 2. GPU支持
```yaml
services:
  backend:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### 3. 缓存优化
```yaml
services:
  redis:
    command: redis-server --maxmemory 1gb --maxmemory-policy allkeys-lru
```

## 🔒 安全配置

### 1. 修改默认密码
```bash
# 编辑 docker.env
SECRET_KEY=your-very-secure-secret-key
```

### 2. 限制访问
```yaml
services:
  nginx:
    ports:
      - "127.0.0.1:8080:80"  # 只允许本地访问
```

### 3. 启用HTTPS
```yaml
services:
  nginx:
    volumes:
      - ./ssl:/etc/nginx/ssl:ro
    ports:
      - "443:443"
```

## 📦 生产部署

### 1. 使用生产配置
```bash
docker compose -f docker-compose.prod.yml up -d
```

### 2. 配置反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 3. 监控和日志
```bash
# 使用ELK栈收集日志
docker compose -f docker-compose.monitoring.yml up -d
```

## 🆘 支持

如果遇到问题，请：
1. 查看日志文件
2. 检查系统资源
3. 验证网络连接
4. 提交Issue到项目仓库

---

**注意**: 确保在生产环境中修改默认配置，包括密码、密钥等敏感信息。
