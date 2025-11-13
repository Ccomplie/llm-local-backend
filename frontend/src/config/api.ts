// frontend/src/config/api.ts
export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000/api/v1',
  ENDPOINTS: {
    // 模型管理
    MODELS: '/models',
    MODEL_SWITCH: '/models/switch',
    MODEL_CURRENT: '/models/current',
    
    // 聊天对话
    CHAT: '/chat',
    CHAT_STREAM: '/chat/stream',
    CHAT_WS: '/chat/ws',
    CHAT_FUNC: '/chat/chat_func',
    // 健康检查
    HEALTH: '/health',
    HEALTH_DETAILED: '/health/detailed',
    
    // 训练功能
    TRAINING_START: '/training/start',
    TRAINING_STATUS: '/training/status',
  }
};

export const WS_CONFIG = {
  CHAT_URL: 'ws://localhost:8000/api/v1/chat/ws'
};