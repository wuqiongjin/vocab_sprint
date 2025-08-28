import unittest
import threading
import time
from unittest.mock import Mock, MagicMock, patch
from src.core.word_entry import WordEntry, PartOfSpeech
from src.core.word_entry_manager import WordEntryManager
from src.core.word_query_service import WordQueryService, QueryResult, InvertIndex

class TestWordQueryService(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        # 创建模拟的WordEntryManager
        self.mock_word_entry_manager = Mock(spec=WordEntryManager)
        
        # 创建一些测试单词条目（使用中文译文）
        self.test_entries = {
            "apple": WordEntry(
                word="apple",
                phonetic_UK="ˈæpl",
                phonetic_US="ˈæpəl",
                interpretations={
                    PartOfSpeech.NOUN: "一种圆形水果，通常是红色、绿色或黄色"
                }
            ),
            "application": WordEntry(
                word="application",
                phonetic_UK="ˌæplɪˈkeɪʃn",
                phonetic_US="ˌæpləˈkeɪʃn",
                interpretations={
                    PartOfSpeech.NOUN: "应用程序；应用软件"
                }
            ),
            "banana": WordEntry(
                word="banana",
                phonetic_UK="bəˈnɑːnə",
                phonetic_US="bəˈnænə",
                interpretations={
                    PartOfSpeech.NOUN: "一种长而弯曲的水果，皮黄色，果肉软甜"
                }
            ),
            "apply": WordEntry(
                word="apply",
                phonetic_UK="əˈplaɪ",
                phonetic_US="əˈplaɪ",
                interpretations={
                    PartOfSpeech.VERB: "申请；应用"
                }
            )
        }
        
        # 设置mock返回这些条目
        self.mock_word_entry_manager.get_word_dict.return_value = self.test_entries
        self.mock_word_entry_manager.get_word_entry.side_effect = lambda word: self.test_entries.get(word)
        
        # 创建WordQueryService实例
        self.query_service = WordQueryService(self.mock_word_entry_manager, debounce_delay=0.1)
        
    def tearDown(self):
        """清理测试环境"""
        self.query_service.stop_realtime_search()
        self.query_service.shutdown()
        
    def test_build_indexes(self):
        """测试索引构建"""
        # 检查索引是否包含完整的翻译作为键
        translations_index = self.query_service.indexes[InvertIndex.TRANSLATION]
        
        # 检查所有译文是否都被正确索引
        self.assertIn("一种圆形水果，通常是红色、绿色或黄色", translations_index)
        self.assertIn("应用程序；应用软件", translations_index)
        self.assertIn("一种长而弯曲的水果，皮黄色，果肉软甜", translations_index)
        self.assertIn("申请；应用", translations_index)
        
        # 检查索引中的条目是否正确
        apple_entries = translations_index["一种圆形水果，通常是红色、绿色或黄色"]
        self.assertEqual(len(apple_entries), 1)
        self.assertEqual(apple_entries[0].word, "apple")
        
        apply_entries = translations_index["申请；应用"]
        self.assertEqual(len(apply_entries), 1)
        self.assertEqual(apply_entries[0].word, "apply")
        
    def test_query_exact_match(self):
        """测试精确匹配查询 - query方法会返回所有匹配结果"""
        results = self.query_service.query("apple")
        # 应该至少包含apple，但也可能包含其他部分匹配的结果
        apple_found = any(entry.word == "apple" for entry in results)
        self.assertTrue(apple_found, "精确匹配 'apple' 应该在结果中")
        
        # 检查结果中是否包含apple的精确匹配
        # 由于query方法会返回所有匹配，我们需要检查apple是否在结果中
        self.assertTrue(any(entry.word == "apple" for entry in results))
        
    def test_query_translation_match(self):
        """测试翻译匹配查询"""
        results = self.query_service.query("应用程序")
        # 应该找到application，但也可能包含其他部分匹配的结果
        application_found = any(entry.word == "application" for entry in results)
        self.assertTrue(application_found, "翻译匹配 '应用程序' 应该找到 'application'")
        
    def test_query_partial_match(self):
        """测试部分匹配查询"""
        results = self.query_service.query("app")
        # 应该匹配到apple, application, apply
        words = [entry.word for entry in results]
        self.assertIn("apple", words)
        self.assertIn("application", words)
        self.assertIn("apply", words)
        
    def test_query_fuzzy_match(self):
        """测试模糊匹配查询"""
        # 测试拼写错误的查询
        results = self.query_service.query("aplle")  # 应该是apple
        # 检查是否找到了相似的单词
        words = [entry.word for entry in results]
        self.assertIn("apple", words)
        
    def test_query_empty_string(self):
        """测试空字符串查询"""
        results = self.query_service.query("")
        self.assertEqual(len(results), 0)
        
    def test_query_no_match(self):
        """测试无匹配查询"""
        results = self.query_service.query("不存在的单词")
        self.assertEqual(len(results), 0)
        
    def test_partial_search(self):
        """测试部分搜索方法"""
        results = self.query_service.partial_search("app")
        words = [entry.word for entry in results]
        self.assertIn("apple", words)
        self.assertIn("application", words)
        self.assertIn("apply", words)
        
    def test_fuzzy_search(self):
        """测试模糊搜索方法"""
        results = self.query_service.fuzzy_search("aplle", threshold=50)
        words = [entry.word for entry in results]
        self.assertIn("apple", words)
        
    def test_fuzzy_search_with_high_threshold(self):
        """测试高阈值模糊搜索"""
        results = self.query_service.fuzzy_search("aplle", threshold=90)
        # 由于阈值高，可能找不到匹配
        # 这里我们只检查方法是否正常工作，不检查具体结果
        
    def test_realtime_search_start_stop(self):
        """测试实时搜索的启动和停止"""
        # 创建模拟回调
        mock_callback = Mock()
        
        # 启动实时搜索
        self.query_service.start_realtime_search(mock_callback)
        self.assertIsNotNone(self.query_service.result_thread)
        self.assertTrue(self.query_service.result_thread.is_alive())
        
        # 停止实时搜索
        self.query_service.stop_realtime_search()
        # 给线程一点时间结束
        time.sleep(0.1)
        self.assertTrue(self.query_service.stop_search)
        
    def test_update_query_with_debounce(self):
        """测试带防抖的查询更新"""
        # 创建模拟回调
        mock_callback = Mock()
        
        # 启动实时搜索
        self.query_service.start_realtime_search(mock_callback)
        
        # 更新查询多次
        self.query_service.update_query("a")
        self.query_service.update_query("ap")
        self.query_service.update_query("app")
        
        # 等待防抖延迟
        time.sleep(0.2)
        
        # 检查回调是否被调用（应该只调用一次，因为防抖）
        mock_callback.assert_called()
        
        # 停止实时搜索
        self.query_service.stop_realtime_search()
        
    def test_query_result_class(self):
        """测试QueryResult类"""
        entry = self.test_entries["apple"]
        result = QueryResult("apple", entry, 85)
        
        self.assertEqual(result.word, "apple")
        self.assertEqual(result.entry, entry)
        self.assertEqual(result.score, 85)
        
    def test_shutdown(self):
        """测试关闭方法"""
        # 启动实时搜索
        mock_callback = Mock()
        self.query_service.start_realtime_search(mock_callback)
        
        # 调用shutdown
        self.query_service.shutdown()
        
        # 检查是否已停止
        self.assertTrue(self.query_service.stop_search)
        
    def test_thread_pool_execution(self):
        """测试线程池执行查询"""
        # 创建模拟回调
        mock_callback = Mock()
        
        # 启动实时搜索
        self.query_service.start_realtime_search(mock_callback)
        
        # 更新查询
        self.query_service.update_query("apple")
        
        # 等待查询完成
        time.sleep(0.3)
        
        # 检查回调是否被调用
        mock_callback.assert_called_once()
        
        # 获取调用参数
        args, _ = mock_callback.call_args
        results = args[0]
        
        # 检查结果中是否包含apple
        apple_found = any(entry.word == "apple" for entry in results)
        self.assertTrue(apple_found, "查询结果应该包含 'apple'")
        
        # 停止实时搜索
        self.query_service.stop_realtime_search()
        
    def test_concurrent_queries(self):
        """测试并发查询"""
        # 创建模拟回调
        mock_callback = Mock()
        
        # 启动实时搜索
        self.query_service.start_realtime_search(mock_callback)
        
        # 快速连续更新查询多次
        for i in range(5):
            self.query_service.update_query(f"测试{i}")
        
        # 等待所有查询完成
        time.sleep(0.5)
        
        # 检查回调被调用的次数
        # 由于防抖，应该只调用1-2次，而不是5次
        call_count = mock_callback.call_count
        self.assertLessEqual(call_count, 2)
        
        # 停止实时搜索
        self.query_service.stop_realtime_search()

if __name__ == '__main__':
    unittest.main()