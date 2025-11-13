from sql_dependencies.database import db_manager
from typing import List, Optional, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "sql_query",
            "description": "执行SQL查询操作，需要指定数据库名称，不必给出查询语句",
            "parameters": {
                "type": "object",
                "properties": {
                    "database": {
                        "type": "string", 
                        "enum": ["world", "employees", "sakila"],
                        "description": "name of the database to query"
                    },
                    "query": {
                        "type": "string",
                        "description":"natural language description of the query to be performed on the database"
                    }
                },
                "required": ["database", "query"]
                # "required": ["database"]
            }
        }
    },
    # {
    #     "type": "function",
    #     "function": {
    #         "name": "file_operation",
    #         "description": "文件操作",
    #         "parameters": {
    #             "type": "object",
    #             "properties": {
    #                 "operation": {
    #                     "type": "string",
    #                     "enum": ["read", "write", "list"],
    #                     "description": "操作类型"
    #                 },
    #                 "file_path": {
    #                     "type": "string",
    #                     "description": "文件路径"
    #                 },
    #                 "content": {
    #                     "type": "string",
    #                     "description": "文件内容（仅写操作需要）"
    #                 }
    #             },
    #             "required": ["operation", "file_path"]
    #         }
    #     }
    # }
]





async def func_call(model_manager, messages):
        """函数调用处理"""
        # try:
        current_model = model_manager.current_model
        # 使用函数调用生成
        result = await model_manager.generate_func_call(
            messages, 
            tools=TOOLS
        )

        logger.info(f"Function Call Result: \n{json.dumps(result, ensure_ascii=False, indent=2)}")
        # 解析函数调用
       
        if isinstance(result, dict) and "message" in result:
            message = result["message"]
            
            # 检查是否是字典格式的message
            if isinstance(message, dict) and "tool_calls" in message:
                tool_calls = message["tool_calls"]
                logger.info(f"Found tool calls: {len(tool_calls)}")
                
                for tool_call in tool_calls:
                    print(type(tool_call))
                    print(tool_call)
                    if "function" in tool_call and tool_call["function"]["name"] == "sql_query":
                        args = json.loads(tool_call["function"]["arguments"])
                        database = args["database"]
                        database = clean_database_name(database)

                        query_desc = messages # 使用最后一条用户消息作为查询描述
                        #logger.info(f"SQL Query Description: {query_desc}")
                        response, sql_query = await sql_generate_and_execute(
                            model_manager, database, query_desc
                        )
                    
                        #logger.info(f"Generated SQL: {sql_query}")
                        #logger.info(f"Executing SQL on database: {database}")
                        #logger.info(f"Executing response: {response}")
                        #return f"SQL查询结果: {response[:10000]}\n生成的SQL语句: {sql_query}"
                        return {"sql": sql_query, "response": response}

                    elif tool_call["function"]["name"] == "file_operation":
                        args = json.loads(tool_call["function"]["arguments"])
                        # 实现文件操作逻辑
                        return {"message": "文件操作功能待实现"}
        else:
            logger.info("No function calls detected in the response.")
        # 如果没有函数调用，返回普通响应
        return {"message": result.message.content if hasattr(result, 'message') else str(result) }
        
    # except Exception as e:
    #     logger.error(f"函数调用处理错误: {e}")
    #     return "抱歉，处理您的请求时出现错误。"

def clean_database_name(db_name: str) -> str:
    """清理数据库名称"""
    if "employees" in db_name.lower():
        return "employees"
    elif "world" in db_name.lower():
        return "world"
    elif "sakila" in db_name.lower():
        return "sakila"
    return db_name.strip().lower()

async def sql_generate_and_execute(model_manager, database: str, messages) -> str:
    """生成并执行SQL查询"""
    # 构建SQL生成提示词
    with open("services/sql_description.json", 'r', encoding='utf-8') as f:
        sql_templates = json.load(f)
    
    sql_prompt = build_prompt_sql(messages, sql_templates.get(database, {}))

    logger.info(f"SQL Prompt: {sql_prompt}")
    sql_query = await model_manager.generate_text(sql_prompt)
    logger.info(f"Raw SQL Query: {sql_query}")
    cleaned_sql = clean_sql(sql_query)
    logger.info(f"Cleaned SQL Query: {cleaned_sql}")
    
    # 执行SQL查询
    result = await db_manager.execute_query(database, cleaned_sql) 
    
    return result, cleaned_sql

# def build_prompt_sql(query_desc: str, sql_sub_templates: Dict[str, str]) -> str:
#     """构建SQL提示词"""
#     system_prompt = f"""
#     角色设定:
#     你是一个专业的SQL专家，专门生成MySQL查询语句。现在需要针对给出数据库进行查询，这里告诉你了所有的数据库模式。
#     数据库结构信息
#     表清单和字段结构：{json.dumps(sql_sub_templates)}。
#     输出要求
#     请根据我的查询需求，生成准确、优化的MySQL查询语句。只需要提供SQL代码，不需要解释。
#     用户查询：{query_desc}
#     """
#     return system_prompt



# async def func_call(model_manager, messages):
#     """函数调用处理"""
#     try:
#         current_model = model_manager.current_model
#         prompt = build_prompt_func_call(messages)
#         response = await model_manager.generate_text(prompt)
#         logger.info(f"Function Call Response: {response}")

#         response_json = json.loads(clean_response(response))
#     except json.JSONDecodeError as e:
#         logger.error(f"JSON解析错误: {e}")
#         return "抱歉，无法理解您的请求。请尝试重新表述。"
    
#     if response_json["intent"] == "sql_query":
#         database = response_json["database"]
#         response, sql_query = await sql_generate_and_execute(model_manager, database, messages)


#         logger.info(f"Generated SQL: {sql_query}")
#         logger.info(f"Executing SQL on database: {database}")
#         logger.info(f"Excuting response: {response}")

      
#         return f"SQL查询结果: {response[:10000]}\n生成的SQL语句: {sql_query}"
    
#     elif response_json["intent"] == "file_operation":
#         pass
#     else:
#         model_manager.generate_text(prompt)

#         return 

# async def sql_generate_and_execute(model_manager, database: str, messages: List) -> str:
#     """生成并执行SQL查询"""
#     sql_prompt = build_prompt_sql(messages, sql_templates.get(database, {}))

#     sql_query = await model_manager.generate_text(sql_prompt)
#     logger.info(f"Raw SQL Query: {sql_query}")
#     cleaned_sql = clean_sql(sql_query)
#     logger.info(f"Cleaned SQL Query: {cleaned_sql}")
#     # 执行SQL查询
#     result = await db_manager.execute_query(database, cleaned_sql) 
#     return result, cleaned_sql
    

   
def build_prompt_func_call(messages: List) -> str:
    """构建函数调用提示词"""
    System_prompt = """ 
    分析用户意图并返回JSON格式的响应。可能的意图：
    1. sql_query - 当用户想要查询world/employees/sakila数据库时, 使用datbase字段指定数据库名称, world 数据库为 包含国家、城市和语言信息的简单数据库， employees 数据库为 员工管理系统数据库， sakila 数据库为 DVD租赁商店数据库
    2. file_operation - 当用户想要进行文件操作时
    3. general_qa - 普通问答
    
    请直接返回JSON格式，例如：
    - SQL查询: {{"intent": "sql_query", "database": "world"}}
    - 文件操作: {{"intent": "file_operation", "operation": "read", "file_path": "path/to/file"}}
    - 普通问答: {{"intent": "general_qa", "response": "回答内容"}}
    """
    
    
    prompt_parts = []
    prompt_parts.append(f"System: {System_prompt}")

    logger.info(f"Messages for frontend: {messages}")
    for message in messages[-1:]:  # 只取最后一条消息
        if message.role == "system":
            prompt_parts.append(f"System: {message.content}")
        elif message.role == "user":
            prompt_parts.append(f"Human: {message.content}")
        elif message.role == "assistant":
            prompt_parts.append(f"Assistant: {message.content}")
    
    prompt_parts.append("Assistant:")
    
    return "\n\n".join(prompt_parts)



def build_prompt_sql(messages, sql_sub_templates: Dict[str, str]) -> str:
    """构建SQL提示词"""

    system_perompt = f"""
    角色设定:
    你是一个专业的SQL专家，专门生成MySQL查询语句。现在需要针对给出数据库进行查询，这里告诉你了所有的数据库模式。
    数据库结构信息
    表清单和字段结构：{str(sql_sub_templates)}。
    输出要求
    请根据我的查询需求，生成准确、优化的MySQL查询语句。只需要提供SQL代码，不需要解释。
    现在开始：
    """
    messages.append({"role": "system", "content": system_perompt})
    return messages


    
def clean_sql(sql: str) -> str:
    """清理生成的SQL语句"""
    return clean_response(sql).split("sql")[-1].strip().split("```" )[0]


def clean_response(response: str) -> str:
    """清理生成的响应"""
    # 清理<think>, <response>等标签
    return response.split("</think>")[-1]

