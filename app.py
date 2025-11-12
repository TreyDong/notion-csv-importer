#!/usr/bin/env python3
"""
CSV到Notion数据导入的完整Web应用
包含文件上传、数据库关联等功能
"""

import os
import json
import re
import time
import pandas as pd
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(title="CSV到Notion导入工具", description="上传CSV文件并导入到Notion数据库")

# 创建模板目录
templates = Jinja2Templates(directory="templates")

class NotionAPI:
    """Notion API操作类"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def get_database_structure(self, database_id: str) -> Optional[Dict]:
        """获取数据库结构"""
        try:
            url = f"https://api.notion.com/v1/databases/{database_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"获取数据库结构失败: {e}")
            return None
    
    def query_holdings(self, database_id: str, stock_code: str) -> Optional[Dict]:
        """查询持仓数据库中的股票"""
        try:
            # 确保输入参数有效
            if not stock_code or not stock_code.strip():
                print("错误: 证券代码为空，无法查询持仓记录")
                return None
            
            stock_code = stock_code.strip()
            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            
            # 首先获取持仓数据库的结构，以确定正确的字段类型
            holdings_structure = self.get_database_structure(database_id)
            if not holdings_structure:
                print("无法获取持仓数据库结构，使用默认配置")
                # 使用默认配置
                payload = {
                    "filter": {
                        "property": "证券代码",
                        "rich_text": {
                            "equals": stock_code
                        }
                    }
                }
            else:
                # 根据实际数据库结构构建查询
                holdings_properties = holdings_structure.get("properties", {})
                
                # 打印数据库结构以便调试
                print(f"持仓数据库字段: {list(holdings_properties.keys())}")
                
                # 确定证券代码字段的类型
                if "证券代码" in holdings_properties:
                    prop_type = holdings_properties["证券代码"].get("type", "rich_text")
                    print(f"证券代码字段类型: {prop_type}")
                    if prop_type == "title":
                        payload = {
                            "filter": {
                                "property": "证券代码",
                                "title": {
                                    "equals": stock_code
                                }
                            }
                        }
                    elif prop_type == "rich_text":
                        payload = {
                            "filter": {
                                "property": "证券代码",
                                "rich_text": {
                                    "equals": stock_code
                                }
                            }
                        }
                    else:
                        print(f"不支持的证券代码字段类型: {prop_type}")
                        return None
                else:
                    print("持仓数据库中没有找到证券代码字段")
                    # 尝试查找可能的替代字段
                    possible_fields = [k for k in holdings_properties.keys() if "代码" in k or "code" in k.lower()]
                    if possible_fields:
                        print(f"找到可能的替代字段: {possible_fields}")
                    return None
            
            print(f"正在查询持仓记录: {stock_code}")
            print(f"查询请求: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            response = requests.post(url, headers=self.headers, json=payload)
            
            # 检查响应状态
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                print(f"查询结果数量: {len(results)}")
                if results:
                    holding_id = results[0].get("id")
                    print(f"找到持仓记录: {stock_code}，ID: {holding_id}")
                    return results[0]  # 返回第一个匹配的结果
                else:
                    print(f"未找到持仓记录: {stock_code}")
                    return None
            else:
                print(f"查询持仓记录失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"查询持仓记录时网络错误: {str(e)}")
            return None
        except Exception as e:
            print(f"查询持仓记录时未知错误: {str(e)}")
            return None
    
    def create_holding(self, database_id: str, stock_code: str, stock_name: str, market: str = None) -> Optional[str]:
        """在持仓数据库中创建新股票记录"""
        try:
            # 确保输入参数有效
            if not stock_code or not stock_code.strip():
                print("错误: 证券代码为空，无法创建持仓记录")
                return None
            
            if not stock_name or not stock_name.strip():
                stock_name = stock_code  # 如果名称为空，使用代码作为名称
            
            stock_code = stock_code.strip()
            stock_name = stock_name.strip()
            
            url = f"https://api.notion.com/v1/pages"
            
            # 首先获取持仓数据库的结构，以确定正确的字段类型
            holdings_structure = self.get_database_structure(database_id)
            if not holdings_structure:
                print("无法获取持仓数据库结构，使用默认配置")
                # 使用默认配置
                payload = {
                    "parent": {"database_id": database_id},
                    "properties": {
                        "证券代码": {
                            "title": [{"text": {"content": stock_code}}]
                        },
                        "证券名称": {
                            "rich_text": [{"text": {"content": stock_name}}]
                        }
                    }
                }
            else:
                # 根据实际数据库结构构建payload
                holdings_properties = holdings_structure.get("properties", {})
                payload = {
                    "parent": {"database_id": database_id},
                    "properties": {}
                }
                
                # 打印数据库结构以便调试
                print(f"持仓数据库字段: {list(holdings_properties.keys())}")
                
                # 处理证券代码字段
                if "证券代码" in holdings_properties:
                    prop_type = holdings_properties["证券代码"].get("type", "title")
                    print(f"证券代码字段类型: {prop_type}")
                    if prop_type == "title":
                        payload["properties"]["证券代码"] = {
                            "title": [{"text": {"content": stock_code}}]
                        }
                    elif prop_type == "rich_text":
                        payload["properties"]["证券代码"] = {
                            "rich_text": [{"text": {"content": stock_code}}]
                        }
                    else:
                        print(f"不支持的证券代码字段类型: {prop_type}")
                        return None
                else:
                    print("警告: 持仓数据库中没有找到证券代码字段")
                
                # 处理证券名称字段 - 尝试多种可能的字段名
                name_fields = ["证券名称", "名称", "股票名称", "Name"]
                name_field_found = False
                for field_name in name_fields:
                    if field_name in holdings_properties:
                        prop_type = holdings_properties[field_name].get("type", "rich_text")
                        print(f"找到名称字段: {field_name}，类型: {prop_type}")
                        if prop_type == "rich_text":
                            payload["properties"][field_name] = {
                                "rich_text": [{"text": {"content": stock_name}}]
                            }
                        elif prop_type == "title":
                            payload["properties"][field_name] = {
                                "title": [{"text": {"content": stock_name}}]
                            }
                        name_field_found = True
                        break
                
                if not name_field_found:
                    print("警告: 持仓数据库中没有找到任何名称字段")
                
                # 处理市场字段
                if market:
                    market_fields = ["市场", "交易市场", "交易所", "Exchange"]
                    for field_name in market_fields:
                        if field_name in holdings_properties:
                            prop_type = holdings_properties[field_name].get("type", "select")
                            if prop_type == "select":
                                # 根据市场代码设置选择值
                                market_value = "沪市A股" if "沪" in market else "深市A股" if "深" in market else market
                                payload["properties"][field_name] = {
                                    "select": {"name": market_value}
                                }
                                print(f"设置市场字段 {field_name}: {market_value}")
                                break
                
                # 处理股票类型字段
                if stock_code.startswith(("6", "0", "3")):
                    stock_type = "A股"
                elif stock_code.startswith(("5", "688")):
                    stock_type = "科创板"
                elif stock_code.startswith(("8", "4")):
                    stock_type = "新三板"
                else:
                    stock_type = "其他"
                
                type_fields = ["证券类型", "股票类型", "Type"]
                for field_name in type_fields:
                    if field_name in holdings_properties:
                        prop_type = holdings_properties[field_name].get("type", "select")
                        if prop_type == "select":
                            payload["properties"][field_name] = {
                                "select": {"name": stock_type}
                            }
                            print(f"设置类型字段 {field_name}: {stock_type}")
                            break
                
                # 处理交易所代码字段
                if stock_code.startswith("6"):
                    exchange_code = "SH"
                elif stock_code.startswith(("0", "3", "2")):
                    exchange_code = "SZ"
                else:
                    exchange_code = "OTHER"
                
                exchange_fields = ["交易所代码", "Exchange Code"]
                for field_name in exchange_fields:
                    if field_name in holdings_properties:
                        prop_type = holdings_properties[field_name].get("type", "rich_text")
                        if prop_type == "rich_text":
                            payload["properties"][field_name] = {
                                "rich_text": [{"text": {"content": exchange_code}}]
                            }
                            print(f"设置交易所代码字段 {field_name}: {exchange_code}")
                            break
                
                # 设置建仓日期为今天
                today = datetime.now().strftime("%Y-%m-%d")
                date_fields = ["建仓日期", "创建日期", "Date", "Created Date"]
                for field_name in date_fields:
                    if field_name in holdings_properties:
                        prop_type = holdings_properties[field_name].get("type", "date")
                        if prop_type == "date":
                            payload["properties"][field_name] = {
                                "date": {"start": today}
                            }
                            print(f"设置日期字段 {field_name}: {today}")
                            break
                
                # 设置初始持仓数量为0
                quantity_fields = ["持仓数量", "数量", "Quantity"]
                for field_name in quantity_fields:
                    if field_name in holdings_properties:
                        prop_type = holdings_properties[field_name].get("type", "number")
                        if prop_type == "number":
                            payload["properties"][field_name] = {
                                "number": 0
                            }
                            print(f"设置数量字段 {field_name}: 0")
                            break
                
                # 设置初始成本价为0
                price_fields = ["成本价", "价格", "Price"]
                for field_name in price_fields:
                    if field_name in holdings_properties:
                        prop_type = holdings_properties[field_name].get("type", "number")
                        if prop_type == "number":
                            payload["properties"][field_name] = {
                                "number": 0
                            }
                            print(f"设置价格字段 {field_name}: 0")
                            break
                
                # 处理股票字段，按照"股票名称(股票代码)"格式填充
                stock_fields = ["股票", "Stock", "名称", "Name"]
                stock_field_found = False
                for field_name in stock_fields:
                    if field_name in holdings_properties:
                        prop_type = holdings_properties[field_name].get("type", "title")
                        stock_display_name = f"{stock_name}({stock_code})"
                        if prop_type == "title":
                            payload["properties"][field_name] = {
                                "title": [{"text": {"content": stock_display_name}}]
                            }
                        elif prop_type == "rich_text":
                            payload["properties"][field_name] = {
                                "rich_text": [{"text": {"content": stock_display_name}}]
                            }
                        print(f"设置股票字段 {field_name}: {stock_display_name}")
                        stock_field_found = True
                        break
                
                # 如果没有找到股票字段，但有Name字段，创建一个组合名称
                if not stock_field_found and "Name" in holdings_properties and "Name" not in payload["properties"]:
                    stock_display_name = f"{stock_name}({stock_code})"
                    payload["properties"]["Name"] = {
                        "title": [{"text": {"content": stock_display_name}}]
                    }
                    print(f"设置Name字段: {stock_display_name}")
                
                # 如果没有设置任何属性，至少设置一个标题
                if not payload["properties"]:
                    stock_display_name = f"{stock_name}({stock_code})"
                    payload["properties"]["Name"] = {
                        "title": [{"text": {"content": stock_display_name}}]
                    }
                    print(f"设置默认Name字段: {stock_display_name}")
            
            print(f"正在创建持仓记录: {stock_code} - {stock_name}")
            print(f"请求数据: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            response = requests.post(url, headers=self.headers, json=payload)
            
            # 检查响应状态
            if response.status_code == 200:
                result = response.json()
                holding_id = result.get("id")
                print(f"成功创建持仓记录，ID: {holding_id}")
                return holding_id
            else:
                print(f"创建持仓记录失败，状态码: {response.status_code}")
                print(f"响应内容: {response.text}")
                return None
            
        except requests.exceptions.RequestException as e:
            print(f"创建持仓记录时网络错误: {str(e)}")
            return None
        except Exception as e:
            print(f"创建持仓记录时未知错误: {str(e)}")
            return None
    
    def get_existing_entrust_numbers(self, database_id: str) -> set:
        """获取数据库中所有已存在的委托编号"""
        try:
            url = f"https://api.notion.com/v1/databases/{database_id}/query"
            existing_numbers = set()
            
            # 初始查询
            payload = {}
            
            while True:
                response = requests.post(url, headers=self.headers, json=payload)
                response.raise_for_status()
                
                data = response.json()
                results = data.get("results", [])
                
                # 提取委托编号
                for page in results:
                    properties = page.get("properties", {})
                    entrust_no_prop = properties.get("委托编号", {})
                    if entrust_no_prop.get("type") == "rich_text" and entrust_no_prop.get("rich_text"):
                        entrust_no = entrust_no_prop["rich_text"][0]["text"]["content"]
                        existing_numbers.add(entrust_no)
                
                # 检查是否有更多数据
                if not data.get("has_more", False):
                    break
                
                # 设置下一页的游标
                payload["start_cursor"] = data.get("next_cursor")
            
            print(f"已获取 {len(existing_numbers)} 个现有委托编号")
            return existing_numbers
        except Exception as e:
            print(f"获取现有委托编号失败: {e}")
            return set()
    
    def create_page(self, database_id: str, properties_data: Dict) -> bool:
        """创建页面"""
        try:
            url = f"https://api.notion.com/v1/pages"
            
            payload = {
                "parent": {"database_id": database_id},
                "properties": properties_data
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"创建页面失败: {e}")
            return False

class CSVProcessor:
    """CSV和Excel数据处理类"""
    
    @staticmethod
    def clean_excel_formula(value: Any) -> str:
        """清理Excel公式格式"""
        if pd.isna(value) or value == "" or value is None:
            return ""
        
        value = str(value).strip()
        
        # 处理Excel公式格式，如 = "588200      "
        if value.startswith('= "') and value.endswith('"'):
            content = value[3:-1]  # 去掉 '= "' 和最后的 '"'
            return content.strip()
        elif value.startswith('=') and '"' in value:
            # 尝试匹配引号内的内容
            match = re.search(r'"([^"]*)"', value)
            if match:
                return match.group(1).strip()
            # 如果没有匹配到引号内的内容，尝试其他模式
            elif value.startswith('=') and value.endswith('"'):
                # 处理 = "XXXXX" 格式
                content = value[2:-1]
                return content.strip()
        
        return value
    
    @staticmethod
    def process_csv(file_content: str, encoding: str = 'gbk') -> pd.DataFrame:
        """处理CSV文件"""
        try:
            # 从字符串读取CSV
            from io import StringIO
            df = pd.read_csv(StringIO(file_content), encoding=encoding)
            
            # 清理列名，去除空格
            df.columns = [col.strip() for col in df.columns]
            
            # 去除空列
            df = df.dropna(axis=1, how='all')
            
            # 清理数据 - 对所有字段都应用Excel公式清理
            for col in df.columns:
                df[col] = df[col].astype(str)
                df[col] = df[col].apply(CSVProcessor.clean_excel_formula)
                df[col] = df[col].str.strip()
            
            # 特殊处理证券代码字段，确保6位数字格式
            if '证券代码' in df.columns:
                # 确保证券代码是6位数字格式，补齐前导零
                def format_stock_code(code):
                    code_str = str(code).strip()
                    # 如果是纯数字且长度小于6，补齐前导零
                    if code_str.isdigit() and len(code_str) < 6:
                        code_str = code_str.zfill(6)
                    # 如果是纯数字且长度大于6，截取前6位
                    elif code_str.isdigit() and len(code_str) > 6:
                        code_str = code_str[:6]
                    return code_str
                
                df['证券代码'] = df['证券代码'].apply(format_stock_code)
            
            return df
        except UnicodeDecodeError:
            # 如果GBK解码失败，尝试UTF-8
            try:
                from io import StringIO
                df = pd.read_csv(StringIO(file_content), encoding='utf-8')
                
                # 清理列名，去除空格
                df.columns = [col.strip() for col in df.columns]
                
                # 去除空列
                df = df.dropna(axis=1, how='all')
                
                # 清理数据 - 对所有字段都应用Excel公式清理
                for col in df.columns:
                    df[col] = df[col].astype(str)
                    df[col] = df[col].apply(CSVProcessor.clean_excel_formula)
                    df[col] = df[col].str.strip()
                
                # 特殊处理证券代码字段，确保6位数字格式
                if '证券代码' in df.columns:
                    # 确保证券代码是6位数字格式，补齐前导零
                    def format_stock_code(code):
                        code_str = str(code).strip()
                        # 如果是纯数字且长度小于6，补齐前导零
                        if code_str.isdigit() and len(code_str) < 6:
                            code_str = code_str.zfill(6)
                        # 如果是纯数字且长度大于6，截取前6位
                        elif code_str.isdigit() and len(code_str) > 6:
                            code_str = code_str[:6]
                        return code_str
                    
                    df['证券代码'] = df['证券代码'].apply(format_stock_code)
                
                return df
            except Exception as e:
                raise Exception(f"处理CSV文件失败，尝试了GBK和UTF-8编码: {e}")
        except Exception as e:
            raise Exception(f"处理CSV文件失败: {e}")
    
    @staticmethod
    def process_excel(file_content: bytes) -> pd.DataFrame:
        """处理Excel文件（.xls和.xlsx）"""
        try:
            from io import BytesIO
            import tempfile
            import os
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xls') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # 尝试使用openpyxl引擎（适用于.xlsx文件）
                try:
                    df = pd.read_excel(temp_file_path, engine='openpyxl')
                except:
                    # 如果openpyxl失败，尝试xlrd引擎（适用于.xls文件）
                    try:
                        df = pd.read_excel(temp_file_path, engine='xlrd')
                    except:
                        # 如果都失败，尝试作为制表符分隔的文本文件处理
                        df = pd.read_csv(temp_file_path, sep='\t', encoding='gbk')
                
                # 清理列名，去除空格
                df.columns = [col.strip() for col in df.columns]
                
                # 去除空列
                df = df.dropna(axis=1, how='all')
                
                # 清理数据 - 对所有字段都应用Excel公式清理
                for col in df.columns:
                    df[col] = df[col].astype(str)
                    df[col] = df[col].apply(CSVProcessor.clean_excel_formula)
                    df[col] = df[col].str.strip()
                
                # 特殊处理证券代码字段，确保保持文本格式
                if '证券代码' in df.columns:
                    # 确保证券代码是6位数字格式，补齐前导零
                    def format_stock_code(code):
                        code_str = str(code).strip()
                        # 如果是纯数字且长度小于6，补齐前导零
                        if code_str.isdigit() and len(code_str) < 6:
                            code_str = code_str.zfill(6)
                        return code_str
                    
                    df['证券代码'] = df['证券代码'].apply(format_stock_code)
                
                return df
                
            finally:
                # 删除临时文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise Exception(f"处理Excel文件失败: {e}")
    
    @staticmethod
    def process_txt(file_content: bytes, encoding: str = 'gbk') -> pd.DataFrame:
        """处理TXT文件（固定宽度或多空格分隔）"""
        try:
            from io import StringIO
            import tempfile
            import os
            
            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w+b') as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # 定义标准的列名
                expected_columns = [
                    '成交日期', '成交时间', '证券代码', '证券名称', '委托方向',
                    '成交数量', '成交均价', '成交金额', '佣金', '其他费用',
                    '印花税', '过户费', '资金余额', '股份余额', '委托编号',
                    '成交编号', '交易市场', '股东账号', '币种'
                ]

                # 定义需要作为字符串读取的列（避免数字类型自动转换导致前导零丢失）
                dtype_spec = {
                    '证券代码': str,
                    '委托编号': str,
                    '成交编号': str,
                    '股东账号': str
                }

                # 首先尝试多空格分隔
                try:
                    df = pd.read_csv(temp_file_path, sep=r'\s{2,}', encoding=encoding, engine='python', header=None, names=expected_columns, dtype=dtype_spec)
                    print(f"多空格分隔成功，行数: {len(df)}")
                except Exception as e1:
                    print(f"多空格分隔失败: {e1}")
                    # 如果多空格分隔失败，尝试单空格分隔
                    try:
                        df = pd.read_csv(temp_file_path, sep=r'\s+', encoding=encoding, engine='python', header=None, names=expected_columns, dtype=dtype_spec)
                        print(f"单空格分隔成功，行数: {len(df)}")
                    except Exception as e2:
                        print(f"单空格分隔失败: {e2}")
                        # 如果空格分隔都失败，尝试固定宽度格式
                        try:
                            df = pd.read_fwf(temp_file_path, encoding=encoding, header=None, names=expected_columns, dtype=dtype_spec)
                            print(f"固定宽度格式成功，行数: {len(df)}")
                        except Exception as e3:
                            print(f"固定宽度格式失败: {e3}")
                            # 最后尝试制表符分隔
                            try:
                                df = pd.read_csv(temp_file_path, sep='\t', encoding=encoding, header=None, names=expected_columns, dtype=dtype_spec)
                                print(f"制表符分隔成功，行数: {len(df)}")
                            except Exception as e4:
                                print(f"制表符分隔失败: {e4}")
                                raise e4
                
                # 清理列名，去除空格
                df.columns = [col.strip() for col in df.columns]
                
                # 去除空列
                df = df.dropna(axis=1, how='all')
                
                # 清理数据 - 对所有字段都应用Excel公式清理
                for col in df.columns:
                    if col not in ['证券代码', '委托编号', '成交编号', '股东账号']:
                        # 非字符串字段才转换类型
                        df[col] = df[col].astype(str)
                    df[col] = df[col].apply(CSVProcessor.clean_excel_formula)
                    df[col] = df[col].str.strip()

                return df
                
            finally:
                # 删除临时文件
                os.unlink(temp_file_path)
                
        except Exception as e:
            raise Exception(f"处理TXT文件失败: {e}")
    
    @staticmethod
    def convert_value_to_notion_format(value: Any, property_type: str) -> Optional[Dict]:
        """将值转换为Notion API接受的格式"""
        # 处理空值
        if pd.isna(value) or value == "" or value is None or value == "nan":
            return None
        
        # 清理值中的空格
        if isinstance(value, str):
            value = value.strip()
        
        # 根据类型转换
        if property_type == "title":
            return {"title": [{"text": {"content": str(value)}}]}
        elif property_type == "rich_text":
            return {"rich_text": [{"text": {"content": str(value)}}]}
        elif property_type == "number":
            try:
                return {"number": float(value)}
            except (ValueError, TypeError):
                return None
        elif property_type == "select":
            return {"select": {"name": str(value)}}
        elif property_type == "date":
            try:
                if isinstance(value, str):
                    value = value.strip()
                    # 尝试不同的日期格式，包括日期时间格式
                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d", "%Y/%m/%d %H:%M:%S"]:
                        try:
                            date_obj = datetime.strptime(value, fmt)
                            return {"date": {"start": date_obj.isoformat()}}
                        except ValueError:
                            continue
                return {"date": {"start": str(value)}}
            except Exception:
                return None
        elif property_type == "relation":
            return {"relation": [{"id": str(value)}]}
        else:
            print(f"警告: 不支持的属性类型 {property_type}")
            return None

# 数据模型
class ImportRequest(BaseModel):
    limit: Optional[int] = 5
    batch_size: Optional[int] = 10
    delay: Optional[int] = 1

class ImportResponse(BaseModel):
    success: bool
    message: str
    imported_count: int
    total_count: int

# 初始化Notion API
notion_api = NotionAPI(os.getenv("NOTION_TOKEN", ""))

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """主页"""
    return templates.TemplateResponse("index.html", {"request": {}})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), encoding: str = Form("gbk"), limit: int = Form(5), batch_size: int = Form(10), delay: int = Form(1)):
    """上传并处理CSV/Excel文件"""
    
    try:
        # 检查环境变量
        database_id = os.getenv("NOTION_DATABASE_ID", "")
        holdings_db_id = os.getenv("NOTION_HOLDINGS_DATABASE_ID", "")
        
        if not database_id or not holdings_db_id:
            raise HTTPException(status_code=500, detail="数据库ID未配置")
        
        # 读取文件内容
        content = await file.read()
        
        # 根据文件扩展名选择处理方法
        file_extension = file.filename.lower().split('.')[-1] if file.filename else ''
        
        if file_extension in ['xls', 'xlsx']:
            # 处理Excel文件
            df = CSVProcessor.process_excel(content)
        elif file_extension == 'csv':
            # 处理CSV文件
            df = CSVProcessor.process_csv(content.decode(encoding), encoding)
        elif file_extension == 'txt':
            # 处理TXT文件
            df = CSVProcessor.process_txt(content, encoding)
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式，请上传CSV、Excel或TXT文件")
        
        # 获取数据库结构
        db_structure = notion_api.get_database_structure(database_id)
        if not db_structure:
            raise HTTPException(status_code=500, detail="无法获取数据库结构")
        
        db_properties = db_structure.get("properties", {})
        
        # 打印数据库结构以便调试
        print(f"交易数据库字段: {list(db_properties.keys())}")
        
        # 创建映射关系 - 使用智能匹配来处理字段名中的空格
        def find_matching_field(csv_field, db_properties):
            """在数据库属性中查找匹配的字段"""
            # 首先尝试精确匹配
            if csv_field in db_properties:
                return csv_field
            
            # 尝试去除空格后匹配
            clean_field = csv_field.strip()
            if clean_field in db_properties:
                return clean_field
            
            # 尝试在数据库字段中查找包含目标字段的项
            for db_field in db_properties.keys():
                if csv_field in db_field or clean_field in db_field:
                    return db_field
            
            # 如果都没找到，返回原字段名
            return csv_field
        
        # 基础映射关系
        base_mapping = {
            "证券代码": "证券代码",
            "证券名称": "证券名称",
            "委托方向": "委托方向",
            "成交数量": "成交数量",
            "成交均价": "成交均价",
            "成交金额": "成交金额",
            "佣金": "佣金",
            "其他费用": "其他费用",
            "印花税": "印花税",
            "过户费": "过户费",
            "资金余额": "资金余额",
            "股份余额": "股份余额",
            "委托编号": "委托编号",
            "成交编号": "成交编号",
            "交易市场": "交易市场",
            "股东账号": "股东账号",
            "币种": "币种",
            "成交日期": "交易日期"
        }
        
        # 创建智能映射
        mapping = {}
        for csv_field, notion_field in base_mapping.items():
            matched_field = find_matching_field(notion_field, db_properties)
            mapping[csv_field] = matched_field
        
        # 限制导入行数
        if limit > 0 and len(df) > limit:
            df = df.head(limit)
        
        # 获取所有已存在的委托编号
        existing_entrust_numbers = notion_api.get_existing_entrust_numbers(database_id)
        
        # 导入数据
        success_count = 0
        skipped_count = 0
        for index, row in df.iterrows():
            # 检查委托编号是否已存在
            entrust_no = str(row.get("委托编号", "")).strip()
            if entrust_no and entrust_no in existing_entrust_numbers:
                skipped_count += 1
                print(f"跳过重复的委托编号: {entrust_no}")
                continue
            
            properties_data = {}
            
            # 转换每列数据
            for csv_col, notion_prop in mapping.items():
                if csv_col in df.columns and notion_prop in db_properties:
                    value = row[csv_col]
                    prop_type = db_properties[notion_prop].get("type", "rich_text")
                    
                    # 添加调试信息
                    print(f"处理字段: {csv_col} -> {notion_prop}, 值: {value}, 类型: {prop_type}")
                    
                    # 特殊处理交易日期字段，合并日期和时间
                    if csv_col == "成交日期" and notion_prop == "交易日期":
                        time_value = row.get("成交时间", "")
                        if pd.notna(time_value) and time_value != "":
                            date_time_str = f"{value} {time_value}"
                            notion_value = CSVProcessor.convert_value_to_notion_format(date_time_str, prop_type)
                        else:
                            notion_value = CSVProcessor.convert_value_to_notion_format(value, prop_type)
                    else:
                        notion_value = CSVProcessor.convert_value_to_notion_format(value, prop_type)
                    
                    if notion_value is not None:
                        properties_data[notion_prop] = notion_value
                        print(f"成功设置字段 {notion_prop}: {notion_value}")
                    else:
                        print(f"警告: 字段 {notion_prop} 值为空或无效，跳过设置")
            
            # 处理股票持仓关联
            if "股票持仓" in db_properties and "证券代码" in row:
                # 获取交易市场信息
                stock_code = str(row["证券代码"]).strip()
                stock_name = str(row["证券名称"]).strip()
                market = str(row.get("交易市场", "")).strip()
                
                # 确保股票代码不为空
                if not stock_code:
                    print(f"警告: 证券代码为空，跳过持仓关联")
                    continue
                
                print(f"正在处理股票持仓关联: {stock_code} - {stock_name} - {market}")
                
                # 确保股票代码不为空
                if not stock_code:
                    print(f"警告: 证券代码为空，跳过持仓关联")
                    continue
                
                print(f"正在处理股票持仓关联: {stock_code} - {stock_name} - {market}")
                
                # 查询持仓数据库中是否已存在此股票
                holding = notion_api.query_holdings(holdings_db_id, stock_code)
                
                if holding:
                    # 如果存在，使用现有记录
                    properties_data["股票持仓"] = {
                        "relation": [{"id": holding["id"]}]
                    }
                    print(f"找到现有持仓记录: {stock_code} - {stock_name}")
                else:
                    # 如果不存在，创建新记录
                    print(f"未找到持仓记录 {stock_code}，正在创建新记录...")
                    new_holding_id = notion_api.create_holding(holdings_db_id, stock_code, stock_name, market)
                    if new_holding_id:
                        properties_data["股票持仓"] = {
                            "relation": [{"id": new_holding_id}]
                        }
                        print(f"成功创建新持仓记录: {stock_code} - {stock_name}")
                    else:
                        # 如果创建失败，记录错误但继续处理
                        print(f"警告: 无法为股票 {stock_code} 创建持仓记录")
            
            # 添加备注字段，标注为外部导入
            if "备注" in db_properties:
                # 使用UTC+8时区
                from datetime import timezone, timedelta
                tz = timezone(timedelta(hours=8))
                import_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
                properties_data["备注"] = {
                    "rich_text": [{"text": {"content": f"外部导入 - {import_time}"}}]
                }
            
            # 创建页面
            if notion_api.create_page(database_id, properties_data):
                success_count += 1
                # 如果有委托编号，添加到已存在集合中，防止同一批次内重复
                if entrust_no:
                    existing_entrust_numbers.add(entrust_no)
            
            # 添加延迟避免API限制
            if (index + 1) % batch_size == 0:
                time.sleep(delay)
        
        return JSONResponse(content={
            "success": True,
            "message": f"成功导入 {success_count} 行数据，跳过 {skipped_count} 行重复数据",
            "imported_count": success_count,
            "skipped_count": skipped_count,
            "total_count": len(df)
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理文件时出错: {str(e)}")

@app.get("/config")
async def get_config():
    """获取当前配置"""
    return JSONResponse(content={
        "database_id": os.getenv("NOTION_DATABASE_ID", ""),
        "holdings_database_id": os.getenv("NOTION_HOLDINGS_DATABASE_ID", ""),
        "csv_encoding": os.getenv("CSV_ENCODING", "gbk"),
        "configured": bool(os.getenv("NOTION_DATABASE_ID") and os.getenv("NOTION_HOLDINGS_DATABASE_ID"))
    })

if __name__ == "__main__":
    import uvicorn
    
    # 创建模板目录
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    
    # 创建简单的HTML模板
    with open("templates/index.html", "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <title>CSV到Notion导入工具</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background-color: #f9f9f9; padding: 20px; border-radius: 8px; }
        h1 { color: #333; }
        .upload-area { border: 2px dashed #ccc; padding: 20px; margin: 20px 0; text-align: center; }
        .upload-area:hover { border-color: #999; }
        .form-group { margin: 15px 0; }
        label { display: block; margin-bottom: 5px; font-weight: bold; }
        input[type="file"] { width: 100%; padding: 8px; margin-bottom: 10px; }
        input[type="number"] { padding: 8px; width: 100px; }
        button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background-color: #45a049; }
        .status { margin-top: 20px; padding: 10px; border-radius: 4px; }
        .success { background-color: #d4edda; color: #155724; }
        .error { background-color: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>CSV到Notion导入工具</h1>
        
        <div class="upload-area">
            <form action="/upload" method="post" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="file">选择CSV文件:</label>
                    <input type="file" id="file" name="file" accept=".csv" required>
                </div>
                
                <div class="form-group">
                    <label for="limit">导入行数限制 (0表示全部):</label>
                    <input type="number" id="limit" name="limit" value="5">
                </div>
                
                <div class="form-group">
                    <label for="batch_size">批量处理大小:</label>
                    <input type="number" id="batch_size" name="batch_size" value="10">
                </div>
                
                <div class="form-group">
                    <label for="delay">请求间隔(秒):</label>
                    <input type="number" id="delay" name="delay" value="1">
                </div>
                
                <button type="submit">上传并导入</button>
            </form>
        </div>
        
        <div id="status" class="status" style="display: none;"></div>
    </div>
    
    <script>
        document.querySelector('form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const statusDiv = document.getElementById('status');
            statusDiv.style.display = 'block';
            statusDiv.className = 'status';
            statusDiv.innerHTML = '正在上传和处理文件...';
            
            const formData = new FormData(e.target);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    statusDiv.className = 'status success';
                    statusDiv.innerHTML = data.message;
                } else {
                    statusDiv.className = 'status error';
                    statusDiv.innerHTML = '导入失败: ' + data.message;
                }
            })
            .catch(error => {
                statusDiv.className = 'status error';
                statusDiv.innerHTML = '错误: ' + error.message;
            });
        });
    </script>
</body>
</html>""")
    
    # 启动FastAPI应用
    uvicorn.run(app, host="0.0.0.0", port=8000)