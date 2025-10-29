import pymysql
from typing import List, Dict, Any, Optional

class MySQLHelper:
    def __init__(self, host: str = 'localhost', user: str = 'root', 
                 password: str = '', database: str = 'employees', 
                 port: int = 3306, charset: str = 'utf8mb4'):
        """
        初始化MySQL数据库连接
        
        Args:
            host: 数据库主机地址
            user: 用户名
            password: 密码
            database: 数据库名
            port: 端口号
            charset: 字符集
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.charset = charset
        self.connection = None
        self.cursor = None
    
    def connect(self) -> None:
        """建立数据库连接"""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                charset=self.charset,
                cursorclass=pymysql.cursors.DictCursor  # 返回字典格式的结果
            )
            self.cursor = self.connection.cursor()
            print("数据库连接成功！")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            raise
    
    def disconnect(self) -> None:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("数据库连接已关闭。")
    
    def execute_query(self, sql: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询语句并返回结果列表
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            
        Returns:
            包含查询结果的字典列表
        """
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            
            self.cursor.execute(sql, params or ())
            result = self.cursor.fetchall()
            
            # 将结果转换为列表
            result_list = [dict(row) for row in result]
            return result_list
            
        except Exception as e:
            print(f"查询执行失败: {e}")
            raise
    
    def execute_non_query(self, sql: str, params: Optional[tuple] = None) -> int:
        """
        执行非查询语句（INSERT, UPDATE, DELETE）
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            受影响的行数
        """
        try:
            if not self.connection or not self.connection.open:
                self.connect()
            
            affected_rows = self.cursor.execute(sql, params or ())
            self.connection.commit()
            return affected_rows
            
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            print(f"非查询语句执行失败: {e}")
            raise
    
    def get_employees(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取员工列表"""
        sql = "SELECT * FROM employees LIMIT %s"
        return self.execute_query(sql, (limit,))
    
    def get_employees_by_department(self, dept_no: str) -> List[Dict[str, Any]]:
        """根据部门编号获取员工列表"""
        sql = """
        SELECT e.*, d.dept_name 
        FROM employees e 
        JOIN dept_emp de ON e.emp_no = de.emp_no 
        JOIN departments d ON de.dept_no = d.dept_no 
        WHERE de.dept_no = %s
        """
        return self.execute_query(sql, (dept_no,))
    
    def get_employee_by_id(self, emp_no: int) -> List[Dict[str, Any]]:
        """根据员工编号获取员工信息"""
        sql = "SELECT * FROM employees WHERE emp_no = %s"
        return self.execute_query(sql, (emp_no,))
    
    def get_departments(self) -> List[Dict[str, Any]]:
        """获取所有部门列表"""
        sql = "SELECT * FROM departments"
        return self.execute_query(sql)
    
    def get_salaries_by_employee(self, emp_no: int) -> List[Dict[str, Any]]:
        """获取指定员工的薪资历史"""
        sql = "SELECT * FROM salaries WHERE emp_no = %s ORDER BY from_date DESC"
        return self.execute_query(sql, (emp_no,))
    
    def get_employees_with_salary(self, min_salary: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
        """获取员工及其当前薪资"""
        sql = """
        SELECT e.emp_no, e.first_name, e.last_name, s.salary, s.from_date, s.to_date
        FROM employees e
        JOIN salaries s ON e.emp_no = s.emp_no
        WHERE s.salary >= %s AND s.to_date = '9999-01-01'
        LIMIT %s
        """
        return self.execute_query(sql, (min_salary, limit))

# 使用示例
if __name__ == "__main__":
    # 创建数据库助手实例
    db_helper = MySQLHelper(
        host='localhost',
        user='app_user',
        password='Test@000',
        database='employees'
    )
    
    try:
        # 连接数据库
        db_helper.connect()
        
        # 示例1: 获取前10名员工
        employees = db_helper.get_employees(10)
        print("前10名员工:")
        for emp in employees:
            print(f"员工编号: {emp['emp_no']}, 姓名: {emp['first_name']} {emp['last_name']}")
        
        # 示例2: 获取特定部门的员工
        dept_employees = db_helper.get_employees_by_department('d001')
        print(f"\n部门d001的员工数量: {len(dept_employees)}")
        
        # 示例3: 获取所有部门
        departments = db_helper.get_departments()
        print("\n所有部门:")
        for dept in departments:
            print(f"部门编号: {dept['dept_no']}, 部门名称: {dept['dept_name']}")
        
        # 示例4: 自定义查询
        custom_sql = """
        SELECT 
        d.dept_name,
        COUNT(de.dept_no) AS employee_count
        FROM 
        departments d
        LEFT JOIN 
        dept_emp de ON d.dept_no = de.dept_no
        GROUP BY 
        d.dept_name;
        """

        senior_staff = db_helper.execute_query(custom_sql)
        
            
    except Exception as e:
        print(f"操作失败: {e}")
    finally:
        # 关闭连接
        db_helper.disconnect()
