import unittest
from src.core.word_entry import WordEntry, PartOfSpeech

class TestWordEntry(unittest.TestCase):
    
    def test_from_dict_with_str_keys(self):
        """测试 from_dict 方法，interpretations 的键为字符串"""
        data = {
            "Word": "test",
            "Phonetic_UK": "/tɛst/",
            "Phonetic_US": "/test/",
            "Interpretations": {
                "Interp_Noun": "a procedure intended to establish the quality",
                "Interp_Verb": "take measures to check the quality"
            }
        }
        
        entry = WordEntry.from_dict(data)
        
        self.assertEqual(entry.word, "test")
        self.assertEqual(entry.phonetic_UK, "/tɛst/")
        self.assertEqual(entry.phonetic_US, "/test/")
        self.assertEqual(len(entry.interpretations), 2)
        self.assertIn(PartOfSpeech.NOUN, entry.interpretations)
        self.assertIn(PartOfSpeech.VERB, entry.interpretations)
        self.assertEqual(entry.interpretations[PartOfSpeech.NOUN], "a procedure intended to establish the quality")
        self.assertEqual(entry.interpretations[PartOfSpeech.VERB], "take measures to check the quality")
    
    def test_from_dict_with_enum_keys(self):
        """测试 from_dict 方法，interpretations 的键为 PartOfSpeech 枚举"""
        data = {
            "Word": "example",
            "Phonetic_UK": "/ɪɡˈzɑːmpəl/",
            "Phonetic_US": "/ɪɡˈzæmpəl/",
            "Interpretations": {
                PartOfSpeech.NOUN: "a representative form or pattern",
                PartOfSpeech.VERB: "be illustrated or exemplified"
            }
        }
        
        entry = WordEntry.from_dict(data)
        
        self.assertEqual(entry.word, "example")
        self.assertEqual(entry.phonetic_UK, "/ɪɡˈzɑːmpəl/")
        self.assertEqual(entry.phonetic_US, "/ɪɡˈzæmpəl/")
        self.assertEqual(len(entry.interpretations), 2)
        self.assertIn(PartOfSpeech.NOUN, entry.interpretations)
        self.assertIn(PartOfSpeech.VERB, entry.interpretations)
        self.assertEqual(entry.interpretations[PartOfSpeech.NOUN], "a representative form or pattern")
        self.assertEqual(entry.interpretations[PartOfSpeech.VERB], "be illustrated or exemplified")
    
    def test_from_dict_with_mixed_keys(self):
        """测试 from_dict 方法，interpretations 的键混合了字符串和枚举"""
        data = {
            "Word": "mixed",
            "Interpretations": {
                PartOfSpeech.NOUN: "a noun meaning",
                "Interp_Verb": "a verb meaning",
                "Invalid_POS": "this should be ignored"
            }
        }
        
        entry = WordEntry.from_dict(data)
        
        self.assertEqual(entry.word, "mixed")
        self.assertEqual(len(entry.interpretations), 2)  # 应该只有两个有效词性
        self.assertIn(PartOfSpeech.NOUN, entry.interpretations)
        self.assertIn(PartOfSpeech.VERB, entry.interpretations)
        self.assertEqual(entry.interpretations[PartOfSpeech.NOUN], "a noun meaning")
        self.assertEqual(entry.interpretations[PartOfSpeech.VERB], "a verb meaning")
    
    def test_from_flat_dict(self):
        """测试 from_flat_dict 方法"""
        flat_data = {
            "Word": "flat",
            "Phonetic_UK": "/flæt/",
            "Phonetic_US": "/flæt/",
            "Interp_Noun": "a set of rooms for living in",
            "Interp_Adj": "smooth and even",
            "Interp_Verb": "lower (a note) by a semitone",
            "Extra_Field": "this should be ignored"
        }
        
        entry = WordEntry.from_flat_dict(flat_data)
        
        self.assertEqual(entry.word, "flat")
        self.assertEqual(entry.phonetic_UK, "/flæt/")
        self.assertEqual(entry.phonetic_US, "/flæt/")
        self.assertEqual(len(entry.interpretations), 3)
        self.assertIn(PartOfSpeech.NOUN, entry.interpretations)
        self.assertIn(PartOfSpeech.ADJ, entry.interpretations)
        self.assertIn(PartOfSpeech.VERB, entry.interpretations)
        self.assertEqual(entry.interpretations[PartOfSpeech.NOUN], "a set of rooms for living in")
        self.assertEqual(entry.interpretations[PartOfSpeech.ADJ], "smooth and even")
        self.assertEqual(entry.interpretations[PartOfSpeech.VERB], "lower (a note) by a semitone")
    
    def test_from_flat_dict_with_empty_fields(self):
        """测试 from_flat_dict 方法处理空字段"""
        flat_data = {
            "Word": "empty",
            "Phonetic_UK": "",
            "Phonetic_US": "",
            "Interp_Noun": "",
            "Interp_Verb": "only this should be included",
            "Interp_Adj": None,
            "Interp_Adv": "   "  # 只有空白的字符串
        }
        
        entry = WordEntry.from_flat_dict(flat_data)
        
        self.assertEqual(entry.word, "empty")
        self.assertEqual(entry.phonetic_UK, "")
        self.assertEqual(entry.phonetic_US, "")
        self.assertEqual(len(entry.interpretations), 1)  # 应该只有一个有效词性
        self.assertIn(PartOfSpeech.VERB, entry.interpretations)
        self.assertEqual(entry.interpretations[PartOfSpeech.VERB], "only this should be included")
        self.assertNotIn(PartOfSpeech.NOUN, entry.interpretations)
        self.assertNotIn(PartOfSpeech.ADJ, entry.interpretations)
        self.assertNotIn(PartOfSpeech.ADV, entry.interpretations)
    
    def test_to_dict_and_from_dict_consistency(self):
        """测试 to_dict 和 from_dict 方法的往返一致性"""
        original_entry = WordEntry(
            word="consistency",
            phonetic_UK="/kənˈsɪstənsi/",
            phonetic_US="/kənˈsɪstənsi/",
            interpretations={
                PartOfSpeech.NOUN: "conformity in the application of something",
                PartOfSpeech.ADJ: "consistent in performance or behavior"
            }
        )
        
        # 转换为字典再转换回来
        dict_data = original_entry.to_dict()
        restored_entry = WordEntry.from_dict(dict_data)
        
        self.assertEqual(original_entry.word, restored_entry.word)
        self.assertEqual(original_entry.phonetic_UK, restored_entry.phonetic_UK)
        self.assertEqual(original_entry.phonetic_US, restored_entry.phonetic_US)
        self.assertEqual(original_entry.interpretations, restored_entry.interpretations)
    
    def test_to_flat_dict_and_from_flat_dict_consistency(self):
        """测试 to_flat_dict 和 from_flat_dict 方法的往返一致性"""
        original_entry = WordEntry(
            word="flat_consistency",
            phonetic_UK="/flæt kənˈsɪstənsi/",
            phonetic_US="/flæt kənˈsɪstənsi/",
            interpretations={
                PartOfSpeech.NOUN: "a noun meaning",
                PartOfSpeech.VERB: "a verb meaning"
            }
        )
        
        # 转换为平面字典再转换回来
        flat_data = original_entry.to_flat_dict()
        restored_entry = WordEntry.from_flat_dict(flat_data)
        
        self.assertEqual(original_entry.word, restored_entry.word)
        self.assertEqual(original_entry.phonetic_UK, restored_entry.phonetic_UK)
        self.assertEqual(original_entry.phonetic_US, restored_entry.phonetic_US)
        self.assertEqual(original_entry.interpretations, restored_entry.interpretations)

    def test_from_flat_dict_with_enum_keys(self):
        """测试 from_flat_dict 方法处理枚举键的情况"""
        # 创建一个包含枚举键的平面字典
        flat_data = {
            "Word": "enum_key_test",
            "Phonetic_UK": "/ˈiːnəm kiː test/",
            "Phonetic_US": "/ˈinəm ki test/",
            PartOfSpeech.NOUN: "a test for enum keys",
            PartOfSpeech.VERB: "to test with enum keys",
            PartOfSpeech.ADJ: "pertaining to enum key testing"
        }

        entry = WordEntry.from_flat_dict(flat_data)

        self.assertEqual(entry.word, "enum_key_test")
        self.assertEqual(entry.phonetic_UK, "/ˈiːnəm kiː test/")
        self.assertEqual(entry.phonetic_US, "/ˈinəm ki test/")
        self.assertEqual(len(entry.interpretations), 3)
        self.assertIn(PartOfSpeech.NOUN, entry.interpretations)
        self.assertIn(PartOfSpeech.VERB, entry.interpretations)
        self.assertIn(PartOfSpeech.ADJ, entry.interpretations)
        self.assertEqual(entry.interpretations[PartOfSpeech.NOUN], "a test for enum keys")
        self.assertEqual(entry.interpretations[PartOfSpeech.VERB], "to test with enum keys")
        self.assertEqual(entry.interpretations[PartOfSpeech.ADJ], "pertaining to enum key testing")

if __name__ == '__main__':
    unittest.main()