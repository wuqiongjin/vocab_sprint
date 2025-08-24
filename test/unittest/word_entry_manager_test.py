import io
import os
import pytest
import sys
import tempfile

from src.core.word_entry import WordEntry
from src.core.word_entry_manager import WordEntryManager
from src.utils.database_manager import DatabaseManager, DataType
from src.utils.exceptions import TableNotFoundError, InvalidTableStructureError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_test_table(db, table_name="WordEntry"):
    """创建测试用的表结构"""
    columns = [
        ("Word", DataType.TEXT),
        ("Phonetic_UK", DataType.TEXT),
        ("Phonetic_US", DataType.TEXT),
        ("Interp_Noun", DataType.TEXT),
        ("Interp_Verb", DataType.TEXT),
        ("Interp_Adj", DataType.TEXT),
        ("Interp_Adv", DataType.TEXT),
        ("Interp_Pron", DataType.TEXT),
        ("Interp_Prep", DataType.TEXT),
        ("Interp_Conj", DataType.TEXT),
        ("Interp_Intj", DataType.TEXT),
        ("Interp_Art", DataType.TEXT),
        ("Interp_Det", DataType.TEXT),
        ("Interp_Num", DataType.TEXT),
        ("Interp_Aux", DataType.TEXT),
        ("Interp_Others", DataType.TEXT),
    ]
    config = {
        "primary_key": "Word",
        "unique_keys": ["Word"],
        "not_null_keys": ["Word", "Phonetic_UK", "Phonetic_US"],
    }
    return db.create_table(table_name, columns, config)

def test_word_entry_manager_init():
    """测试WordEntryManager初始化"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 创建表
        create_test_table(db)
        
        # 正常初始化
        manager = WordEntryManager(db, "WordEntry")
        assert manager.table_name == "WordEntry"
        assert isinstance(manager.word_dict, dict)
        
        # 测试表不存在的情况
        with pytest.raises(TableNotFoundError):
            WordEntryManager(db, "NonExistentTable")
            
    finally:
        db.close()
        os.unlink(db_path)

def test_invalid_table_structure():
    """测试表结构不匹配的情况"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器
        db = DatabaseManager(db_path, create_if_not_exist=True)
        
        # 创建不匹配的表结构
        columns = [
            ("Word", DataType.TEXT),
            ("Phonetic_UK", DataType.TEXT),
            # 缺少其他必要字段
        ]
        config = {
            "primary_key": "Word",
            "unique_keys": ["Word"],
            "not_null_keys": ["Word", "Phonetic_UK"],
        }
        db.create_table("InvalidTable", columns, config)
        
        # 测试表结构不匹配的情况
        with pytest.raises(InvalidTableStructureError):
            WordEntryManager(db, "InvalidTable")
            
    finally:
        db.close()
        os.unlink(db_path)

def test_add_word_entry():
    """测试添加单词条目功能"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器和表
        db = DatabaseManager(db_path, create_if_not_exist=True)
        create_test_table(db)
        
        manager = WordEntryManager(db, "WordEntry")
        
        # 添加新单词
        word_entry = WordEntry(
            Word="test",
            Phonetic_UK="/test_uk/",
            Phonetic_US="/test_us/",
            Interp_Noun="测试名词",
            Interp_Verb="测试动词"
        )
        result = manager.add_word_entry(word_entry)
        assert result is True
        assert "test" in manager.word_dict
        
        # 验证添加的数据
        added_entry = manager.get_word_entry("test")
        assert added_entry.Word == "test"
        assert added_entry.Phonetic_UK == "/test_uk/"
        assert added_entry.Interp_Noun == "测试名词"
        
        # 尝试添加重复单词
        result2 = manager.add_word_entry(word_entry)
        assert result2 is False
        
    finally:
        db.close()
        os.unlink(db_path)

def test_remove_word_entry():
    """测试删除单词条目功能"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器和表
        db = DatabaseManager(db_path, create_if_not_exist=True)
        create_test_table(db)
        
        manager = WordEntryManager(db, "WordEntry")
        
        # 先添加一个单词
        word_entry = WordEntry(
            Word="test",
            Phonetic_UK="/test_uk/",
            Phonetic_US="/test_us/",
            Interp_Noun="测试"
        )
        manager.add_word_entry(word_entry)
        
        # 删除存在的单词
        result = manager.remove_word_entry("test")
        assert result is True
        assert "test" not in manager.word_dict
        
        # 删除不存在的单词
        result2 = manager.remove_word_entry("nonexistent")
        assert result2 is False
        
    finally:
        db.close()
        os.unlink(db_path)

def test_update_word_entry():
    """测试更新单词条目功能"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器和表
        db = DatabaseManager(db_path, create_if_not_exist=True)
        create_test_table(db)
        
        manager = WordEntryManager(db, "WordEntry")
        
        # 先添加一个单词
        word_entry = WordEntry(
            Word="test",
            Phonetic_UK="/test_uk/",
            Phonetic_US="/test_us/",
            Interp_Noun="测试"
        )
        manager.add_word_entry(word_entry)
        
        # 更新单词
        updated_entry = WordEntry(
            Word="test",
            Phonetic_UK="/updated_uk/",
            Phonetic_US="/updated_us/",
            Interp_Noun="更新后的测试",
            Interp_Verb="动词解释"
        )
        result = manager.update_word_entry("test", updated_entry)
        assert result is True
        
        # 验证更新后的数据
        updated = manager.get_word_entry("test")
        assert updated.Phonetic_UK == "/updated_uk/"
        assert updated.Interp_Noun == "更新后的测试"
        assert updated.Interp_Verb == "动词解释"
        
        # 更新不存在的单词
        result2 = manager.update_word_entry("nonexistent", updated_entry)
        assert result2 is False
        
    finally:
        db.close()
        os.unlink(db_path)

def test_get_methods():
    """测试各种获取方法"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器和表
        db = DatabaseManager(db_path, create_if_not_exist=True)
        create_test_table(db)
        
        manager = WordEntryManager(db, "WordEntry")
        
        # 添加几个单词
        words = [
            WordEntry("word1", "/uk1/", "/us1/", "解释1", "动词1"),
            WordEntry("word2", "/uk2/", "/us2/", "解释2", "动词2"),
            WordEntry("word3", "/uk3/", "/us3/", "解释3", "动词3"),
        ]
        
        for word in words:
            manager.add_word_entry(word)
        
        # 测试获取所有单词
        all_words = manager.get_all_words()
        assert len(all_words) == 3
        assert "word1" in all_words
        assert "word2" in all_words
        assert "word3" in all_words
        
        # 测试获取所有单词条目
        all_entries = manager.get_all_word_entries()
        assert len(all_entries) == 3
        assert isinstance(all_entries[0], WordEntry)
        
        # 测试获取单个单词条目
        entry = manager.get_word_entry("word1")
        assert entry.Word == "word1"
        assert entry.Phonetic_UK == "/uk1/"
        assert entry.Interp_Noun == "解释1"
        assert entry.Interp_Verb == "动词1"
        
        # 测试获取不存在的单词
        entry_none = manager.get_word_entry("nonexistent")
        assert entry_none is None
        
        # 测试获取所有条目字典
        entries_dict = manager.get_word_entries()
        assert isinstance(entries_dict, dict)
        assert len(entries_dict) == 3
        
    finally:
        db.close()
        os.unlink(db_path)

def test_word_entry_with_all_fields():
    """测试使用WordEntry的所有字段"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        # 创建数据库管理器和表
        db = DatabaseManager(db_path, create_if_not_exist=True)
        create_test_table(db)
        
        manager = WordEntryManager(db, "WordEntry")
        
        # 创建一个包含所有字段的WordEntry
        full_entry = WordEntry(
            Word="complete",
            Phonetic_UK="/kəmˈpliːt/",
            Phonetic_US="/kəmˈpliːt/",
            Interp_Noun="完整",
            Interp_Verb="完成",
            Interp_Adj="完全的",
            Interp_Adv="完全地",
            Interp_Pron="代词",
            Interp_Prep="介词",
            Interp_Conj="连词",
            Interp_Intj="感叹词",
            Interp_Art="冠词",
            Interp_Det="限定词",
            Interp_Num="数词",
            Interp_Aux="助动词",
            Interp_Others="其他"
        )
        
        result = manager.add_word_entry(full_entry)
        assert result is True
        
        # 验证所有字段都被正确保存
        retrieved = manager.get_word_entry("complete")
        assert retrieved.Word == "complete"
        assert retrieved.Phonetic_UK == "/kəmˈpliːt/"
        assert retrieved.Interp_Noun == "完整"
        assert retrieved.Interp_Verb == "完成"
        assert retrieved.Interp_Adj == "完全的"
        assert retrieved.Interp_Adv == "完全地"
        assert retrieved.Interp_Pron == "代词"
        assert retrieved.Interp_Prep == "介词"
        assert retrieved.Interp_Conj == "连词"
        assert retrieved.Interp_Intj == "感叹词"
        assert retrieved.Interp_Art == "冠词"
        assert retrieved.Interp_Det == "限定词"
        assert retrieved.Interp_Num == "数词"
        assert retrieved.Interp_Aux == "助动词"
        assert retrieved.Interp_Others == "其他"
        
    finally:
        db.close()
        os.unlink(db_path)

if __name__ == "__main__":
    test_word_entry_manager_init()
    print("[PASSED] WordEntryManager初始化测试通过!")

    test_invalid_table_structure()
    print("[PASSED] 表结构不匹配测试通过!")

    test_add_word_entry()
    print("[PASSED] 添加单词条目测试通过!")

    test_remove_word_entry()
    print("[PASSED] 删除单词条目测试通过!")

    test_update_word_entry()
    print("[PASSED] 更新单词条目测试通过!")

    test_get_methods()
    print("[PASSED] 获取单词条目测试通过!")

    test_word_entry_with_all_fields()
    print("[PASSED] 使用WordEntry的所有字段测试通过!")

    print("\n[ALL PASSED] 所有测试通过!")