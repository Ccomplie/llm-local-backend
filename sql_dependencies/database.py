# dependencies/database.py
import aiomysql
import json
import os
from typing import Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.pools: Dict[str, aiomysql.Pool] = {}
        self._initialized = False
        self.configs = {}
    
    async def initialize_from_json(self, config_file: str = "sql_dependencies/conf.json"):
        """从JSON文件初始化数据库连接池"""
        if self._initialized:
            return
        
        # 读取配置文件
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Database config file not found: {config_file}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.configs = json.load(f)
        
        await self._initialize_pools()
    
    async def initialize_from_dict(self, config_dict: Dict[str, Any]):
        """从字典初始化数据库连接池"""
        if self._initialized:
            return
        
        self.configs = config_dict
        await self._initialize_pools()
    
    async def _initialize_pools(self):
        """实际初始化连接池的逻辑"""
        for db_name, config in self.configs.items():
            try:
                # 支持从环境变量覆盖配置（用于生产环境）
                host = os.getenv(f"{db_name.upper()}_DB_HOST", config['host'])
                port = int(os.getenv(f"{db_name.upper()}_DB_PORT", config['port']))
                user = os.getenv(f"{db_name.upper()}_DB_USER", config['user'])
                password = os.getenv(f"{db_name.upper()}_DB_PASSWORD", config['password'])
                database = os.getenv(f"{db_name.upper()}_DB_NAME", config['database'])
                
                self.pools[db_name] = await aiomysql.create_pool(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    db=database,
                    minsize=config.get('minsize', 1),
                    maxsize=config.get('maxsize', 10),
                    autocommit=config.get('autocommit', True)
                )
                logger.info(f"Database pool initialized: {db_name}")
            except Exception as e:
                logger.error(f"Failed to initialize database {db_name}: {e}")
                raise
        
        self._initialized = True
    
    async def shutdown(self):
        """关闭所有数据库连接"""
        for db_name, pool in self.pools.items():
            pool.close()
            await pool.wait_closed()
            logger.info(f"Database pool closed: {db_name}")
        self.pools.clear()
        self._initialized = False
    
    async def get_connection(self, db_name: str):
        """获取数据库连接"""
        if db_name not in self.pools:
            raise ValueError(f"Database '{db_name}' not found")
        return await self.pools[db_name].acquire()
    
    async def execute_query(self, db_name: str, query: str, params: tuple = None):
        """执行查询并返回结果"""
        conn = await self.get_connection(db_name)
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return await cursor.fetchall()
                else:
                    await conn.commit()
                    return cursor.lastrowid
        finally:
            self.pools[db_name].release(conn)
    
    
    async def execute_many(self, db_name: str, query: str, params_list: list):
        """批量执行"""
        conn = await self.get_connection(db_name)
        try:
            async with conn.cursor(aiomysql.DictCursor) as cursor:
                await cursor.executemany(query, params_list)
                await conn.commit()
                return cursor.rowcount
        finally:
            self.pools[db_name].release(conn)
    
    def get_available_databases(self):
        """获取所有可用的数据库名称"""
        return list(self.pools.keys())

# 全局数据库管理器实例
db_manager = DatabaseManager()