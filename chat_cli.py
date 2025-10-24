#!/usr/bin/env python3
"""
大模型命令行聊天工具
直接使用已部署的API服务
"""

import requests
import json
import sys
import argparse

BASE_URL = "http://localhost:8000/api/v1"

def send_message(message, stream=False):
    """发送消息到模型"""
    try:
        data = {
            "messages": [{"role": "user", "content": message}],
            "stream": stream
        }
        
        if stream:
            response = requests.post(f"{BASE_URL}/chat/stream", json=data, stream=True)
            for line in response.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line.decode('utf-8'))
                        if chunk.get('content'):
                            print(chunk['content'], end='', flush=True)
                    except:
                        continue
            print()
        else:
            response = requests.post(f"{BASE_URL}/chat", json=data)
            result = response.json()
            print(result['message'])
            
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='大模型命令行聊天工具')
    parser.add_argument('message', nargs='?', help='要发送的消息')
    parser.add_argument('-s', '--stream', action='store_true', help='使用流式响应')
    parser.add_argument('-i', '--interactive', action='store_true', help='交互模式')
    
    args = parser.parse_args()
    
    # 检查服务状态
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ 服务未运行，请先启动服务", file=sys.stderr)
            sys.exit(1)
    except:
        print("❌ 无法连接到服务，请检查服务是否运行", file=sys.stderr)
        sys.exit(1)
    
    if args.interactive:
        # 交互模式
        print("🤖 大模型聊天工具 (输入 'quit' 退出)")
        while True:
            try:
                message = input("\n👤 你: ")
                if message.lower() in ['quit', 'exit', '退出']:
                    break
                if message.strip():
                    print("🤖 模型: ", end='')
                    send_message(message, args.stream)
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
    elif args.message:
        # 单次对话
        send_message(args.message, args.stream)
    else:
        # 默认交互模式
        print("🤖 大模型聊天工具 (输入 'quit' 退出)")
        while True:
            try:
                message = input("\n👤 你: ")
                if message.lower() in ['quit', 'exit', '退出']:
                    break
                if message.strip():
                    print("🤖 模型: ", end='')
                    send_message(message, args.stream)
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break

if __name__ == "__main__":
    main()
