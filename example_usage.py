#!/usr/bin/env python3
"""
大模型本地化系统使用示例
直接调用已部署的API服务
"""

import requests
import json
import time

# API基础URL
BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """测试服务健康状态"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ 服务状态: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        return False

def get_available_models():
    """获取可用模型列表"""
    try:
        response = requests.get(f"{BASE_URL}/models")
        models = response.json()
        print(f"📋 可用模型: {models}")
        return models
    except Exception as e:
        print(f"❌ 获取模型失败: {e}")
        return []

def chat_with_model(message, stream=False):
    """与模型对话"""
    try:
        data = {
            "messages": [{"role": "user", "content": message}],
            "stream": stream
        }
        
        if stream:
            # 流式响应
            response = requests.post(f"{BASE_URL}/chat/stream", 
                                   json=data, stream=True)
            print("🤖 模型回复（流式）:")
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if chunk.get('content'):
                            print(chunk['content'], end='', flush=True)
                    except:
                        continue
            print("\n")
        else:
            # 普通响应
            response = requests.post(f"{BASE_URL}/chat", json=data)
            result = response.json()
            print(f"🤖 模型回复: {result['message']}")
            return result['message']
            
    except Exception as e:
        print(f"❌ 对话失败: {e}")
        return None

def get_system_info():
    """获取系统信息"""
    try:
        response = requests.get(f"{BASE_URL}/system/info")
        info = response.json()
        print(f"💻 系统信息: {json.dumps(info, indent=2, ensure_ascii=False)}")
        return info
    except Exception as e:
        print(f"❌ 获取系统信息失败: {e}")
        return None

def get_gpu_info():
    """获取GPU信息"""
    try:
        response = requests.get(f"{BASE_URL}/computing/gpus")
        gpus = response.json()
        print(f"🎮 GPU信息: {json.dumps(gpus, indent=2, ensure_ascii=False)}")
        return gpus
    except Exception as e:
        print(f"❌ 获取GPU信息失败: {e}")
        return None

def main():
    """主函数"""
    print("🚀 大模型本地化系统使用示例")
    print("=" * 50)
    
    # 1. 检查服务状态
    print("\n1. 检查服务状态...")
    if not test_health():
        print("❌ 服务未运行，请先启动服务")
        return
    
    # 2. 获取可用模型
    print("\n2. 获取可用模型...")
    models = get_available_models()
    
    # 3. 获取系统信息
    print("\n3. 获取系统信息...")
    get_system_info()
    
    # 4. 获取GPU信息
    print("\n4. 获取GPU信息...")
    get_gpu_info()
    
    # 5. 与模型对话
    print("\n5. 与模型对话...")
    
    # 普通对话
    print("\n📝 普通对话:")
    chat_with_model("你好，请简单介绍一下你自己")
    
    # 流式对话
    print("\n📝 流式对话:")
    chat_with_model("请写一首关于AI的诗", stream=True)
    
    # 6. 交互式对话
    print("\n6. 交互式对话模式")
    print("输入 'quit' 退出")
    
    while True:
        try:
            user_input = input("\n👤 你: ")
            if user_input.lower() in ['quit', 'exit', '退出']:
                break
            
            if user_input.strip():
                chat_with_model(user_input)
                
        except KeyboardInterrupt:
            print("\n👋 再见！")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")

if __name__ == "__main__":
    main()
