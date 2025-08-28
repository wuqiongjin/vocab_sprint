import io
import os
import pytest
import sys
import tempfile

from src.utils.database_manager import DatabaseManager, DataType, SelectQuery, OrderDirection
from src.utils.exceptions import ValidationError, DatabaseError, TableNotFoundError, ColumnNotFoundError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_create_table_basic():
    """测试基本表创建功能"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 创建简单表
        columns = [
            ("id", DataType.INTEGER),
            ("name", DataType.TEXT),
            ("age", DataType.INTEGER)
        ]
        
        result = db.create_table("users", columns)
        assert result is True, "表应该创建成功"
        
        # 验证表是否存在
        assert db.check_table_exist("users"), "表应该存在"
        
        # 尝试重复创建（应该返回False）
        result2 = db.create_table("users", columns)
        assert result2 is False, "重复创建应该返回False"
        
    finally:
        db.close()
        os.unlink(db_path)

def test_create_table_with_constraints():
    """测试带各种约束的表创建"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 创建带各种约束的表
        columns = [
            ("id", DataType.INTEGER),
            ("username", DataType.TEXT),
            ("email", DataType.TEXT),
            ("age", DataType.INTEGER),
            ("score", DataType.REAL),
            ("created_at", DataType.DATETIME)
        ]
        
        config = {
            "primary_key": "id",
            "not_null_keys": ["id", "username", "email"],
            "unique_keys": ["username", "email"],
            "default_values": {"score": 0.0, "created_at": "CURRENT_TIMESTAMP"},
            "check_constraints": [("age", ">= 0"), ("score", ">= 0")]
        }
        
        result = db.create_table("users", columns, config)
        assert result is True
        
        # 验证表结构
        table_columns = db.get_table_columns("users")
        assert len(table_columns) == 6
        
        # 验证NOT NULL约束
        id_column = next(col for col in table_columns if col["name"] == "id")
        assert id_column["notnull"] == 1, "id列应该有NOT NULL约束"
        
    finally:
        db.close()
        os.unlink(db_path)

def test_create_table_with_composite_keys():
    """测试复合键功能"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 创建带复合主键和复合唯一键的表
        columns = [
            ("order_id", DataType.INTEGER),
            ("product_id", DataType.INTEGER),
            ("quantity", DataType.INTEGER),
            ("price", DataType.REAL)
        ]
        
        config = {
            "primary_key": ["order_id", "product_id"],
            "not_null_keys": ["order_id", "product_id", "quantity", "price"],
            "unique_keys": [["order_id", "product_id"]]
        }
        
        result = db.create_table("order_items", columns, config)
        assert result is True
        
    finally:
        db.close()
        os.unlink(db_path)

def test_create_table_validation_errors():
    """测试验证错误"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        columns = [("id", DataType.INTEGER), ("name", DataType.TEXT)]
        
        # 测试无效表名
        with pytest.raises(ValidationError):
            db.create_table("", columns)
        
        # 测试空列列表
        with pytest.raises(ValidationError):
            db.create_table("test", [])
        
        # 测试无效主键列
        with pytest.raises(ColumnNotFoundError):
            config = {"primary_key": "invalid_column"}
            db.create_table("test", columns, config)
        
        # 测试无效NOT NULL列
        with pytest.raises(ColumnNotFoundError):
            config = {"not_null_keys": ["invalid_column"]}
            db.create_table("test", columns, config)
        
        # 测试无效唯一键列
        with pytest.raises(ColumnNotFoundError):
            config = {"unique_keys": ["invalid_column"]}
            db.create_table("test", columns, config)
            
    finally:
        db.close()
        os.unlink(db_path)

def test_create_table_with_foreign_keys():
    """测试外键功能"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 先创建被引用的表
        users_columns = [("id", DataType.INTEGER), ("name", DataType.TEXT)]
        db.create_table("users", users_columns, {"primary_key": "id"})
        
        # 创建带外键的表
        orders_columns = [
            ("id", DataType.INTEGER),
            ("user_id", DataType.INTEGER),
            ("amount", DataType.REAL)
        ]
        
        config = {
            "primary_key": "id",
            "foreign_keys": [("user_id", "users", "id")]
        }
        
        result = db.create_table("orders", orders_columns, config)
        assert result is True
        
    finally:
        db.close()
        os.unlink(db_path)

def test_create_table_and_insert_data():
    """测试创建表并插入数据"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 创建表
        columns = [
            ("id", DataType.INTEGER),
            ("name", DataType.TEXT),
            ("email", DataType.TEXT)
        ]
        
        config = {
            "primary_key": "id",
            "not_null_keys": ["id", "name", "email"],
            "unique_keys": ["email"]
        }
        
        db.create_table("users", columns, config)
        
        # 插入数据
        test_data = {
            "id": 1,
            "name": "Alice",
            "email": "alice@example.com"
        }
        
        db.insert_data("users", test_data)
        
        # 验证数据插入
        data = db.export_table_data("users")
        assert len(data) == 1
        assert data[0]['name'] == "Alice"
        
        # 测试唯一约束
        duplicate_data = {
            "id": 2,
            "name": "Bob", 
            "email": "alice@example.com"  # 重复的邮箱
        }
        
        with pytest.raises(DatabaseError):
            db.insert_data("users", duplicate_data)
            
    finally:
        db.close()
        os.unlink(db_path)

def test_create_table_edge_cases():
    """测试边界情况"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 测试空配置
        columns = [("id", DataType.INTEGER), ("name", DataType.TEXT)]
        result = db.create_table("test", columns, {})
        assert result is True
        
        # 测试部分配置
        config = {
            "not_null_keys": ["id"],
            "unique_keys": ["name"]
        }
        result = db.create_table("test2", columns, config)
        assert result is True
        
        # 测试复合唯一键
        config = {
            "unique_keys": [["id", "name"]]
        }
        result = db.create_table("test3", columns, config)
        assert result is True
        
    finally:
        db.close()
        os.unlink(db_path)

def test_default_values():
    """测试默认值功能"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        columns = [
            ("id", DataType.INTEGER),
            ("name", DataType.TEXT),
            ("score", DataType.REAL),
            ("created", DataType.DATETIME)
        ]
        
        config = {
            "default_values": {
                "score": 100.0,
                "created": "CURRENT_TIMESTAMP"
            }
        }
        
        db.create_table("test", columns, config)
        
        # 插入不带默认值字段的数据
        db.insert_data("test", {"id": 1, "name": "Test"})
        
        # 验证默认值
        query = SelectQuery(
            table="test",
            where_clause="id = ?",
            where_args=(1,)
        )
        data = db.select_data(query)
        assert data[0]["score"] == 100.0
        assert data[0]["created"] is not None
        
    finally:
        db.close()
        os.unlink(db_path)


def test_insert_data_edge_cases():
    """测试插入数据的边界情况"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)

        # 加上 NOT NULL 和 UNIQUE，确保能稳定触发异常
        columns = [
            ("id", DataType.INTEGER),
            ("name", DataType.TEXT),
            ("email", DataType.TEXT),
        ]
        config = {
            "primary_key": "id",
            "not_null_keys": ["id", "name"],   # 关键：name 必填
            "unique_keys": ["email"],          # 关键：email 唯一
        }
        db.create_table("users", columns, config)

        # 1) 缺少 NOT NULL 字段 -> 应触发 DatabaseError（NOT NULL constraint failed）
        with pytest.raises(DatabaseError):
            db.insert_data("users", {"id": 1, "email": "a@a.com"})

        # 2) 多余字段 -> 应触发 ColumnNotFoundError（字段不存在的校验）
        with pytest.raises(ColumnNotFoundError):
            db.insert_data("users", {"id": 2, "name": "Bob", "email": "b@b.com", "age": 18})

        # 3) UNIQUE 冲突 -> 应触发 DatabaseError
        db.insert_data("users", {"id": 3, "name": "C", "email": "dup@x.com"})
        with pytest.raises(DatabaseError):
            db.insert_data("users", {"id": 4, "name": "D", "email": "dup@x.com"})

        # 4) 表不存在 -> 应触发 TableNotFoundError（如果你的实现如此命名）
        with pytest.raises(TableNotFoundError):
            db.insert_data("no_such_table", {"id": 1, "name": "X"})

    finally:
        db.close()
        os.unlink(db_path)


def test_update_data():
    """测试更新数据的边界情况"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)

        columns = [
            ("id", DataType.INTEGER),
            ("name", DataType.TEXT),
            ("email", DataType.TEXT),
        ]
        config = {
            "primary_key": "id",
            "not_null_keys": ["id", "name"],
            "unique_keys": ["email"],
        }
        db.create_table("users", columns, config)

        # 插入数据
        db.insert_data("users", {"id": 1, "name": "Alice", "email": "a@a.com"})
        db.insert_data("users", {"id": 2, "name": "Bob", "email": "b@b.com"})

        # 测试更新数据
        db.update_data("users", {"name": "Charlie"}, where_clause="id = ?", where_args=(1,))
        query = SelectQuery(
            table="users",
            columns=["id", "name", "email"],
            where_clause="id = ?",
            where_args=(1,)
        )
        data = db.select_data(query)
        assert data[0]["name"] == "Charlie"

        # 测试更新不存在的数据
        with pytest.raises(DatabaseError):
            db.update_data("users", {"name": "Dave"}, where_clause="id = ?", where_args=(4,), raise_if_no_rows=True)

    finally:
        db.close()
        os.unlink(db_path)

def test_select_and_export_data():
    """测试查询和导出功能"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)

        columns = [("id", DataType.INTEGER), ("name", DataType.TEXT), ("score", DataType.REAL)]
        db.create_table("users", columns, {"primary_key": "id"})

        db.insert_data("users", {"id": 1, "name": "Alice", "score": 95.5})
        db.insert_data("users", {"id": 2, "name": "Bob", "score": 88.0})
        db.insert_data("users", {"id": 3, "name": "Charlie", "score": 70.0})

        # 测试 select_data
        query = SelectQuery(
            table="users",
            where_clause="score > ?",
            where_args=(80,),
            order_by="score",
            order_direction=OrderDirection.DESC
        )
        result = db.select_data(query)
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

        # 测试 limit
        query = SelectQuery(
            table="users",
            limit=1,
            order_by="id",
            order_direction=OrderDirection.ASC
        )
        result = db.select_data(query)
        assert result[0]["id"] == 1

        # 测试 export_table_data
        exported = db.export_table_data("users")
        assert isinstance(exported, list)
        assert all(isinstance(d, dict) for d in exported)
        assert exported[0]['name'] == "Alice"

    finally:
        db.close()
        os.unlink(db_path)


def test_check_table_and_get_columns_errors():
    """测试表存在检查和异常场景"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        db = DatabaseManager(db_path, create_if_not_exist=True)

        columns = [("id", DataType.INTEGER)]
        db.create_table("users", columns)

        # check_table_exist 返回 True / False
        assert db.check_table_exist("users") is True
        assert db.check_table_exist("nonexistent") is False

        # 获取不存在表的列
        with pytest.raises(TableNotFoundError):
            db.get_table_columns("nonexistent")

    finally:
        db.close()
        os.unlink(db_path)


def test_close_multiple_times():
    """测试重复关闭数据库"""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    db = DatabaseManager(db_path, create_if_not_exist=True)
    db.close()
    # 第二次关闭不应报错
    db.close()
    os.unlink(db_path)



if __name__ == "__main__":
    test_create_table_basic()
    print("[PASSED] 基本表创建测试通过")

    test_create_table_with_constraints()
    print("[PASSED] 约束测试通过")

    test_create_table_with_composite_keys()
    print("[PASSED] 复合键测试通过")

    test_create_table_validation_errors()
    print("[PASSED] 验证错误测试通过")

    test_create_table_with_foreign_keys()
    print("[PASSED] 外键测试通过")

    test_create_table_and_insert_data()
    print("[PASSED] 数据操作测试通过")
    
    test_create_table_edge_cases()
    print("[PASSED] 边界情况测试通过")
    
    test_default_values()
    print("[PASSED] 默认值测试通过")

    test_insert_data_edge_cases()
    print("[PASSED] 插入数据边界测试通过")

    test_update_data()
    print("[PASSED] 更新数据测试通过")

    test_select_and_export_data()
    print("[PASSED] 查询和导出测试通过")

    test_check_table_and_get_columns_errors()
    print("[PASSED] 检查和列获取测试通过")

    test_close_multiple_times()
    print("[PASSED] 关闭测试通过")

    print("\n[ALL PASSED] 所有测试通过！")