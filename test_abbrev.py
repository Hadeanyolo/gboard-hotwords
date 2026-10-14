import tempfile
from pathlib import Path
import unittest
from zipfile import ZipFile

from build_abbrev import Abbreviation, merge_pairs, normalize_code, parse_upstream, write_zip


class AbbreviationTests(unittest.TestCase):
    def test_chinese_initials_and_accented_n(self):
        self.assertEqual(normalize_code("有一说一", "yyuy"), "yysy")
        self.assertEqual(normalize_code("你说的", "nud"), "nsd")
        self.assertEqual(normalize_code("安装", "av"), "az")
        self.assertEqual(normalize_code("嗯呐嗯呐", "ǹnǹn"), "nnnn")

    def test_english_and_mixed_codes_do_not_get_corrupted(self):
        for word, code in [("PVP", "pvp"), ("SKU", "sku"), ("TUI", "tui"), ("H股", "hgu"), ("AA制", "aav")]:
            self.assertEqual(normalize_code(word, code), code)

    def test_only_identical_pairs_removed_and_collision_variants_retained(self):
        a = Abbreviation("qswl", "千丝万缕", "qswl", "wanxiang")
        b = Abbreviation("qswl", "千思万虑", "qswl", "wanxiang")
        c = Abbreviation("qs", "千丝万缕", "qs", "wanxiang")
        result = merge_pairs([a, b, a, c], [])
        self.assertEqual(result, [a, b, c])

    def test_no_5000_cap_or_word_length_filter(self):
        upstream = [Abbreviation("cs", f"测试{i}", "cs", "wanxiang") for i in range(6001)]
        upstream.append(Abbreviation("ppt", "PowerPoint", "ppt", "wanxiang"))
        upstream.append(Abbreviation("cm", "柴米油盐酱醋茶", "cm", "wanxiang"))
        self.assertEqual(len(merge_pairs(upstream, [])), 6003)

    def test_strict_parse_and_zip_format(self):
        entries = list(parse_upstream("name: dict\n...\n# note\n有一说一\tyyuy\nPVP\tpvp\n"))
        self.assertEqual([e.shortcut for e in entries], ["yysy", "pvp"])
        with self.assertRaises(ValueError):
            list(parse_upstream("name: no_body\n"))
        with self.assertRaises(ValueError):
            list(parse_upstream("...\n坏数据\n"))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.zip"
            write_zip(path, entries)
            with ZipFile(path) as archive:
                self.assertEqual(archive.namelist(), ["dictionary.txt"])
                self.assertEqual(archive.read("dictionary.txt").decode("utf-8"),
                                 "# Gboard Dictionary version:1\nyysy\t有一说一\tzh-CN\npvp\tPVP\tzh-CN\n")


if __name__ == "__main__":
    unittest.main()
