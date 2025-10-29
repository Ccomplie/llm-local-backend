# dependencies/database.py
import aiomysql
from aiomysql import create_pool

from fastapi import Depends

class DatabaseDependency:
    def __init__(self):
        self.pool = None
    
    async def initialize(self, **kwargs):
        if self.pool is None:
            self.pool = await create_pool(**kwargs)
    
    async def shutdown(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
    
    async def get_connection(self):
        if self.pool is None:
            raise Exception("Database not initialized")
        return self.pool.acquire()
    
    async def get_cursor(self):
        connection = await self.get_connection()
        cursor = await connection.cursor(aiomysql.DictCursor)
        return connection, cursor

# 全局依赖实例
db_dependency = DatabaseDependency()

# 依赖注入函数
async def get_db():
    connection, cursor = await db_dependency.get_cursor( host='localhost',
                                                        port=3306,
                                                        user='app_user',
                                                        password='Test@000',
                                                        db='employees')
    
    try:
        yield cursor
    finally:
        await cursor.close()
        connection.close()