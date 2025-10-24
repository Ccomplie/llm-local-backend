#!/usr/bin/env python3
"""
简单的后端服务测试脚本
"""

import requests
import json
import time

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🔍 测试后端服务...")
    
    # 1. 测试健康检查
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False
    
    # 2. 测试模型列表
    try:
        response = requests.get(f"{base_url}/api/v1/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ 模型列表获取成功，共{len(models)}个模型")
            for model in models:
                print(f"   - {model['name']} ({model.get('type', 'unknown')})")
        else:
            print(f"❌ 模型列表获取失败: {response.status_code}")
    except Exception as e:
        print(f"❌ 模型列表获取异常: {e}")
    
    # 3. 测试普通聊天API
    try:
        response = requests.post(f"{base_url}/api/v1/chat", 
                               json={
                                   "messages": [{"role": "user", "content": "你好"}],
                                   "max_tokens": 50
                               }, 
                               timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("✅ 普通聊天API测试成功")
            print(f"   回复: {result.get('message', '')[:100]}...")
        else:
            print(f"❌ 普通聊天API失败: {response.status_code}")
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 普通聊天API异常: {e}")
    
    # 4. 测试流式聊天API
    try:
        response = requests.post(f"{base_url}/api/v1/chat/stream", 
                               json={
                                   "messages": [{"role": "user", "content": "你好"}],
                                   "max_tokens": 50
                               }, 
                               stream=True,
                               timeout=30)
        if response.status_code == 200:
            print("✅ 流式聊天API测试成功")
            print("   流式响应:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'token' in data:
                                print(f"   {data['token']}", end='', flush=True)
                        except:
                            pass
            print("\n   流式响应结束")
        else:
            print(f"❌ 流式聊天API失败: {response.status_code}")
            print(f"   错误: {response.text}")
    except Exception as e:
        print(f"❌ 流式聊天API异常: {e}")
    
    print("\n🎉 后端服务测试完成！")
    return True

if __name__ == "__main__":
    test_backend()
