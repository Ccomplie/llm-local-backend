import React, { useState, useEffect } from 'react';
import { Layout, Menu, theme, Switch, ConfigProvider } from 'antd';
import {
  DesktopOutlined,
  HddOutlined,
  SettingOutlined,
  ApiOutlined,
  RobotOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import LoginPage from './pages/LoginPage';
import ComputingResourcePage from './pages/ComputingResourcePage';
import StorageResourcePage from './pages/StorageResourcePage';
import SystemResourcePage from './pages/SystemResourcePage';
import ModelServicePage from './pages/ModelServicePage';
import AgentChatPage from './pages/AgentChatPage';
import './global.css';

const { Header, Content, Sider } = Layout;

const PrivateRoute = ({ children }: { children: React.ReactNode }) => {
  const isLoggedIn = localStorage.getItem('isLoggedIn') === 'true';
  return isLoggedIn ? children : <Navigate to="/login" />;
};

const AppContent: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // 根据当前路径设置选中的菜单项
  const selectedKey = location.pathname.substring(1) || 'agent';

  const menuItems = [
    {
      key: 'agent',
      icon: <RobotOutlined />,
      label: '智能Agent',
    },
    {
      key: 'computing',
      icon: <DesktopOutlined />,
      label: '算力资源管理',
    },
    {
      key: 'storage',
      icon: <HddOutlined />,
      label: '存储资源管理',
    },
    {
      key: 'system',
      icon: <SettingOutlined />,
      label: '系统资源管理',
    },
    {
      key: 'model',
      icon: <ApiOutlined />,
      label: '模型服务管理',
    },
  ];


  // 添加主题切换函数
  const handleThemeChange = (checked: boolean) => {
    setIsDarkMode(checked);
    // 保存主题设置到 localStorage
    localStorage.setItem('theme', checked ? 'dark' : 'light');
    // 更新 body 的 class
    document.body.className = checked ? 'dark-theme' : 'light-theme';
  };

  // 在组件加载时读取保存的主题设置
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
      document.body.className = savedTheme === 'dark' ? 'dark-theme' : 'light-theme';
    }
  }, []);

  return (
    <ConfigProvider
      theme={{
        algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          // 自定义主题令牌
          colorPrimary: isDarkMode ? '#60a5fa' : '#3b82f6',
          // 修改明亮主题的背景色为灰白色
          colorBgContainer: isDarkMode ? '#1f2937' : '#f7f7f7',
          colorBgElevated: isDarkMode ? '#374151' : '#f0f2f5',
          colorText: isDarkMode ? '#e5e7eb' : '#2c3e50',
          colorTextSecondary: isDarkMode ? '#9ca3af' : '#34495e',
          borderRadius: 6,
          boxShadow: isDarkMode 
            ? '0 4px 6px rgba(0, 0, 0, 0.2)' 
            : '0 4px 6px rgba(0, 0, 0, 0.05)',
        },
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
          <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
            <div style={{ padding: '16px', textAlign: 'center' }}>
              <Switch
                checkedChildren={<BulbOutlined />}
                unCheckedChildren={<BulbOutlined />}
                checked={isDarkMode}
                onChange={handleThemeChange}
                style={{ 
                  backgroundColor: isDarkMode ? '#60a5fa' : '#3b82f6',
                  boxShadow: '0 2px 4px var(--shadow)'
                }}
              />
            </div>
            <div className="logo" />
            <Menu
              theme={isDarkMode ? "dark" : "light"}
              defaultSelectedKeys={['agent']}
              mode="inline"
              items={menuItems}
              selectedKeys={[selectedKey]}
              onClick={({ key }) => navigate(`/${key}`)}
              style={{
                backgroundColor: isDarkMode ? '#1f2937' : '#f7f7f7',
              }}
            />
          </Sider>
          <Layout>
            <Header style={{ padding: 0, background: colorBgContainer }}>
              <div style={{ padding: '0 24px', fontSize: '18px', fontWeight: 'bold' }}>
                智能化模型服务管理平台
              </div>
            </Header>
            <Content style={{ margin: '0 16px' }}>
              <div
                style={{
                  padding: 24,
                  minHeight: 360,
                  background: colorBgContainer,
                  borderRadius: borderRadiusLG,
                  margin: '16px 0',
                }}
              >
                <Routes>
                  <Route path="/login" element={<LoginPage />} />
                  <Route path="/computing" element={
                    <PrivateRoute>
                      <ComputingResourcePage />
                    </PrivateRoute>
                  } />
                  <Route path="/storage" element={
                    <PrivateRoute>
                      <StorageResourcePage />
                    </PrivateRoute>
                  } />
                  <Route path="/system" element={
                    <PrivateRoute>
                      <SystemResourcePage />
                    </PrivateRoute>
                  } />
                  <Route path="/model" element={
                    <PrivateRoute>
                      <ModelServicePage />
                    </PrivateRoute>
                  } />
                  <Route path="/agent" element={
                    <PrivateRoute>
                      <AgentChatPage />
                    </PrivateRoute>
                  } />
                  <Route path="/" element={<Navigate to="/login" />} />
                </Routes>
              </div>
            </Content>
          </Layout>
        </Layout>
    </ConfigProvider>
  );
};

const App: React.FC = () => {
  return (
    <Router>
      <AppContent />
    </Router>
  );
};

export default App;

