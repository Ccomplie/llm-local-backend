import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Tag,
  Button,
  Modal,
  Form,
  Select,
  Input,
  Space,
  Tabs,
  Drawer,
  Timeline,
  Badge,
  Descriptions,
  Radio,
  message,
  
} from 'antd';
import {
  ApiOutlined,
  PlayCircleOutlined,
  StopOutlined,
  ReloadOutlined,
  SettingOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { Line } from '@ant-design/charts';

const { Option } = Select;
const { TabPane } = Tabs;

interface ModelService {
  key: string;
  id: string;
  name: string;
  type: 'llm' | 'vision' | 'health' | 'trajectory';
  model: string;
  version: string;
  status: 'running' | 'stopped' | 'error' | 'starting';
  port: number;
  gpu: string;
  memory: number;
  startTime: string;
  requests: number;
  avgResponseTime: number;
  health: 'healthy' | 'warning' | 'error';
}

interface ModelTemplate {
  name: string;
  type: 'llm' | 'vision' | 'health' | 'trajectory';
  description: string;
  requirements: string;
  defaultPort: number;
  defaultMemory: number;
}

interface ServiceMetrics {
  timestamp: string;
  requestCount: number;
  responseTime: number;
  memoryUsage: number;
  cpuUsage: number;
}

const ModelServicePage: React.FC = () => {
  const [isStartModalVisible, setIsStartModalVisible] = useState(false);
  const [isConfigModalVisible, setIsConfigModalVisible] = useState(false);
  const [selectedService, setSelectedService] = useState<ModelService | null>(null);
  const [showServiceDetail, setShowServiceDetail] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<string[]>([]);
  const [metricsData, setMetricsData] = useState<ServiceMetrics[]>([]);
  const [serviceLog, setServiceLog] = useState<string[]>([]);
  const [apiTestVisible, setApiTestVisible] = useState(false);

  const [startForm] = Form.useForm();
  const [configForm] = Form.useForm();

  // 模型模板数据
  const modelTemplates: ModelTemplate[] = [
    {
      name: 'Qwen-7B',
      type: 'llm',
      description: '阿里云开源大语言模型，支持中英文对话和代码生成',
      requirements: 'GPU: 16GB+, Memory: 8GB+',
      defaultPort: 8001,
      defaultMemory: 8,
    },
    {
      name: 'DeepSeek-7B',
      type: 'llm',
      description: '深度求索开源大语言模型，擅长数学推理和代码生成',
      requirements: 'GPU: 16GB+, Memory: 8GB+',
      defaultPort: 8002,
      defaultMemory: 8,
    },
    {
      name: 'ResNet-50',
      type: 'vision',
      description: '图像分类模型，支持1000类物体识别',
      requirements: 'GPU: 4GB+, Memory: 2GB+',
      defaultPort: 8003,
      defaultMemory: 2,
    },
    {
      name: 'YOLO-v8',
      type: 'vision',
      description: '目标检测模型，实时检测图像中的物体',
      requirements: 'GPU: 6GB+, Memory: 3GB+',
      defaultPort: 8004,
      defaultMemory: 3,
    },
    {
      name: 'Health-Predictor',
      type: 'health',
      description: '健康状态预测模型，基于生理指标预测健康风险',
      requirements: 'GPU: 2GB+, Memory: 1GB+',
      defaultPort: 8005,
      defaultMemory: 1,
    },
    {
      name: 'Trajectory-Recognition',
      type: 'trajectory',
      description: '轨迹识别模型，分析移动物体的运动轨迹',
      requirements: 'GPU: 4GB+, Memory: 2GB+',
      defaultPort: 8006,
      defaultMemory: 2,
    },
  ];

  // 运行中的服务数据
  const runningServices: ModelService[] = [
    {
      key: '1',
      id: 'SERVICE-001',
      name: 'Qwen-7B服务',
      type: 'llm',
      model: 'Qwen-7B',
      version: 'v1.0.0',
      status: 'running',
      port: 8001,
      gpu: 'GPU-001',
      memory: 8,
      startTime: '2024-01-15 09:00:00',
      requests: 1250,
      avgResponseTime: 2.3,
      health: 'healthy',
    },
    {
      key: '2',
      id: 'SERVICE-002',
      name: 'ResNet-50服务',
      type: 'vision',
      model: 'ResNet-50',
      version: 'v1.0.0',
      status: 'running',
      port: 8003,
      gpu: 'GPU-003',
      memory: 2,
      startTime: '2024-01-15 10:30:00',
      requests: 890,
      avgResponseTime: 0.8,
      health: 'healthy',
    },
    {
      key: '3',
      id: 'SERVICE-003',
      name: 'Health-Predictor服务',
      type: 'health',
      model: 'Health-Predictor',
      version: 'v1.0.0',
      status: 'running',
      port: 8005,
      gpu: 'GPU-002',
      memory: 1,
      startTime: '2024-01-15 11:15:00',
      requests: 456,
      avgResponseTime: 1.2,
      health: 'warning',
    },
  ];

  const serviceColumns = [
    {
      title: '服务ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '服务名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '模型类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap = {
          llm: { color: 'blue', text: '大语言模型' },
          vision: { color: 'green', text: '图像识别' },
          health: { color: 'purple', text: '健康预测' },
          trajectory: { color: 'orange', text: '轨迹识别' },
        };
        return <Tag color={typeMap[type as keyof typeof typeMap].color}>{typeMap[type as keyof typeof typeMap].text}</Tag>;
      },
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          running: { color: 'success', text: '运行中' },
          stopped: { color: 'default', text: '已停止' },
          error: { color: 'error', text: '错误' },
          starting: { color: 'processing', text: '启动中' },
        };
        return <Tag color={statusMap[status as keyof typeof statusMap].color}>{statusMap[status as keyof typeof statusMap].text}</Tag>;
      },
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
    },
    {
      title: '分配GPU',
      dataIndex: 'gpu',
      key: 'gpu',
    },
    {
      title: '内存使用',
      dataIndex: 'memory',
      key: 'memory',
      render: (value: number) => `${value}GB`,
    },
    {
      title: '健康状态',
      dataIndex: 'health',
      key: 'health',
      render: (health: string) => {
        const healthMap = {
          healthy: { color: 'success', text: '健康' },
          warning: { color: 'warning', text: '警告' },
          error: { color: 'error', text: '错误' },
        };
        return <Tag color={healthMap[health as keyof typeof healthMap].color}>{healthMap[health as keyof typeof healthMap].text}</Tag>;
      },
    },
    {
      title: '请求数',
      dataIndex: 'requests',
      key: 'requests',
    },
    {
      title: '平均响应时间',
      dataIndex: 'avgResponseTime',
      key: 'avgResponseTime',
      render: (value: number) => `${value}s`,
    },
    {
      title: '操作',
      key: 'action',
      render: (record: ModelService) => (
        <Space>
          <Button 
            size="small" 
            icon={<EyeOutlined />}
            onClick={() => handleViewService(record)}
          >
            查看
          </Button>
          {record.status === 'running' ? (
            <Button 
              size="small" 
              icon={<StopOutlined />}
              danger
              onClick={() => handleStopService(record.id)}
            >
              停止
            </Button>
          ) : (
            <Button 
              size="small" 
              icon={<PlayCircleOutlined />}
              type="primary"
              onClick={() => handleStartService(record.id)}
            >
              启动
            </Button>
          )}
          <Button 
            size="small" 
            icon={<SettingOutlined />}
            onClick={() => handleConfigService(record)}
          >
            配置
          </Button>
        </Space>
      ),
    },
  ];

  const templateColumns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap = {
          llm: { color: 'blue', text: '大语言模型' },
          vision: { color: 'green', text: '图像识别' },
          health: { color: 'purple', text: '健康预测' },
          trajectory: { color: 'orange', text: '轨迹识别' },
        };
        return <Tag color={typeMap[type as keyof typeof typeMap].color}>{typeMap[type as keyof typeof typeMap].text}</Tag>;
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '系统要求',
      dataIndex: 'requirements',
      key: 'requirements',
    },
    {
      title: '默认端口',
      dataIndex: 'defaultPort',
      key: 'defaultPort',
    },
    {
      title: '默认内存',
      dataIndex: 'defaultMemory',
      key: 'defaultMemory',
      render: (value: number) => `${value}GB`,
    },
    {
      title: '操作',
      key: 'action',
      render: (record: ModelTemplate) => (
        <Button 
          type="primary" 
          size="small" 
          icon={<PlayCircleOutlined />}
          onClick={() => handleStartFromTemplate(record)}
        >
          启动服务
        </Button>
      ),
    },
  ];

  const handleStartFromTemplate = (template: ModelTemplate) => {
    startForm.setFieldsValue({
      modelName: template.name,
      modelType: template.type,
      port: template.defaultPort,
      memory: template.defaultMemory,
    });
    setIsStartModalVisible(true);
  };

  const handleViewService = (service: ModelService) => {
    setSelectedService(service);
    setShowServiceDetail(true);
    
    // 模拟加载性能数据
    const mockMetrics: ServiceMetrics[] = Array(24).fill(0).map((_, i) => ({
      timestamp: `2024-01-15 ${String(i).padStart(2, '0')}:00`,
      requestCount: Math.floor(Math.random() * 100),
      responseTime: Math.random() * 3,
      memoryUsage: Math.random() * 100,
      cpuUsage: Math.random() * 100,
    }));
    setMetricsData(mockMetrics);

    // 模拟加载日志数据
    setServiceLog([
      '2024-01-15 09:00:00 [INFO] 服务启动成功',
      '2024-01-15 09:01:00 [INFO] 模型加载完成',
      '2024-01-15 09:02:00 [INFO] 开始接收请求',
      // ... 更多日志
    ]);
  };

  const handleStartService = (serviceId: string) => {
    console.log('启动服务:', serviceId);
  };

  const handleStopService = (serviceId: string) => {
    console.log('停止服务:', serviceId);
  };

  const handleConfigService = (service: ModelService) => {
    configForm.setFieldsValue({
      serviceId: service.id,
      port: service.port,
      memory: service.memory,
    });
    setIsConfigModalVisible(true);
  };

  const handleStartModalOk = () => {
    startForm.validateFields().then((values) => {
      console.log('启动服务:', values);
      setIsStartModalVisible(false);
      startForm.resetFields();
    });
  };

  const handleConfigModalOk = () => {
    configForm.validateFields().then((values) => {
      console.log('配置服务:', values);
      setIsConfigModalVisible(false);
      configForm.resetFields();
    });
  };

  const handleBatchOperation = (operation: 'start' | 'stop') => {
    const actionText = operation === 'start' ? '启动' : '停止';
    message.success(`已${actionText}选中的 ${selectedRowKeys.length} 个服务`);
    setSelectedRowKeys([]);
  };

  const handleTestApi = async (service: ModelService) => {
    try {
      // 这里实现实际的API测试逻辑
      // 使用 service 参数，例如打印请求地址
      console.log(`API测试请求已发送到: http://localhost:${service.port}/api/predict`);
      message.success('API测试请求已发送');
    } catch (error) {
      message.error('API测试失败');
    }
  };

  const runningCount = runningServices.filter(service => service.status === 'running').length;
  const totalCount = runningServices.length;
  const healthyCount = runningServices.filter(service => service.health === 'healthy').length;

  // 服务详情抽屉组件
  const ServiceDetailDrawer = () => (
    <Drawer
      title="服务详情"
      width={800}
      placement="right"
      onClose={() => setShowServiceDetail(false)}
      open={showServiceDetail && selectedService !== null}
    >
      {selectedService && (
        <>
          <Descriptions title="基本信息" bordered column={2}>
            <Descriptions.Item label="服务ID">{selectedService.id}</Descriptions.Item>
            <Descriptions.Item label="服务名称">{selectedService.name}</Descriptions.Item>
            <Descriptions.Item label="模型类型">{selectedService.type}</Descriptions.Item>
            <Descriptions.Item label="模型版本">{selectedService.version}</Descriptions.Item>
            <Descriptions.Item label="运行状态">
              <Badge status={selectedService.status === 'running' ? 'success' : 'error'} 
                     text={selectedService.status === 'running' ? '运行中' : '已停止'} />
            </Descriptions.Item>
            <Descriptions.Item label="健康状态">
              <Badge status={
                selectedService.health === 'healthy' ? 'success' : 
                selectedService.health === 'warning' ? 'warning' : 'error'
              } text={selectedService.health} />
            </Descriptions.Item>
          </Descriptions>

          <div style={{ marginTop: 24 }}>
            <h4>性能监控</h4>
            <Line
              data={metricsData}
              height={300}
              xField="timestamp"
              yField="value"
              seriesField="metric"
              point={{
                size: 5,
                shape: 'diamond',
              }}
              label={{
                style: {
                  fill: '#aaa',
                },
              }}
            />
          </div>

          <div style={{ marginTop: 24 }}>
            <h4>服务日志</h4>
            <Timeline style={{ maxHeight: 300, overflowY: 'auto' }}>
              {serviceLog.map((log, index) => (
                <Timeline.Item key={index}>{log}</Timeline.Item>
              ))}
            </Timeline>
          </div>
        </>
      )}
    </Drawer>
  );

  // API测试对话框组件
  interface ApiTestModalProps {
    visible: boolean;
    service: ModelService | null;
    onClose: () => void;
  }

  const ApiTestModal: React.FC<ApiTestModalProps> = ({ visible, onClose, service }) => (
    <Modal
      title="API测试"
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
    >
      <Form layout="vertical">
        <Form.Item label="请求地址">
          <Input 
            readOnly 
            value={service ? `http://localhost:${service.port}/api/predict` : ''} 
          />
        </Form.Item>
        <Form.Item label="请求方法">
          <Radio.Group defaultValue="POST">
            <Radio.Button value="GET">GET</Radio.Button>
            <Radio.Button value="POST">POST</Radio.Button>
          </Radio.Group>
        </Form.Item>
        <Form.Item label="请求参数">
          <Input.TextArea rows={4} placeholder="请输入JSON格式的请求参数" />
        </Form.Item>
        <Form.Item>
          <Button 
            type="primary" 
            onClick={() => service && handleTestApi(service)}
            disabled={!service}
          >
            发送请求
          </Button>
        </Form.Item>
        <Form.Item label="响应结果">
          <Input.TextArea rows={4} readOnly />
        </Form.Item>
      </Form>
    </Modal>
  );

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>模型服务管理</h2>
      
      {/* 统计概览 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总服务数"
              value={totalCount}
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="运行中服务"
              value={runningCount}
              prefix={<PlayCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="健康服务"
              value={healthyCount}
              prefix={<SettingOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="服务健康率"
              value={totalCount > 0 ? Math.round((healthyCount / totalCount) * 100) : 0}
              suffix="%"
              valueStyle={{ color: healthyCount / totalCount > 0.8 ? '#3f8600' : '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要功能标签页 */}
      <Tabs defaultActiveKey="running" size="large">
        <TabPane tab="运行中服务" key="running">
          <Card 
            title="服务状态监控" 
            extra={
              <Space>
                <Button icon={<ReloadOutlined />}>刷新</Button>
                <Button 
                  type="primary" 
                  icon={<PlayCircleOutlined />}
                  onClick={() => setIsStartModalVisible(true)}
                >
                  启动新服务
                </Button>
              </Space>
            }
          >
            <Table 
              columns={serviceColumns} 
              dataSource={runningServices} 
              pagination={false}
              size="middle"
              rowSelection={{
                selectedRowKeys,
                onChange: (keys) => setSelectedRowKeys(keys as string[]),
              }}
              footer={() => (
                <Space>
                  <span>已选择 {selectedRowKeys.length} 项</span>
                  <Button 
                    disabled={selectedRowKeys.length === 0}
                    onClick={() => handleBatchOperation('start')}
                  >
                    批量启动
                  </Button>
                  <Button 
                    disabled={selectedRowKeys.length === 0}
                    onClick={() => handleBatchOperation('stop')}
                  >
                    批量停止
                  </Button>
                </Space>
              )}
            />
          </Card>
        </TabPane>

        <TabPane tab="模型模板" key="templates">
          <Card title="可用模型模板">
            <Table 
              columns={templateColumns} 
              dataSource={modelTemplates} 
              pagination={false}
              size="middle"
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* 启动服务模态框 */}
      <Modal
        title="启动模型服务"
        open={isStartModalVisible}
        onOk={handleStartModalOk}
        onCancel={() => setIsStartModalVisible(false)}
        okText="启动"
        cancelText="取消"
        width={600}
      >
        <Form form={startForm} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="modelName"
                label="模型名称"
                rules={[{ required: true, message: '请选择模型名称' }]}
              >
                <Select placeholder="请选择模型">
                  {modelTemplates.map(template => (
                    <Option key={template.name} value={template.name}>
                      {template.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="modelType"
                label="模型类型"
                rules={[{ required: true, message: '请选择模型类型' }]}
              >
                <Select placeholder="请选择类型">
                  <Option value="llm">大语言模型</Option>
                  <Option value="vision">图像识别</Option>
                  <Option value="health">健康预测</Option>
                  <Option value="trajectory">轨迹识别</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="port"
                label="服务端口"
                rules={[{ required: true, message: '请输入服务端口' }]}
              >
                <Input placeholder="请输入端口号" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="memory"
                label="内存分配(GB)"
                rules={[{ required: true, message: '请输入内存分配' }]}
              >
                <Input placeholder="请输入内存大小" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item
            name="gpu"
            label="GPU选择"
            rules={[{ required: true, message: '请选择GPU' }]}
          >
            <Select placeholder="请选择GPU">
              <Option value="GPU-001">GPU-001 (RTX 4090)</Option>
              <Option value="GPU-002">GPU-002 (RTX 4080)</Option>
              <Option value="GPU-003">GPU-003 (RTX 4070)</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="description"
            label="服务描述"
          >
            <Input.TextArea placeholder="请输入服务描述" rows={3} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 配置服务模态框 */}
      <Modal
        title="配置模型服务"
        open={isConfigModalVisible}
        onOk={handleConfigModalOk}
        onCancel={() => setIsConfigModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={configForm} layout="vertical">
          <Form.Item
            name="serviceId"
            label="服务ID"
          >
            <Input disabled />
          </Form.Item>
          <Form.Item
            name="port"
            label="服务端口"
            rules={[{ required: true, message: '请输入服务端口' }]}
          >
            <Input placeholder="请输入端口号" />
          </Form.Item>
          <Form.Item
            name="memory"
            label="内存分配(GB)"
            rules={[{ required: true, message: '请输入内存分配' }]}
          >
            <Input placeholder="请输入内存大小" />
          </Form.Item>
        </Form>
      </Modal>

      <ServiceDetailDrawer />
      <ApiTestModal 
        visible={apiTestVisible} 
        service={selectedService}
        onClose={() => setApiTestVisible(false)}
      />
    </div>
  );
};

export default ModelServicePage;
