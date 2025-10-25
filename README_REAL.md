# 🤖 大模型本地化部署系统

一个完整的本地化大模型部署解决方案，支持GPU加速、多模型管理、资源监控等功能。

## ✨ 特性

- 🚀 **GPU加速**: 基于transformers 的GPU加速推理
- 🎯 **多模型支持**: Qwen、DeepSeek等多种模型
- 📊 **资源监控**: 实时监控GPU、存储、系统资源           ？？？
- 🎨 **现代界面**: React + TypeScript + Ant Design   
- 🐳 **Docker部署**: 一键部署，跨平台运行               ？？？
- 🔧 **完整API**: RESTful API + WebSocket支持

## 🚀 快速开始

windows平台建议在wsl环境下开发
建议使用python3.8

### wsl 或 linux
```bash
# 1. 安装依赖
pip install -r requirements.txt
## 这里通常还需要手动解决依赖，以及部分包可能未添加进requirements 

cd frontend && npm install

# 2. 启动服务
./start_all.sh
bash start_all.sh

# 3. 停止服务
./stop_all.sh

```

### windows

```shell
# 会丢失部分环境
python3 start.py

# 直接手动启动
npm run dev
```


## 后端快速上手：


主要用到fastapi unicorn transformer torch

为了开发模型相关功能，
可以下载1B以下模型进行测试，运行速度较快。
下载建议使用modelscope，不用挂梯子，且速度较快，可以参考download_model.py

### 数据库选择


**sqlite** or **mysql**
后期根据项目规模进行确定，目前使用sqlite即可


### 验证后端fastapi接口

 Swagger UI中可以测试大部分接口
```
http://localhost:8000/docs
```

使用较复杂，但可以手动测试流式接口
```
postman 
```


### 开发任务
* 保证大模型对话的流式传输接口 "/chat/stream" 在使用transformers库时正常工作，需要保证大模型流式产生结果（目前需要等到大模型生成所有结果后才能返回），并通过stream接口流式传输。建议复制
* 基于sqlite数据库开发登陆用api，包括注册和登陆，并在路由中注册
* 学习Agent功能和对话记录功能构建方式，暂时不需要开发
* 暂时不用管ollama相关组件
* 尝试确定聊天过程中后端长时间未响应(60s)导致的聊天接口失效的原因

## 前端快速上手
使用typescript+react。

* 检查前端是否正确调用了流失传输接口，可以使用chat/teststream接口进行测试，
* 修改页面中元素固定方式，（聊天框和右上角四个按钮在不同页面缩放下出现显示错位）
* 开发注册登陆相关功能（现有登陆功能缺少密码校验，加密）
* 尝试确定聊天过程中后端长时间未响应（60s）导致的聊天接口失效的原因
* 修复切换模型过程中错误显示 “正在思考” 的bug
* 修改上传文件功能（可以先不改，根据后续agent开发需求再进行修改）