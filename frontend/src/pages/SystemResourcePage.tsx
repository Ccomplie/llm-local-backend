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
  Tabs,
  Descriptions,
} from 'antd';
import {
  SettingOutlined,
  MonitorOutlined,
  ApiOutlined,
  DatabaseOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  StopOutlined,
} from '@ant-design/icons';
import { Line } from '@ant-design/plots';

const { Option } = Select;
const { TabPane } = Tabs;

interface SystemInfo {
  key: string;
  metric: string;
  current: number;
  total: number;
  unit: string;
  status: 'normal' | 'warning' | 'error';
  trend: 'up' | 'down' | 'stable';
}

interface ProcessInfo {
  key: string;
  pid: number;
  name: string;
  cpu: number;
  memory: number;
  status: 'running' | 'sleeping' | 'stopped' | 'zombie';
  user: string;
  startTime: string;
  command: string;
}

interface NetworkInfo {
  key: string;
  interface: string;
  ipAddress: string;
  status: 'up' | 'down';
  rxBytes: number;
  txBytes: number;
  rxPackets: number;
  txPackets: number;
  errors: number;
}

interface TrendData {
  timestamp: string;
  value: number;
  metric: string;
}

interface SystemLog {
  key: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error';
  module: string;
  message: string;
}

const SystemResourcePage: React.FC = () => {
  const [isProcessModalVisible, setIsProcessModalVisible] = useState(false);
  const [processDetailVisible, setProcessDetailVisible] = useState(false);
  const [processForm] = Form.useForm();
  const [selectedProcess, setSelectedProcess] = useState<ProcessInfo | null>(null);
  const [trendData] = useState<TrendData[]>([
    { timestamp: '00:00', value: 45, metric: 'CPU' },
    { timestamp: '01:00', value: 52, metric: 'CPU' },
    { timestamp: '02:00', value: 48, metric: 'CPU' },
    { timestamp: '03:00', value: 65, metric: 'CPU' },
    { timestamp: '00:00', value: 55, metric: '内存' },
    { timestamp: '01:00', value: 58, metric: '内存' },
    { timestamp: '02:00', value: 62, metric: '内存' },
    { timestamp: '03:00', value: 68, metric: '内存' },
    { timestamp: '00:00', value: 35, metric: '磁盘' },
    { timestamp: '01:00', value: 38, metric: '磁盘' },
    { timestamp: '02:00', value: 42, metric: '磁盘' },
    { timestamp: '03:00', value: 45, metric: '磁盘' },
  ]);

  const systemData: SystemInfo[] = [
    {
      key: '1',
      metric: 'CPU使用率',
      current: 65,
      total: 100,
      unit: '%',
      status: 'normal',
      trend: 'up',
    },
    {
      key: '2',
      metric: '内存使用率',
      current: 78,
      total: 100,
      unit: '%',
      status: 'warning',
      trend: 'up',
    },
    {
      key: '3',
      metric: '磁盘使用率',
      current: 45,
      total: 100,
      unit: '%',
      status: 'normal',
      trend: 'stable',
    },
    {
      key: '4',
      metric: '网络带宽',
      current: 320,
      total: 1000,
      unit: 'Mbps',
      status: 'normal',
      trend: 'down',
    },
  ];

  const processData: ProcessInfo[] = [
    {
      key: '1',
      pid: 1234,
      name: 'python',
      cpu: 25.5,
      memory: 512,
      status: 'running',
      user: 'train_user',
      startTime: '2024-01-15 09:00:00',
      command: 'python train.py --model resnet50',
    },
    {
      key: '2',
      pid: 1235,
      name: 'tensorboard',
      cpu: 8.2,
      memory: 128,
      status: 'running',
      user: 'train_user',
      startTime: '2024-01-15 09:05:00',
      command: 'tensorboard --logdir logs',
    },
    {
      key: '3',
      pid: 1236,
      name: 'nginx',
      cpu: 2.1,
      memory: 64,
      status: 'running',
      user: 'www-data',
      startTime: '2024-01-15 08:00:00',
      command: 'nginx -g daemon off;',
    },
  ];

  const networkData: NetworkInfo[] = [
    {
      key: '1',
      interface: 'eth0',
      ipAddress: '192.168.1.100',
      status: 'up',
      rxBytes: 1024000,
      txBytes: 512000,
      rxPackets: 1500,
      txPackets: 800,
      errors: 0,
    },
    {
      key: '2',
      interface: 'eth1',
      ipAddress: '10.0.0.50',
      status: 'up',
      rxBytes: 2048000,
      txBytes: 1024000,
      rxPackets: 3000,
      txPackets: 1500,
      errors: 2,
    },
  ];

  const systemColumns = [
    {
      title: '指标',
      dataIndex: 'metric',
      key: 'metric',
    },
    {
      title: '当前值',
      key: 'current',
      render: (record: SystemInfo) => (
        <div>
          <span style={{ fontSize: '18px', fontWeight: 'bold' }}>
            {record.current}{record.unit}
          </span>
          {record.total !== 100 && (
            <span style={{ marginLeft: '8px', color: '#666' }}>
              / {record.total}{record.unit}
            </span>
          )}
        </div>
      ),
    },
    {
      title: '使用率',
      key: 'usage',
      render: (record: SystemInfo) => {
        const percent = record.total === 100 ? record.current : Math.round((record.current / record.total) * 100);
        return (
          <Progress 
            percent={percent} 
            size="small" 
            status={percent > 90 ? 'exception' : 'normal'}
          />
        );
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          normal: { color: 'success', text: '正常' },
          warning: { color: 'warning', text: '警告' },
          error: { color: 'error', text: '错误' },
        };
        return <Tag color={statusMap[status as keyof typeof statusMap].color}>{statusMap[status as keyof typeof statusMap].text}</Tag>;
      },
    },
    {
      title: '趋势',
      dataIndex: 'trend',
      key: 'trend',
      render: (trend: string) => {
        const trendMap = {
          up: { color: 'red', text: '↑ 上升' },
          down: { color: 'green', text: '↓ 下降' },
          stable: { color: 'default', text: '→ 稳定' },
        };
        return <Tag color={trendMap[trend as keyof typeof trendMap].color}>{trendMap[trend as keyof typeof trendMap].text}</Tag>;
      },
    },
  ];

  const processColumns = [
    {
      title: 'PID',
      dataIndex: 'pid',
      key: 'pid',
    },
    {
      title: '进程名',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'CPU使用率',
      dataIndex: 'cpu',
      key: 'cpu',
      render: (value: number) => `${value}%`,
    },
    {
      title: '内存使用',
      dataIndex: 'memory',
      key: 'memory',
      render: (value: number) => `${value}MB`,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const statusMap = {
          running: { color: 'success', text: '运行中' },
          sleeping: { color: 'default', text: '睡眠' },
          stopped: { color: 'warning', text: '停止' },
          zombie: { color: 'error', text: '僵尸' },
        };
        return <Tag color={statusMap[status as keyof typeof statusMap].color}>{statusMap[status as keyof typeof statusMap].text}</Tag>;
      },
    },
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
    },
    {
      title: '启动时间',
      dataIndex: 'startTime',
      key: 'startTime',
    },
    {
      title: '命令',
      dataIndex: 'command',
      key: 'command',
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: ProcessInfo) => (
        <Space>
          <Button 
            type="link"
            onClick={() => {
              setSelectedProcess(record);
              setProcessDetailVisible(true);
            }}
          >
            详情
          </Button>
          {record.status === 'running' ? (
            <Button 
              size="small" 
              icon={<StopOutlined />}
              danger
            >
              停止
            </Button>
          ) : (
            <Button 
              size="small" 
              icon={<PlayCircleOutlined />}
              type="primary"
            >
              启动
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const networkColumns = [
    {
      title: '网络接口',
      dataIndex: 'interface',
      key: 'interface',
    },
    {
      title: 'IP地址',
      dataIndex: 'ipAddress',
      key: 'ipAddress',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'up' ? 'success' : 'error'}>
          {status === 'up' ? '在线' : '离线'}
        </Tag>
      ),
    },
    {
      title: '接收字节',
      dataIndex: 'rxBytes',
      key: 'rxBytes',
      render: (value: number) => `${(value / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '发送字节',
      dataIndex: 'txBytes',
      key: 'txBytes',
      render: (value: number) => `${(value / 1024 / 1024).toFixed(2)} MB`,
    },
    {
      title: '接收包数',
      dataIndex: 'rxPackets',
      key: 'rxPackets',
    },
    {
      title: '发送包数',
      dataIndex: 'txPackets',
      key: 'txPackets',
    },
    {
      title: '错误数',
      dataIndex: 'errors',
      key: 'errors',
      render: (value: number) => (
        <span style={{ color: value > 0 ? '#ff4d4f' : '#52c41a' }}>
          {value}
        </span>
      ),
    },
  ];

  const handleProcessModalOk = () => {
    processForm.validateFields().then((values) => {
      console.log('启动进程:', values);
      setIsProcessModalVisible(false);
      processForm.resetFields();
    });
  };

  const avgCpu = Math.round(systemData.find(item => item.metric === 'CPU使用率')?.current || 0);
  const avgMemory = Math.round(systemData.find(item => item.metric === '内存使用率')?.current || 0);
  const avgDisk = Math.round(systemData.find(item => item.metric === '磁盘使用率')?.current || 0);
  const avgNetwork = Math.round(systemData.find(item => item.metric === '网络带宽')?.current || 0);

  const [systemLogs] = useState<SystemLog[]>([
    {
      key: '1',
      timestamp: '2024-01-15 10:30:00',
      level: 'info',
      module: 'System',
      message: '系统启动完成'
    },
    {
      key: '2',
      timestamp: '2024-01-15 10:35:00',
      level: 'warning',
      module: 'Memory',
      message: '内存使用率超过 80%'
    },
    {
      key: '3',
      timestamp: '2024-01-15 10:40:00',
      level: 'error',
      module: 'Process',
      message: '进程 1234 意外退出'
    },
  ]);

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>系统资源管理</h2>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="CPU使用率"
              value={avgCpu}
              suffix="%"
              prefix={<MonitorOutlined />}
              valueStyle={{ color: avgCpu > 80 ? '#cf1322' : avgCpu > 60 ? '#faad14' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="内存使用率"
              value={avgMemory}
              suffix="%"
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: avgMemory > 80 ? '#cf1322' : avgMemory > 60 ? '#faad14' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="磁盘使用率"
              value={avgDisk}
              suffix="%"
              prefix={<SettingOutlined />}
              valueStyle={{ color: avgDisk > 80 ? '#cf1322' : avgDisk > 60 ? '#faad14' : '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="网络带宽"
              value={avgNetwork}
              suffix="Mbps"
              prefix={<ApiOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="system" size="large">
        <TabPane tab="系统监控" key="system">
          <Card title="系统资源监控" extra={<Button icon={<ReloadOutlined />}>刷新</Button>}>
            <Table columns={systemColumns} dataSource={systemData} pagination={false} />
          </Card>
        </TabPane>

        <TabPane tab="进程管理" key="process">
          <Card 
            title="进程状态" 
            extra={
              <Button 
                type="primary" 
                icon={<PlayCircleOutlined />}
                onClick={() => setIsProcessModalVisible(true)}
              >
                启动进程
              </Button>
            }
          >
            <Table columns={processColumns} dataSource={processData} pagination={false} />
          </Card>
        </TabPane>

        <TabPane tab="网络状态" key="network">
          <Card title="网络接口状态">
            <Table columns={networkColumns} dataSource={networkData} pagination={false} />
          </Card>
        </TabPane>

        <TabPane tab="使用趋势" key="trend">
          <Card title="系统资源使用趋势" extra={<Button icon={<ReloadOutlined />}>刷新</Button>}>
            <Line
              data={trendData}
              xField="timestamp"
              yField="value"
              seriesField="metric"
              smooth
              animation={{
                appear: {
                  animation: 'wave-in',
                  duration: 1000
                }
              }}
              xAxis={{
                title: { text: '时间' }
              }}
              yAxis={{
                title: { text: '使用率 (%)' },
                min: 0,
                max: 100
              }}
              tooltip={{
                showMarkers: false
              }}
              legend={{
                position: 'top'
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab="系统日志" key="logs">
          <Card
            title="系统日志"
            extra={
              <Space>
                <Select defaultValue="all" style={{ width: 120 }}>
                  <Option value="all">所有级别</Option>
                  <Option value="info">信息</Option>
                  <Option value="warning">警告</Option>
                  <Option value="error">错误</Option>
                </Select>
                <Button icon={<ReloadOutlined />}>刷新</Button>
                <Button type="primary">导出日志</Button>
              </Space>
            }
          >
            <Table
              dataSource={systemLogs}
              columns={[
                { 
                  title: '时间',
                  dataIndex: 'timestamp',
                  width: 180
                },
                { 
                  title: '级别',
                  dataIndex: 'level',
                  width: 100,
                  render: (level: string) => {
                    const colorMap = {
                      info: 'blue',
                      warning: 'gold',
                      error: 'red'
                    };
                    return <Tag color={colorMap[level as keyof typeof colorMap]}>{level.toUpperCase()}</Tag>;
                  }
                },
                { 
                  title: '模块',
                  dataIndex: 'module',
                  width: 120
                },
                { 
                  title: '消息',
                  dataIndex: 'message'
                }
              ]}
              pagination={{ pageSize: 10 }}
              scroll={{ y: 400 }}
            />
          </Card>
        </TabPane>
      </Tabs>

      <Modal
        title="启动新进程"
        open={isProcessModalVisible}
        onOk={handleProcessModalOk}
        onCancel={() => setIsProcessModalVisible(false)}
        okText="确认"
        cancelText="取消"
      >
        <Form form={processForm} layout="vertical">
          <Form.Item
            name="processName"
            label="进程名称"
            rules={[{ required: true, message: '请输入进程名称' }]}
          >
            <Input placeholder="请输入进程名称" />
          </Form.Item>
          <Form.Item
            name="command"
            label="启动命令"
            rules={[{ required: true, message: '请输入启动命令' }]}
          >
            <Input placeholder="请输入启动命令" />
          </Form.Item>
          <Form.Item
            name="user"
            label="运行用户"
            rules={[{ required: true, message: '请选择运行用户' }]}
          >
            <Select placeholder="请选择运行用户">
              <Option value="train_user">train_user</Option>
              <Option value="root">root</Option>
              <Option value="www-data">www-data</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="进程详情"
        open={processDetailVisible}
        onCancel={() => {
          setProcessDetailVisible(false);
          setSelectedProcess(null);
        }}
        footer={null}
        width={800}
      >
        {selectedProcess && (
          <div>
            <Descriptions bordered column={2}>
              <Descriptions.Item label="进程ID">{selectedProcess.pid}</Descriptions.Item>
              <Descriptions.Item label="进程名称">{selectedProcess.name}</Descriptions.Item>
              <Descriptions.Item label="CPU使用率">{selectedProcess.cpu}%</Descriptions.Item>
              <Descriptions.Item label="内存使用">{selectedProcess.memory}MB</Descriptions.Item>
              <Descriptions.Item label="运行状态">
                <Tag color={
                  selectedProcess.status === 'running' ? 'success' :
                  selectedProcess.status === 'sleeping' ? 'default' :
                  selectedProcess.status === 'stopped' ? 'warning' : 'error'
                }>
                  {
                    selectedProcess.status === 'running' ? '运行中' :
                    selectedProcess.status === 'sleeping' ? '睡眠' :
                    selectedProcess.status === 'stopped' ? '已停止' : '僵尸'
                  }
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="运行用户">{selectedProcess.user}</Descriptions.Item>
              <Descriptions.Item label="启动时间" span={2}>
                {selectedProcess.startTime}
              </Descriptions.Item>
              <Descriptions.Item label="启动命令" span={2}>
                <Input.TextArea
                  value={selectedProcess.command}
                  autoSize
                  readOnly
                  style={{ width: '100%', backgroundColor: '#f5f5f5' }}
                />
              </Descriptions.Item>
            </Descriptions>
            
            <div style={{ marginTop: 16 }}>
              <h4>实时资源使用</h4>
              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ textAlign: 'center' }}>
                    <h5>CPU使用率</h5>
                    <Progress
                      type="dashboard"
                      percent={selectedProcess.cpu}
                      format={() => `${selectedProcess.cpu}%`}
                    />
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ textAlign: 'center' }}>
                    <h5>内存使用</h5>
                    <Progress
                      type="dashboard"
                      percent={Math.round((selectedProcess.memory / 1024) * 100)}
                      format={() => `${selectedProcess.memory}MB`}
                    />
                  </div>
                </Col>
              </Row>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default SystemResourcePage;



