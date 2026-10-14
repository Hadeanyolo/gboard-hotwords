"""Offline tests for destructive import mistakes and selection boundaries."""
import tempfile
from pathlib import Path
import unittest
from zipfile import ZipFile, ZIP_DEFLATED

from convert import Entry, HEADER, ROOT, dictionary_text, load_curated, parse_rime, select_entries, write_dictionary


class DictionaryTests(unittest.TestCase):
    def test_rime_headers_comments_missing_pinyin_and_invalid_words(self):
        text = "name: dict\n...\n# note\n\n苹果\tping guo\t100\n云端推理\tyun duan tui li\t20\n腾讯词库\t100\n网3络\twang san luo\t10\n过长过长过长词\tguo chang guo chang guo chang ci\t10\n模型幻觉\tmo xing huan jue\t12\n"
        entries = list(parse_rime(text, "base"))
        self.assertEqual([e.word for e in entries], ["云端推理", "模型幻觉"])
        self.assertEqual(entries[0].weight, 20)
        with self.assertRaises(ValueError):
            list(parse_rime("name: broken\n", "broken"))

    def test_selection_priority_exclusions_balance_and_collision_cap(self):
        rules = {"topics": {"tech": ["模型"], "online": ["网络"]},
                 "exclude_words": ["基础模型"], "exclude_fragments": ["测试禁词"]}
        curated = [Entry("精选模型", "jing xuan mo xing", 0, "curated", "tech")]
        base = [Entry("精选模型", "jing xuan mo xing", 999, "base"),
                Entry("基础模型", "ji chu mo xing", 9999, "base"),
                Entry("网络安全", "wang luo an quan", 10, "base"),
                Entry("语言模型", "yu yan mo xing", 100, "base"),
                Entry("量化模型", "liang hua mo xing", 20, "base")]
        entries = select_entries(base, curated, rules, limit=3)
        self.assertEqual([e.word for e in entries], ["精选模型", "语言模型", "网络安全"])
        collisions = [Entry(w, "jian suo mo xing", 10-i, "base") for i, w in
                      enumerate(("检索模型", "剪索模型", "减锁模型", "简锁模型"))]
        self.assertEqual(len(select_entries(collisions, [], rules)), 3)

    def test_zip_contains_only_utf8_dictionary_with_exact_tabs(self):
        entry = Entry("模型幻觉", "mo xing huan jue", 0, "curated")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "dict.zip"
            write_dictionary(path, [entry])
            with ZipFile(path) as archive:
                self.assertEqual(archive.namelist(), ["dictionary.txt"])
                self.assertEqual(archive.getinfo("dictionary.txt").compress_type, ZIP_DEFLATED)
                self.assertEqual(archive.read("dictionary.txt").decode("utf-8"),
                                 HEADER + "\nmoxinghuanjue\t模型幻觉\tzh-CN\n")
            with self.assertRaises(ValueError):
                write_dictionary(path, [])
            with self.assertRaises(ValueError):
                write_dictionary(path, [entry, entry])
            with self.assertRaises(ValueError):
                write_dictionary(path, [entry] * 5001)

    def test_curated_is_valid_and_test_words_are_distinct(self):
        entries = load_curated(ROOT / "hotwords.tsv")
        self.assertGreaterEqual(len(entries), 30)
        self.assertEqual(len({e.word for e in entries}), len(entries))
        self.assertTrue(dictionary_text(entries).startswith(HEADER + "\n"))


if __name__ == "__main__":
    unittest.main()
