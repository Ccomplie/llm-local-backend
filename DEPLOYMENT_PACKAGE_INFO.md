# 📦 部署包信息

## 📍 当前部署包位置

**部署包文件：**
- **路径**: `/media/cring/mydrive/llm-local-backend-20251017-211642.tar.gz`
- **大小**: 3.5M
- **创建时间**: 2025年10月17日 21:16

## 🚀 使用方法

### 方法1：复制到其他机器
```bash
# 复制到目标机器
scp /media/cring/mydrive/llm-local-backend-20251017-211642.tar.gz user@target-machine:/home/user/

# 在目标机器上部署
tar -xzf llm-local-backend-20251017-211642.tar.gz
cd llm-local-backend-20251017-211642
./install.sh
```

### 方法2：本地测试
```bash
# 在当前位置测试
cd /media/cring/mydrive
tar -xzf llm-local-backend-20251017-211642.tar.gz
cd llm-local-backend-20251017-211642
./install.sh
```

### 方法3：重新创建部署包
```bash
# 如果需要重新创建
cd /media/cring/mydrive/llm-local-backend
./create_deployment_package.sh
```

## 📋 部署包内容

- ✅ 完整的源代码
- ✅ Docker配置文件
- ✅ 启动脚本
- ✅ 部署文档
- ✅ 自动安装脚本

## 🎯 访问地址

部署完成后访问：
- **主页面**: http://localhost:8080
- **API文档**: http://localhost:8000/docs

## 🔧 管理命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

**注意**: 部署包已移动到 `/media/cring/mydrive/` 目录，所有相关文档已更新路径信息。
