// frontend/src/services/api.ts
import { API_CONFIG, WS_CONFIG } from '../config/api';

export class ModelAPI {
  private baseUrl = API_CONFIG.BASE_URL;

  // 获取模型列表
  async getModels() {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.MODELS}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  // 切换模型
  async switchModel(modelName: string) {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.MODEL_SWITCH}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model_name: modelName
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  // 获取当前模型
  async getCurrentModel() {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.MODEL_CURRENT}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  // 健康检查
  async getHealth() {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.HEALTH}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }
}

export class ChatAPI {
  private baseUrl = API_CONFIG.BASE_URL;

  // 发送聊天消息
  async sendMessage(messages: Array<{role: string, content: string}>, options: any = {}) {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.CHAT}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages,
        max_tokens: options.maxTokens || 1000,
        temperature: options.temperature || 0.7,
        top_p: options.topP || 0.9,
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  }

  // 流式聊天
  async *sendMessageStream(messages: Array<{role: string, content: string}>, options: any = {}) {
    const response = await fetch(`${this.baseUrl}${API_CONFIG.ENDPOINTS.CHAT_STREAM}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        messages: messages,
        max_tokens: options.maxTokens || 1000,
        temperature: options.temperature || 0.7,
        top_p: options.topP || 0.9,
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) return;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          if (data === '[DONE]') {
            return;
          }
          try {
            const parsed = JSON.parse(data);
            yield parsed;
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    }
  }

  // WebSocket聊天
  createWebSocketChat(onMessage: (token: string) => void, onComplete: () => void, onError: (error: string) => void) {
    const ws = new WebSocket(WS_CONFIG.CHAT_URL);
    
    ws.onopen = () => {
      console.log('WebSocket连接已建立');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'token') {
          onMessage(data.token);
        } else if (data.type === 'complete') {
          onComplete();
        } else if (data.type === 'error') {
          onError(data.error);
        }
      } catch (e) {
        console.error('WebSocket消息解析失败:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket错误:', error);
      onError('WebSocket连接错误');
    };

    ws.onclose = () => {
      console.log('WebSocket连接已关闭');
    };

    return ws;
  }

  // 发送WebSocket消息
  sendWebSocketMessage(ws: WebSocket, messages: Array<{role: string, content: string}>) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        type: "chat",
        messages: messages
      }));
    } else {
      throw new Error('WebSocket连接未建立');
    }
  }
}

// 导出API实例
// 算力资源管理API
export class ComputingAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async getGPUs() {
    const response = await fetch(`${this.baseURL}/api/v1/computing/gpus`);
    return response.json();
  }

  async getTasks() {
    const response = await fetch(`${this.baseURL}/api/v1/computing/tasks`);
    return response.json();
  }

  async createTask(taskData: any) {
    const response = await fetch(`${this.baseURL}/api/v1/computing/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(taskData)
    });
    return response.json();
  }

  async getPerformanceData() {
    const response = await fetch(`${this.baseURL}/api/v1/computing/performance`);
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.baseURL}/api/v1/computing/stats`);
    return response.json();
  }
}

// 存储资源管理API
export class StorageAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async getStorageDevices() {
    const response = await fetch(`${this.baseURL}/api/v1/storage/devices`);
    return response.json();
  }

  async getFiles(path: string = '/', fileType?: string, search?: string) {
    const params = new URLSearchParams({ path });
    if (fileType) params.append('file_type', fileType);
    if (search) params.append('search', search);
    
    const response = await fetch(`${this.baseURL}/api/v1/storage/files?${params}`);
    return response.json();
  }

  async uploadFile(file: File, targetPath: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('target_path', targetPath);
    
    const response = await fetch(`${this.baseURL}/api/v1/storage/upload`, {
      method: 'POST',
      body: formData
    });
    return response.json();
  }

  async downloadFile(filePath: string) {
    const response = await fetch(`${this.baseURL}/api/v1/storage/download?file_path=${encodeURIComponent(filePath)}`);
    return response.blob();
  }

  async deleteFile(filePath: string) {
    const response = await fetch(`${this.baseURL}/api/v1/storage/files?file_path=${encodeURIComponent(filePath)}`, {
      method: 'DELETE'
    });
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.baseURL}/api/v1/storage/stats`);
    return response.json();
  }
}

// 系统资源管理API
export class SystemAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async getSystemInfo() {
    const response = await fetch(`${this.baseURL}/api/v1/system/info`);
    return response.json();
  }

  async getProcesses() {
    const response = await fetch(`${this.baseURL}/api/v1/system/processes`);
    return response.json();
  }

  async getNetworkInfo() {
    const response = await fetch(`${this.baseURL}/api/v1/system/network`);
    return response.json();
  }

  async getSystemLogs(level?: string, limit: number = 100) {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (level) params.append('level', level);
    
    const response = await fetch(`${this.baseURL}/api/v1/system/logs?${params}`);
    return response.json();
  }

  async getPerformanceTrend() {
    const response = await fetch(`${this.baseURL}/api/v1/system/performance-trend`);
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.baseURL}/api/v1/system/stats`);
    return response.json();
  }
}

// 模型服务管理API
export class ModelServiceAPI {
  private baseURL: string;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async getTemplates() {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/templates`);
    return response.json();
  }

  async getServices() {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/services`);
    return response.json();
  }

  async createService(serviceData: any) {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/services`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(serviceData)
    });
    return response.json();
  }

  async startService(serviceId: string) {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/services/${serviceId}/start`, {
      method: 'POST'
    });
    return response.json();
  }

  async stopService(serviceId: string) {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/services/${serviceId}/stop`, {
      method: 'POST'
    });
    return response.json();
  }

  async getServiceMetrics(serviceId: string, limit: number = 100) {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/services/${serviceId}/metrics?limit=${limit}`);
    return response.json();
  }

  async getServiceLogs(serviceId: string, limit: number = 100) {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/services/${serviceId}/logs?limit=${limit}`);
    return response.json();
  }

  async getStats() {
    const response = await fetch(`${this.baseURL}/api/v1/model-service/stats`);
    return response.json();
  }
}

export const modelAPI = new ModelAPI();
export const chatAPI = new ChatAPI();
export const computingAPI = new ComputingAPI();
export const storageAPI = new StorageAPI();
export const systemAPI = new SystemAPI();
export const modelServiceAPI = new ModelServiceAPI();