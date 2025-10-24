import React, { useState } from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import RegisterModal from '../components/RegisterModal';

const LoginContainer = styled.div`
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #1890ff 0%, #096dd9 100%);
`;

const LoginCard = styled(Card)`
  width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  
  .ant-card-body {
    padding: 40px;
  }
`;

const LoginPage: React.FC = () => {
  const [registerVisible, setRegisterVisible] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; password: string }) => {
    try {
      // 演示模式：直接登录成功
      message.success('登录成功');
      localStorage.setItem('isLoggedIn', 'true');
      localStorage.setItem('username', values.username); // 保存用户名，可用于显示
      navigate('/computing');
    } catch (error) {
      message.error('登录失败，请稍后重试');
    }
  };

  return (
    <LoginContainer>
      <LoginCard title="模型训练管理系统">
        <Form
          name="login"
          onFinish={onFinish}
          initialValues={{ remember: true }}
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名' }]}
          >
            <Input 
              prefix={<UserOutlined />} 
              placeholder="用户名" 
              size="large"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              size="large"
            />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" block size="large">
              登录
            </Button>
          </Form.Item>

          <Button 
            type="link" 
            onClick={() => setRegisterVisible(true)}
            style={{ float: 'right' }}
          >
            注册新账号
          </Button>
        </Form>
      </LoginCard>

      <RegisterModal
        visible={registerVisible}
        onCancel={() => setRegisterVisible(false)}
      />
    </LoginContainer>
  );
};

export default LoginPage;