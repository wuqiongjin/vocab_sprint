import unittest
import threading
import time
import tempfile
import os
from src.core.word_entry import WordEntry, PartOfSpeech
from src.core.word_entry_manager import WordEntryManager
from src.core.word_query_service import WordQueryService
from src.utils.database_manager import DatabaseManager, DataType

class TestWordQueryServiceRealData(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境，使用真实数据库"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # 初始化数据库
        self._init_test_database()
        
        # 创建真实的 DatabaseManager 和 WordEntryManager
        self.database_manager = DatabaseManager(self.db_path)
        self.word_entry_manager = WordEntryManager(self.database_manager, "vocabulary")
        
        # 创建 WordQueryService
        self.query_service = WordQueryService(self.word_entry_manager, debounce_delay=0.1)
        
        # 用于存储搜索结果的列表
        self.search_results = []
        self.result_callback_called = False
        
    def _init_test_database(self):
        """使用DatabaseManager的方法初始化测试数据库"""
        db_manager = DatabaseManager(self.db_path, create_if_not_exist=True)
        
        # 创建表
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
            ("Interp_Others", DataType.TEXT)
        ]
        
        config = {
            "primary_key": "Word",
            "not_null_keys": ["Word"]
        }
        
        db_manager.create_table("vocabulary", columns, config)
        
        # 插入测试数据
        test_data = [
            {
                "Word": "apple", 
                "Phonetic_UK": "ˈæpl", 
                "Phonetic_US": "ˈæpəl", 
                "Interp_Noun": "一种圆形水果，通常是红色、绿色或黄色"
            },
            {
                "Word": "application", 
                "Phonetic_UK": "ˌæplɪˈkeɪʃn", 
                "Phonetic_US": "ˌæpləˈkeɪʃn", 
                "Interp_Noun": "应用程序；应用软件"
            },
            {
                "Word": "apply", 
                "Phonetic_UK": "əˈplaɪ", 
                "Phonetic_US": "əˈplaɪ", 
                "Interp_Verb": "申请；应用"
            },
            {
                "Word": "banana", 
                "Phonetic_UK": "bəˈnɑːnə", 
                "Phonetic_US": "bəˈnænə", 
                "Interp_Noun": "一种长而弯曲的水果，皮黄色，果肉软甜"
            },
            {
                "Word": "computer", 
                "Phonetic_UK": "kəmˈpjuːtə", 
                "Phonetic_US": "kəmˈpjuːtər", 
                "Interp_Noun": "计算机；电脑"
            }
        ]
        
        for data in test_data:
            db_manager.insert_data("vocabulary", data)
        
        db_manager.close()
    
    def tearDown(self):
        """清理测试环境"""
        try:
            if hasattr(self, 'query_service'):
                self.query_service.stop_realtime_search()
                self.query_service.shutdown()
            
            if hasattr(self, 'database_manager'):
                self.database_manager.close()
        except:
            pass
        
        # 等待一下确保文件被释放
        time.sleep(0.1)
        
        # 删除临时数据库文件
        if os.path.exists(self.db_path):
            try:
                os.unlink(self.db_path)
            except:
                # 如果无法删除，忽略错误（临时文件会被系统自动清理）
                pass
    
    def search_results_callback(self, results):
        """真实的回调函数"""
        self.search_results = results
        self.result_callback_called = True
        print(f"回调被调用，找到 {len(results)} 个结果")
        for entry in results:
            meanings = list(entry.interpretations.values())
            main_meaning = meanings[0] if meanings else "无释义"
            print(f"  - {entry.word}: {main_meaning}")
    
    def test_word_entry_manager_initialization(self):
        """测试WordEntryManager是否正确初始化"""
        # 检查WordEntryManager是否成功加载数据
        word_entries = self.word_entry_manager.get_word_dict()
        self.assertEqual(len(word_entries), 5, "应该加载5个单词条目")
        
        # 检查具体条目
        self.assertIn("apple", word_entries)
        self.assertIn("computer", word_entries)
        
        apple_entry = word_entries["apple"]
        self.assertEqual(apple_entry.phonetic_UK, "ˈæpl")
        self.assertEqual(apple_entry.phonetic_US, "ˈæpəl")
        self.assertIn(PartOfSpeech.NOUN, apple_entry.interpretations)
    
    def test_query_exact_match(self):
        """测试精确匹配查询"""
        results = self.query_service.query("apple")
        
        self.assertGreater(len(results), 0, "应该找到结果")
        apple_found = any(entry.word == "apple" for entry in results)
        self.assertTrue(apple_found, "应该找到 'apple'")
    
    def test_query_partial_match(self):
        """测试部分匹配查询"""
        results = self.query_service.query("app")
        
        words = [entry.word for entry in results]
        print(f"部分匹配 'app' 找到的单词: {words}")
        
        # 应该找到 apple, application, apply
        expected_words = {'apple', 'application', 'apply'}
        found_words = set(words)
        self.assertTrue(expected_words.issubset(found_words), 
                       f"应该找到 {expected_words}，实际找到 {found_words}")
    
    def test_query_translation_match(self):
        """测试翻译匹配查询"""
        results = self.query_service.query("应用程序")
        
        self.assertGreater(len(results), 0, "翻译查询应该返回结果")
        
        # 检查是否通过翻译找到了application
        application_found = any(entry.word == "application" for entry in results)
        self.assertTrue(application_found, "应该通过翻译找到 'application'")
    
    def test_real_time_search_basic(self):
        """测试基本实时搜索功能"""
        self.result_callback_called = False
        self.search_results = []
        
        # 启动实时搜索
        self.query_service.start_realtime_search(self.search_results_callback)
        
        # 更新查询
        self.query_service.update_query("banana")
        
        # 等待回调被调用
        timeout = 3.0
        start_time = time.time()
        while not self.result_callback_called and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        self.assertTrue(self.result_callback_called, "回调函数应该被调用")
        self.assertGreater(len(self.search_results), 0, "应该找到一些结果")
        
        banana_found = any(entry.word == "banana" for entry in self.search_results)
        self.assertTrue(banana_found, "应该找到 'banana'")
        
        self.query_service.stop_realtime_search()
    
    def test_add_word_via_manager(self):
        """测试通过WordEntryManager添加新单词"""
        # 创建新单词条目
        new_entry = WordEntry(
            word="python",
            phonetic_UK="ˈpaɪθən",
            phonetic_US="ˈpaɪθɑːn",
            interpretations={
                PartOfSpeech.NOUN: "Python编程语言；蟒蛇"
            }
        )
        
        # 添加新单词
        success = self.word_entry_manager.add_word_entry(new_entry)
        self.assertTrue(success, "应该成功添加新单词")
        
        # 验证新单词可以被查询到
        results = self.query_service.query("python")
        python_found = any(entry.word == "python" for entry in results)
        self.assertTrue(python_found, "应该能找到新添加的 'python'")
    
    def test_empty_query(self):
        """测试空查询"""
        results = self.query_service.query("")
        self.assertEqual(len(results), 0, "空查询应该返回空结果")
    
    def test_word_entry_manager_methods(self):
        """测试WordEntryManager的其他方法"""
        # 测试获取所有单词
        all_words = self.word_entry_manager.get_all_words()
        self.assertEqual(len(all_words), 5, "应该返回5个单词")
        self.assertIn("apple", all_words)
        
        # 测试获取单个单词条目
        apple_entry = self.word_entry_manager.get_word_entry("apple")
        self.assertIsNotNone(apple_entry, "应该能找到apple条目")
        self.assertEqual(apple_entry.word, "apple")
        
        # 测试获取所有条目
        all_entries = self.word_entry_manager.get_all_word_entries()
        self.assertEqual(len(all_entries), 5, "应该返回5个条目")

if __name__ == '__main__':
    unittest.main()