import React, { useState } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Table,
  Tag,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Space,
} from 'antd';
import {
  DesktopOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  StopOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './ComputingResourcePage.css';

const { Option } = Select;

interface GPUInfo {
  key: string;
  id: string;
  name: string;
  memory: number;
  memoryUsed: number;
  utilization: number;
  temperature: number;
  status: 'idle' | 'running' | 'error';
  task?: string;
}

interface TaskInfo {
  key: string;
  id: string;
  name: string;
  gpu: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  startTime: string;
  estimatedTime: string;
}

const ComputingResourcePage: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [selectedGPU, setSelectedGPU] = useState<string>('');
  const [form] = Form.useForm();

  // 模拟数据
  const gpuData: GPUInfo[] = [
    {
      key: '1',
      id: 'GPU-001',
      name: 'NVIDIA RTX 4090',
      memory: 24,
      memoryUsed: 18.5,
      utilization: 85,
      temperature: 72,
      status: 'running',
      task: 'ResNet-50训练',
    },
    {
      key: '2',
      id: 'GPU-002',
      name: 'NVIDIA RTX 4080',
      memory: 16,
      memoryUsed: 0,
      utilization: 0,
      temperature: 45,
      status: 'idle',
    },
    {
      key: '3',
      id: 'GPU-003',
      name: 'NVIDIA RTX 4070',
      memory: 12,
      memoryUsed: 8.2,
      utilization: 65,
      temperature: 68,
      status: 'running',
      task: 'BERT微调',
    },
  ];

  const taskData: TaskInfo[] = [
    {
      key: '1',
      id: 'TASK-001',
      name: 'ResNet-50图像分类训练',
      gpu: 'GPU-001',
      status: 'running',
      progress: 75,
      startTime: '2024-01-15 09:00:00',
      estimatedTime: '2024-01-15 18:00:00',
    },
    {
      key: '2',
      id: 'TASK-002',
      name: 'BERT文本分类微调',
      gpu: 'GPU-003',
      status: 'running',
      progress: 45,
      startTime: '2024-01-15 10:30:00',
      estimatedTime: '2024-01-15 20:00:00',
    },
    {
      key: '3',
      id: 'TASK-003',
      name: 'YOLO目标检测训练',
      gpu: 'GPU-002',
      status: 'pending',
      progress: 0,
      startTime: '2024-01-15 14:00:00',
      estimatedTime: '2024-01-16 02:00:00',
    },
  ];

  const performanceData = [
    { time: '00:00', gpu1: 85, gpu2: 0, gpu3: 65 },
    { time: '02:00', gpu1: 88, gpu2: 0, gpu3: 70 },
    { time: '04:00', gpu1: 92, gpu2: 0, gpu3: 75 },
    { time: '06:00', gpu1: 90, gpu2: 0, gpu3: 78 },
    { time: '08:00', gpu1: 87, gpu2: 0, gpu3: 72 },
    { time: '10:00', gpu1: 85, gpu2: 0, gpu3: 65 },
  ];

  const gpuColumns = [
    {
      title: 'GPU ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '型号',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '显存使用',
      key: 'memory',
      render: (record: GPUInfo) => (
        <div>
          <div>{record.memoryUsed}GB / {record.memory}GB</div>
          <Progress 
            percent={Math.round((record.memoryUsed / record.memory) * 100)} 
            size="small" 
            status={record.memoryUsed / record.memory > 0.9 ? 'exception' : 'normal'}
          />
        </div>
      ),
    },
    {
      title: '利用率',
      dataIndex: 'utilization',
      key: 'utilization',
      render: (value: number) => (
        <Progress 
          percent={value} 
          size="small" 
          status={value > 90 ? 'exception' : value > 70 ? 'active' : 'normal'}
        />
      ),
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      render: (value: number) => (
        <span style={{ color: value > 80 ? '#ff4d4f' : value > 70 ? '#faad14' : '#52c41a' }}>
          {value}°C
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          idle: { color: 'default', text: '空闲' },
          running: { color: 'processing', text: '运行中' },
          error: { color: 'error', text: '错误' },
        };
        return <Tag color={statusMap[status as keyof typeof statusMap].color}>{statusMap[status as keyof typeof statusMap].text}</Tag>;
      },
    },
    {
      title: '当前任务',
      dataIndex: 'task',
      key: 'task',
      render: (task: string) => task || '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (record: GPUInfo) => (
        <Space>
          {record.status === 'idle' ? (
            <Button 
              type="primary" 
              size="small" 
              icon={<PlayCircleOutlined />}
              onClick={() => handleStartTask(record.id)}
            >
              分配任务
            </Button>
          ) : (
            <>
              <Button 
                size="small" 
                icon={<PauseCircleOutlined />}
                onClick={() => handlePauseTask(record.id)}
              >
                暂停
              </Button>
              <Button 
                danger 
                size="small" 
                icon={<StopOutlined />}
                onClick={() => handleStopTask(record.id)}
              >
                停止
              </Button>
            </>
          )}
        </Space>
      ),
    },
  ];

  const taskColumns = [
    {
      title: '任务ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '任务名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '分配GPU',
      dataIndex: 'gpu',
      key: 'gpu',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          pending: { color: 'default', text: '等待中' },
          running: { color: 'processing', text: '运行中' },
          completed: { color: 'success', text: '已完成' },
          failed: { color: 'error', text: '失败' },
        };
        return <Tag color={statusMap[status as keyof typeof statusMap].color}>{statusMap[status as keyof typeof statusMap].text}</Tag>;
      },
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (value: number) => <Progress percent={value} size="small" />,
    },
    {
      title: '开始时间',
      dataIndex: 'startTime',
      key: 'startTime',
    },
    {
      title: '预计完成',
      dataIndex: 'estimatedTime',
      key: 'estimatedTime',
    },
  ];

  const handleStartTask = (gpuId: string) => {
    setSelectedGPU(gpuId);
    setIsModalVisible(true);
  };

  const handlePauseTask = (gpuId: string) => {
    // 实现暂停任务逻辑
    console.log('暂停任务:', gpuId);
  };

  const handleStopTask = (gpuId: string) => {
    // 实现停止任务逻辑
    console.log('停止任务:', gpuId);
  };

  const handleModalOk = () => {
    form.validateFields().then((values) => {
      console.log('分配任务:', values);
      setIsModalVisible(false);
      form.resetFields();
    });
  };

  const totalGPUs = gpuData.length;
  const runningGPUs = gpuData.filter(gpu => gpu.status === 'running').length;
  const totalMemory = gpuData.reduce((sum, gpu) => sum + gpu.memory, 0);
  const usedMemory = gpuData.reduce((sum, gpu) => sum + gpu.memoryUsed, 0);
  const avgUtilization = Math.round(gpuData.reduce((sum, gpu) => sum + gpu.utilization, 0) / totalGPUs);

  return (
    <div className="computing-resource-page">
      <div className="page-header">
        <h2>算力资源管理</h2>
        <Button 
          type="primary"
          icon={<ReloadOutlined />}
          onClick={() => console.log('刷新数据')}
        >
          刷新数据
        </Button>
      </div>
      
      {/* 统计概览 */}
      <Row gutter={24} className="stats-overview">
        <Col span={6}>
          <Card hoverable className="stat-card">
            <Statistic
              title={<span className="stat-title">总GPU数量</span>}
              value={totalGPUs}
              prefix={<DesktopOutlined className="stat-icon" />}
              valueStyle={{ color: '#3f8600', fontSize: '28px' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable className="stat-card">
            <Statistic
              title={<span className="stat-title">运行中GPU</span>}
              value={runningGPUs}
              prefix={<PlayCircleOutlined className="stat-icon" />}
              valueStyle={{ color: '#1890ff', fontSize: '28px' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable className="stat-card">
            <Statistic
              title={<span className="stat-title">显存使用率</span>}
              value={Math.round((usedMemory / totalMemory) * 100)}
              suffix="%"
              valueStyle={{ color: usedMemory / totalMemory > 0.8 ? '#cf1322' : '#3f8600', fontSize: '28px' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card hoverable className="stat-card">
            <Statistic
              title={<span className="stat-title">平均利用率</span>}
              value={avgUtilization}
              suffix="%"
              valueStyle={{ color: avgUtilization > 80 ? '#cf1322' : '#3f8600', fontSize: '28px' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 性能监控图表 */}
      <Card 
        title={<span className="card-title">GPU利用率趋势</span>}
        className="chart-card"
      >
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
            <XAxis dataKey="time" stroke="#666" />
            <YAxis stroke="#666" />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255,255,255,0.95)',
                borderRadius: '4px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
              }} 
            />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="gpu1" 
              stroke="#1890ff" 
              strokeWidth={2}
              dot={{ stroke: '#1890ff', strokeWidth: 2 }}
              activeDot={{ r: 6 }}
              name="GPU-001" 
            />
            <Line 
              type="monotone" 
              dataKey="gpu2" 
              stroke="#82ca9d" 
              strokeWidth={2}
              dot={{ stroke: '#82ca9d', strokeWidth: 2 }}
              activeDot={{ r: 6 }}
              name="GPU-002" 
            />
            <Line 
              type="monotone" 
              dataKey="gpu3" 
              stroke="#ffc658" 
              strokeWidth={2}
              dot={{ stroke: '#ffc658', strokeWidth: 2 }}
              activeDot={{ r: 6 }}
              name="GPU-003" 
            />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      {/* GPU状态表格 */}
      <Card 
        title={<span className="card-title">GPU状态监控</span>}
        className="table-card"
      >
        <Table 
          columns={gpuColumns} 
          dataSource={gpuData} 
          pagination={false}
          className="custom-table"
          rowClassName={(record) => record.status === 'running' ? 'running-row' : ''}
        />
      </Card>

      {/* 任务队列表格 */}
      <Card title="任务队列管理">
        <Table 
          columns={taskColumns} 
          dataSource={taskData} 
          pagination={false}
          size="middle"
        />
      </Card>

      {/* 分配任务模态框 */}
      <Modal
        title="分配任务到GPU"
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => setIsModalVisible(false)}
        okText="确认"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="gpuId"
            label="GPU ID"
            initialValue={selectedGPU}
          >
            <Input disabled />
          </Form.Item>
          <Form.Item
            name="taskName"
            label="任务名称"
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="请输入任务名称" />
          </Form.Item>
          <Form.Item
            name="taskType"
            label="任务类型"
            rules={[{ required: true, message: '请选择任务类型' }]}
          >
            <Select placeholder="请选择任务类型">
              <Option value="training">模型训练</Option>
              <Option value="inference">模型推理</Option>
              <Option value="finetune">模型微调</Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="priority"
            label="优先级"
            rules={[{ required: true, message: '请选择优先级' }]}
          >
            <Select placeholder="请选择优先级">
              <Option value="high">高</Option>
              <Option value="medium">中</Option>
              <Option value="low">低</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ComputingResourcePage;



