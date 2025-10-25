import sqlite3
import random
from datetime import datetime, timedelta
import names

class TestDatabaseCreator:
    def __init__(self, db_name="test_sql/test_database.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        
    def connect(self):
        """连接到SQLite数据库"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"成功连接到数据库: {self.db_name}")
        except sqlite3.Error as e:
            print(f"数据库连接错误: {e}")
            
    def create_tables(self):
        """创建两张表：用户表和订单表"""
        try:
            # 用户表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    age INTEGER,
                    registration_date DATE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 订单表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_name TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    total_amount REAL NOT NULL,
                    order_date DATE NOT NULL,
                    status TEXT CHECK(status IN ('pending', 'completed', 'cancelled')),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            print("成功创建两张表: users 和 orders")
            
        except sqlite3.Error as e:
            print(f"创建表时发生错误: {e}")
            
    def generate_users_data(self, count=50):
        """生成用户测试数据"""
        users_data = []
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com']
        
        for i in range(count):
            first_name = names.get_first_name()
            last_name = names.get_last_name()
            username = f"{first_name.lower()}.{last_name.lower()}"
            email = f"{username}@{random.choice(domains)}"
            age = random.randint(18, 80)
            
            # 生成注册日期（过去1-365天内）
            registration_date = datetime.now() - timedelta(days=random.randint(1, 365))
            
            users_data.append((
                username,
                email,
                first_name,
                last_name,
                age,
                registration_date.strftime('%Y-%m-%d'),
                random.choice([True, False])
            ))
            
        return users_data
    
    def generate_orders_data(self, user_count=50, orders_per_user=5):
        """生成订单测试数据"""
        orders_data = []
        products = [
            "笔记本电脑", "智能手机", "平板电脑", "耳机", "键盘",
            "鼠标", "显示器", "打印机", "摄像头", "路由器"
        ]
        statuses = ['pending', 'completed', 'cancelled']
        
        for user_id in range(1, user_count + 1):
            # 每个用户有0-5个订单
            num_orders = random.randint(0, orders_per_user)
            
            for _ in range(num_orders):
                product_name = random.choice(products)
                quantity = random.randint(1, 5)
                unit_price = round(random.uniform(10.0, 1000.0), 2)
                total_amount = round(quantity * unit_price, 2)
                
                # 生成订单日期（过去30天内）
                order_date = datetime.now() - timedelta(days=random.randint(1, 30))
                
                orders_data.append((
                    user_id,
                    product_name,
                    quantity,
                    unit_price,
                    total_amount,
                    order_date.strftime('%Y-%m-%d'),
                    random.choice(statuses)
                ))
                
        return orders_data
    
    def insert_data(self):
        """插入测试数据到数据库"""
        try:
            # 生成并插入用户数据
            print("正在生成用户数据...")
            users_data = self.generate_users_data(50)
            self.cursor.executemany('''
                INSERT INTO users (username, email, first_name, last_name, age, registration_date, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', users_data)
            
            # 生成并插入订单数据
            print("正在生成订单数据...")
            orders_data = self.generate_orders_data(50, 5)
            self.cursor.executemany('''
                INSERT INTO orders (user_id, product_name, quantity, unit_price, total_amount, order_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', orders_data)
            
            self.conn.commit()
            print(f"成功插入 {len(users_data)} 条用户记录和 {len(orders_data)} 条订单记录")
            
        except sqlite3.Error as e:
            print(f"插入数据时发生错误: {e}")
            self.conn.rollback()
            
    def verify_data(self):
        """验证插入的数据"""
        try:
            # 统计用户数量
            self.cursor.execute("SELECT COUNT(*) FROM users")
            user_count = self.cursor.fetchone()[0]
            
            # 统计订单数量
            self.cursor.execute("SELECT COUNT(*) FROM orders")
            order_count = self.cursor.fetchone()[0]
            
            # 获取活跃用户及其订单信息
            self.cursor.execute('''
                SELECT u.username, u.email, COUNT(o.order_id) as order_count, 
                       SUM(o.total_amount) as total_spent
                FROM users u
                LEFT JOIN orders o ON u.user_id = o.user_id
                WHERE u.is_active = TRUE
                GROUP BY u.user_id
                ORDER BY total_spent DESC
                LIMIT 5
            ''')
            top_customers = self.cursor.fetchall()
            
            print(f"\n数据验证结果:")
            print(f"- 用户总数: {user_count}")
            print(f"- 订单总数: {order_count}")
            print(f"\n前5名活跃客户的消费情况:")
            for customer in top_customers:
                print(f"  用户名: {customer[0]}, 邮箱: {customer[1]}, 订单数: {customer[2]}, 总消费: ¥{customer[3]:.2f}")
                
        except sqlite3.Error as e:
            print(f"验证数据时发生错误: {e}")
            
    def close_connection(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print(f"\n数据库连接已关闭")
            
    def run(self):
        """运行完整的数据库创建流程"""
        print("开始创建测试数据库...")
        self.connect()
        self.create_tables()
        self.insert_data()
        self.verify_data()
        self.close_connection()
        print("测试数据库创建完成！")

# 运行脚本
if __name__ == "__main__":
    # 创建数据库实例
    db_creator = TestDatabaseCreator("test_sql/test_database.db")
    
    # 运行数据库创建流程
    db_creator.run()
    
    # 可选：添加一些额外的查询示例
    print("\n" + "="*50)
    print("额外的查询示例:")
    
    # 重新连接以执行额外查询
    db_creator.connect()
    
    # 示例查询1：按状态统计订单
    db_creator.cursor.execute('''
        SELECT status, COUNT(*) as count, SUM(total_amount) as total
        FROM orders 
        GROUP BY status
    ''')
    status_stats = db_creator.cursor.fetchall()
    print("\n订单状态统计:")
    for stat in status_stats:
        print(f"  状态: {stat[0]}, 数量: {stat[1]}, 总金额: ¥{stat[2]:.2f}")
    
    # 示例查询2：最近注册的用户
    db_creator.cursor.execute('''
        SELECT username, email, registration_date 
        FROM users 
        ORDER BY registration_date DESC 
        LIMIT 3
    ''')
    recent_users = db_creator.cursor.fetchall()
    print("\n最近注册的用户:")
    for user in recent_users:
        print(f"  用户名: {user[0]}, 邮箱: {user[1]}, 注册日期: {user[2]}")
    
    db_creator.close_connection()