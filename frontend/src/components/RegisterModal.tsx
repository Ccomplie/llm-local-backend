import React, { useState } from 'react';
import { Modal, Form, Input, Button, message } from 'antd';
import { MailOutlined, UserOutlined, LockOutlined, SafetyOutlined } from '@ant-design/icons';

interface RegisterModalProps {
  visible: boolean;
  onCancel: () => void;
}

const RegisterModal: React.FC<RegisterModalProps> = ({ visible, onCancel }) => {
  const [form] = Form.useForm();
  const [sending, setSending] = useState(false);
  const [countdown, setCountdown] = useState(0);

  const sendVerificationCode = async () => {
    try {
      const email = form.getFieldValue('email');
      if (!email) {
        message.error('请先输入邮箱');
        return;
      }
      
      setSending(true);
      // TODO: 替换为实际的发送验证码API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('验证码已发送到邮箱');
      
      // 开始倒计时
      setCountdown(60);
      const timer = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timer);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
    } catch (error) {
      message.error('发送验证码失败，请稍后重试');
    } finally {
      setSending(false);
    }
  };

  const onFinish = async (values: any) => {
    try {
      if (values.password !== values.confirmPassword) {
        message.error('两次输入的密码不一致');
        return;
      }
      
      // TODO: 替换为实际的注册API调用
      await new Promise(resolve => setTimeout(resolve, 1000));
      message.success('注册成功');
      form.resetFields();
      onCancel();
    } catch (error) {
      message.error('注册失败，请稍后重试');
    }
  };

  return (
    <Modal
      title="注册新账号"
      open={visible}
      onCancel={onCancel}
      footer={null}
      destroyOnClose
    >
      <Form
        form={form}
        name="register"
        onFinish={onFinish}
        autoComplete="off"
      >
        <Form.Item
          name="email"
          rules={[
            { required: true, message: '请输入邮箱' },
            { type: 'email', message: '请输入有效的邮箱地址' }
          ]}
        >
          <Input 
            prefix={<MailOutlined />} 
            placeholder="邮箱" 
          />
        </Form.Item>

        <Form.Item
          name="username"
          rules={[
            { required: true, message: '请输入用户名' },
            { min: 3, message: '用户名至少3个字符' }
          ]}
        >
          <Input 
            prefix={<UserOutlined />} 
            placeholder="用户名" 
          />
        </Form.Item>

        <Form.Item
          name="password"
          rules={[
            { required: true, message: '请输入密码' },
            { min: 6, message: '密码至少6个字符' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="密码"
          />
        </Form.Item>

        <Form.Item
          name="confirmPassword"
          rules={[
            { required: true, message: '请再次输入密码' },
            { min: 6, message: '密码至少6个字符' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="确认密码"
          />
        </Form.Item>

        <Form.Item
          name="verificationCode"
          rules={[{ required: true, message: '请输入验证码' }]}
        >
          <Input
            prefix={<SafetyOutlined />}
            placeholder="验证码"
            suffix={
              <Button
                type="link"
                disabled={countdown > 0 || sending}
                onClick={sendVerificationCode}
              >
                {countdown > 0 ? `${countdown}秒后重试` : '发送验证码'}
              </Button>
            }
          />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" block>
            注册
          </Button>
        </Form.Item>
      </Form>
    </Modal>
  );
};

export default RegisterModal;