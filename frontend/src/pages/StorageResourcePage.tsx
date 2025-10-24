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
  Select,
  Space,
  Tabs,
  Upload,
  message,
  Input,
} from 'antd';
import {
  HddOutlined,
  FolderOutlined,
  FileOutlined,
  CloudUploadOutlined,
  SyncOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import { Line } from '@ant-design/plots';

const { Option } = Select;
const { TabPane } = Tabs;

interface StorageInfo {
  key: string;
  id: string;
  name: string;
  type: 'ssd' | 'hdd' | 'nvme';
  totalSpace: number;
  usedSpace: number;
  status: 'normal' | 'warning' | 'error';
  mountPoint: string;
}

interface FileInfo {
  key: string;
  name: string;
  size: number;
  type: 'file' | 'directory';
  path: string;
  modifiedTime: string;
}

const StorageResourcePage: React.FC = () => {
  const [isUploadModalVisible, setIsUploadModalVisible] = useState(false);
  const [uploadForm] = Form.useForm();

  const [searchText, setSearchText] = useState('');
  const [fileTypeFilter, setFileTypeFilter] = useState<string[]>([]);

  const storageData: StorageInfo[] = [
    {
      key: '1',
      id: 'STORAGE-001',
      name: '主存储阵列',
      type: 'ssd',
      totalSpace: 2000,
      usedSpace: 1200,
      status: 'normal',
      mountPoint: '/data/main',
    },
    {
      key: '2',
      id: 'STORAGE-002',
      name: '备份存储',
      type: 'hdd',
      totalSpace: 4000,
      usedSpace: 2800,
      status: 'warning',
      mountPoint: '/data/backup',
    },
  ];

  const fileData: FileInfo[] = [
    {
      key: '1',
      name: 'models/',
      size: 0,
      type: 'directory',
      path: '/data/main/models',
      modifiedTime: '2024-01-15 10:30:00',
    },
    {
      key: '2',
      name: 'resnet50.pth',
      size: 1024,
      type: 'file',
      path: '/data/main/models/resnet50.pth',
      modifiedTime: '2024-01-15 09:15:00',
    },
  ];

  const storageColumns = [
    {
      title: '存储ID',
      dataIndex: 'id',
      key: 'id',
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => {
        const typeMap = {
          ssd: { color: 'blue', text: 'SSD' },
          hdd: { color: 'green', text: 'HDD' },
          nvme: { color: 'purple', text: 'NVMe' },
        };
        return <Tag color={typeMap[type as keyof typeof typeMap].color}>{typeMap[type as keyof typeof typeMap].text}</Tag>;
      },
    },
    {
      title: '存储空间',
      key: 'space',
      render: (record: StorageInfo) => (
        <div>
          <div>{record.usedSpace}GB / {record.totalSpace}GB</div>
          <Progress 
            percent={Math.round((record.usedSpace / record.totalSpace) * 100)} 
            size="small" 
            status={record.usedSpace / record.totalSpace > 0.9 ? 'exception' : 'normal'}
          />
        </div>
      ),
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
      title: '挂载点',
      dataIndex: 'mountPoint',
      key: 'mountPoint',
    },
  ];

  // 添加文件操作列
  const fileColumns = [
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: FileInfo) => (
        <Space>
          {record.type === 'directory' ? <FolderOutlined /> : <FileOutlined />}
          {name}
        </Space>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => size === 0 ? '-' : `${size}MB`,
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag color={type === 'directory' ? 'blue' : 'green'}>
          {type === 'directory' ? '目录' : '文件'}
        </Tag>
      ),
    },
    {
      title: '路径',
      dataIndex: 'path',
      key: 'path',
    },
    {
      title: '修改时间',
      dataIndex: 'modifiedTime',
      key: 'modifiedTime',
    },
    {
      title: '操作',
      key: 'action',
      render: (_: unknown, record: FileInfo) => (
        <Space>
          {record.type === 'file' && (
            <>
              <Button type="link" onClick={() => handleDownload(record)}>
                下载
              </Button>
              <Button type="link" onClick={() => handlePreview(record)}>
                预览
              </Button>
            </>
          )}
          <Button type="link" danger onClick={() => handleDelete(record)}>
            删除
          </Button>
        </Space>
      ),
    },
  ];

  const totalSpace = storageData.reduce((sum, storage) => sum + storage.totalSpace, 0);
  const usedSpace = storageData.reduce((sum, storage) => sum + storage.usedSpace, 0);
  const availableSpace = totalSpace - usedSpace;
  const usageRate = Math.round((usedSpace / totalSpace) * 100);

  const handleUploadModalOk = () => {
    uploadForm.validateFields().then((values) => {
      console.log('上传文件:', values);
      setIsUploadModalVisible(false);
      uploadForm.resetFields();
    });
  };

  const { Dragger } = Upload;

  // 添加上传配置
  const uploadProps = {
    name: 'file',
    multiple: true,
    action: '/api/upload', // 替换为实际的上传接口
    onChange(info: any) {
      const { status } = info.file;
      if (status === 'done') {
        message.success(`${info.file.name} 上传成功`);
      } else if (status === 'error') {
        message.error(`${info.file.name} 上传失败`);
      }
    },
  };

  // 修改上传模态框内容
  const renderUploadModal = () => (
    <Modal
      title="上传文件"
      open={isUploadModalVisible}
      onOk={handleUploadModalOk}
      onCancel={() => setIsUploadModalVisible(false)}
      okText="确认"
      cancelText="取消"
      width={600}
    >
      <Form form={uploadForm} layout="vertical">
        <Form.Item
          name="targetPath"
          label="目标路径"
          rules={[{ required: true, message: '请选择目标路径' }]}
        >
          <Select placeholder="请选择目标路径">
            <Option value="/data/main/models">模型目录</Option>
            <Option value="/data/main/datasets">数据集目录</Option>
          </Select>
        </Form.Item>
        <Form.Item>
          <Dragger {...uploadProps}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
            <p className="ant-upload-hint">
              支持单个或批量上传，单个文件大小不超过500MB
            </p>
          </Dragger>
        </Form.Item>
      </Form>
    </Modal>
  );

  // 添加文件操作处理函数
  const handleDownload = (file: FileInfo) => {
    // TODO: 实现文件下载逻辑
    message.success(`开始下载文件: ${file.name}`);
  };

  const handlePreview = (file: FileInfo) => {
    // TODO: 实现文件预览逻辑
    Modal.info({
      title: '文件预览',
      content: `预览文件: ${file.name}`,
      width: 600,
    });
  };

  const handleDelete = (file: FileInfo) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除 ${file.name} 吗？`,
      okText: '确认',
      cancelText: '取消',
      onOk: () => {
        // TODO: 实现文件删除逻辑
        message.success(`成功删除: ${file.name}`);
      },
    });
  };

  // 添加存储使用趋势数据
  const storageUsageTrend = [
    { date: '2024-01-01', usage: 45 },
    { date: '2024-01-02', usage: 52 },
    { date: '2024-01-03', usage: 49 },
    // ...更多数据
  ];

  // 添加趋势图配置
  const trendConfig = {
    data: storageUsageTrend,
    xField: 'date',
    yField: 'usage',
    smooth: true,
    point: {
      size: 3,
    },
    yAxis: {
      label: {
        formatter: (v: string) => `${v}%`,
      },
    },
  };

  return (
    <div>
      <h2 style={{ marginBottom: 24 }}>存储资源管理</h2>
      
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总存储空间"
              value={totalSpace}
              suffix="GB"
              prefix={<HddOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="已使用空间"
              value={usedSpace}
              suffix="GB"
              prefix={<FileOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="可用空间"
              value={availableSpace}
              suffix="GB"
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="使用率"
              value={usageRate}
              suffix="%"
              valueStyle={{ color: usageRate > 90 ? '#cf1322' : '#3f8600' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="storage" size="large">
        <TabPane tab="存储监控" key="storage">
          <Card title="存储设备状态" extra={<Button icon={<SyncOutlined />}>刷新</Button>}>
            <Table columns={storageColumns} dataSource={storageData} pagination={false} />
          </Card>
        </TabPane>

        <TabPane tab="文件管理" key="files">
          <Card 
            title="文件系统" 
            extra={
              <Space>
                <Input.Search
                  placeholder="搜索文件"
                  onSearch={(value) => setSearchText(value)}
                  style={{ width: 200 }}
                />
                <Select
                  mode="multiple"
                  placeholder="文件类型筛选"
                  onChange={setFileTypeFilter}
                  style={{ width: 150 }}
                >
                  <Option value="directory">目录</Option>
                  <Option value="file">文件</Option>
                </Select>
                <Button 
                  type="primary" 
                  icon={<CloudUploadOutlined />}
                  onClick={() => setIsUploadModalVisible(true)}
                >
                  上传文件
                </Button>
              </Space>
            }
          >
            <Table 
              columns={fileColumns} 
              dataSource={fileData.filter(file => {
                const matchesSearch = file.name.toLowerCase().includes(searchText.toLowerCase());
                const matchesType = fileTypeFilter.length === 0 || fileTypeFilter.includes(file.type);
                return matchesSearch && matchesType;
              })}
              pagination={false} 
            />
          </Card>
        </TabPane>

        <TabPane tab="使用趋势" key="trend">
          <Card title="存储使用趋势">
            <Line {...trendConfig} />
          </Card>
        </TabPane>
      </Tabs>

      {renderUploadModal()}
    </div>
  );
};

export default StorageResourcePage;
