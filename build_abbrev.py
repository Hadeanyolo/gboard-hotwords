#!/usr/bin/env python3
"""Convert all Wanxiang abbreviation pairs to Gboard. SPDX-License-Identifier: GPL-3.0-only."""

import argparse
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from zipfile import ZIP_DEFLATED, ZipFile

from convert import ROOT, HEADER, fetch

UPSTREAM = "amzxyz/rime-wanxiang"
BRANCH = "wanxiang"
DICT_PATH = "dicts/abbrev.dict.yaml"
HAN_WORD = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff〇]+\Z")
CHINESE_INITIALS = str.maketrans({"u": "s", "i": "c", "v": "z"})
TEST_PAIRS = [("nsdd", "你说的对"), ("xswl", "笑死我了"),
              ("yysy", "有一说一"), ("qswl", "千丝万缕"), ("qswl", "千思万虑")]


@dataclass(frozen=True)
class Abbreviation:
    shortcut: str
    word: str
    original_code: str
    source: str


def check_word(word):
    if not word or any(ord(c) < 32 or ord(c) == 127 for c in word):
        raise ValueError(f"Invalid word: {word!r}")


def normalize_code(word, code):
    # The upstream Chinese abbreviation table uses u/i/v for sh/ch/zh.
    # These are abbreviation conventions, not the ü notation of full pinyin.
    # English and mixed words (PVP, SKU, H股, AA制) retain their original codes.
    if HAN_WORD.fullmatch(word):
        code = "".join(c for c in unicodedata.normalize("NFKD", code)
                       if not unicodedata.combining(c)).translate(CHINESE_INITIALS)
    if not re.fullmatch(r"[a-z]+", code):
        raise ValueError(f"Unsupported upstream shortcut {code!r} for {word!r}")
    return code


def parse_upstream(text):
    in_body = False
    for number, line in enumerate(text.splitlines(), 1):
        if not in_body:
            if line.strip() == "...":
                in_body = True
            continue
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 2:
            raise ValueError(f"Upstream line {number}: missing code column")
        word, code = fields[0].strip(), fields[1].strip()
        check_word(word)
        yield Abbreviation(normalize_code(word, code), word, code, "wanxiang")
    if not in_body:
        raise ValueError("Upstream dictionary missing YAML end marker")


def load_additions(path):
    entries = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 2 or not re.fullmatch(r"[a-z]+", fields[0]):
            raise ValueError(f"{path.name}:{number}: expected shortcut<Tab>word")
        shortcut, word = fields
        check_word(word)
        entries.append(Abbreviation(shortcut, word, shortcut, "local-addition"))
    return entries


def merge_pairs(upstream, additions):
    # Deduplicate only identical normalized shortcut+word pairs. Never collapse
    # all words with one shortcut, or all shortcuts pointing to the same word.
    result = []
    seen = set()
    for entry in [*additions, *upstream]:
        pair = (entry.shortcut, entry.word)
        if pair not in seen:
            seen.add(pair)
            result.append(entry)
    return result


def write_zip(path, entries):
    if not entries:
        raise ValueError("Cannot publish empty abbreviation dictionary")
    text = HEADER + "\n" + "".join(f"{e.shortcut}\t{e.word}\tzh-CN\n" for e in entries)
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("dictionary.txt", text.encode("utf-8"))
    with ZipFile(path) as archive:
        if archive.namelist() != ["dictionary.txt"] or archive.testzip() is not None:
            raise ValueError("Invalid abbreviation ZIP")
        if archive.read("dictionary.txt").decode("utf-8") != text:
            raise ValueError("Abbreviation ZIP round-trip mismatch")


def build(output, upstream_dir=None, ref=None):
    if upstream_dir:
        ref = ref or "local-snapshot"
        snapshot = {DICT_PATH: (upstream_dir / "abbrev.dict.yaml").read_bytes(),
                    "LICENSE": (upstream_dir / "LICENSE").read_bytes()}
    else:
        if ref is None:
            metadata = json.loads(fetch(f"https://api.github.com/repos/{UPSTREAM}/git/ref/heads/{BRANCH}"))
            ref = metadata["object"]["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError("Upstream ref must be a full commit SHA")
        snapshot = {path: fetch(f"https://raw.githubusercontent.com/{UPSTREAM}/{ref}/{path}")
                    for path in (DICT_PATH, "LICENSE")}
    upstream = list(parse_upstream(snapshot[DICT_PATH].decode("utf-8-sig")))
    if not upstream:
        raise ValueError("Empty upstream abbreviation table")
    additions = load_additions(ROOT / "abbrev-additions.tsv")
    entries = merge_pairs(upstream, additions)
    lookup = {(e.shortcut, e.word): e for e in entries}
    # Check the published test examples against the actual full package.
    test = [lookup[pair] for pair in TEST_PAIRS]
    assert {e.word for e in upstream} <= {e.word for e in entries}
    output.mkdir(parents=True, exist_ok=True)
    write_zip(output / "gboard_abbrev.zip", entries)
    write_zip(output / "gboard_abbrev_test.zip", test)
    words = "shortcut\tword\toriginal_code\tsource\n" + "".join(
        f"{e.shortcut}\t{e.word}\t{e.original_code}\t{e.source}\n" for e in entries)
    (output / "abbrev-words.tsv").write_text(words, encoding="utf-8")
    collision_counts = Counter(e.shortcut for e in entries)
    info = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "upstream_repository": UPSTREAM, "upstream_commit": ref, "upstream_path": DICT_PATH,
        "upstream_row_count": len(upstream), "local_addition_count": len(additions),
        "full_pair_count": len(entries), "test_pair_count": len(test),
        "exact_duplicate_pairs_removed": len(upstream) + len(additions) - len(entries),
        "distinct_word_count": len({e.word for e in entries}),
        "distinct_shortcut_count": len(collision_counts),
        "shortcuts_with_multiple_candidates": sum(n > 1 for n in collision_counts.values()),
        "max_candidates_for_one_shortcut": max(collision_counts.values()),
        "normalization": "For Chinese words only: u->s, i->c, v->z; remove accent marks. English/mixed codes unchanged.",
        "filtering": "None; only exact normalized shortcut+word duplicates removed. No size or collision cap.",
        "upstream_sha256": {path: hashlib.sha256(data).hexdigest() for path, data in snapshot.items()},
        "zip_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                       for name in ("gboard_abbrev.zip", "gboard_abbrev_test.zip")},
    }
    (output / "abbrev-build-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "WANXIANG-LICENSE").write_bytes(snapshot["LICENSE"])
    attribution = (
        f"万象简码库 Gboard 转换版；原作者及维护者：amzxyz 与万象拼音贡献者。\n"
        f"原始仓库：https://github.com/{UPSTREAM}\n"
        f"原始词表：https://github.com/{UPSTREAM}/blob/{ref}/{DICT_PATH}\n"
        "词表许可：CC BY 4.0 https://creativecommons.org/licenses/by/4.0/\n"
        "修改：中文简码转换为普通首字母，完全重复映射去重，添加 abbrev-additions.tsv 中的快捷短语，转换为 Gboard 格式。\n"
        "英文和混合词保留原码。非万象官方发布的 Gboard 版本，候选顺序与手机兼容性不作保证。\n"
        "转换脚本：GPL-3.0，见项目 LICENSE。完整上游原文及许可在此源文件包内。\n"
    )
    with ZipFile(output / "gboard_abbrev_sources.zip", "w", compression=ZIP_DEFLATED) as archive:
        for path, data in snapshot.items():
            archive.writestr(f"upstream/{path}", data)
        for path in ("build_abbrev.py", "convert.py", "abbrev-additions.tsv", "test_abbrev.py", "README.md", "LICENSE", ".github/workflows/build.yml"):
            archive.write(ROOT / path, f"project/{path}")
        for path in ("abbrev-words.tsv", "abbrev-build-info.json"):
            archive.write(output / path, path)
        archive.writestr("ATTRIBUTION.txt", attribution)
    notes = (
        f"## 中文简拼快捷词库（全量）\n\n构建时间：{info['built_at_utc']}。\n\n"
        f"- 正式包 `gboard_abbrev.zip`：**{len(entries)} 条快捷码映射**；不按数量、词长、主题或重码数筛选。\n"
        f"- 上游 {len(upstream)} 条，补充 {len(additions)} 条，转换后去除 {info['exact_duplicate_pairs_removed']} 条完全重复映射。\n"
        f"- 测试包 `gboard_abbrev_test.zip`：**{len(test)} 条**；正式包包含全部测试词，不必重复导入。\n"
        "- 验证：`nsdd` → 你说的对；`xswl` → 笑死我了；`yysy` → 有一说一。\n"
        "- `qswl` 保留千丝万缕、千思万虑。同码候选全部保留，不保证置顶，也不能移植 Rime 的预测引擎。\n"
        "- 手机请先导出备份，ZIP 不要解压；已有全拼包无需删除，两个包使用不同快捷码。\n"
        "- 文件大小不能代表手机运行性能；全量导入速度、候选显示和重复导入行为需要实测。\n"
        f"- 来源：[万象简码库](https://github.com/{UPSTREAM}/blob/{ref}/{DICT_PATH})，作者 amzxyz 与贡献者，CC BY 4.0。\n"
        "- 本项目转换版：中文 u/i/v → s/c/z，保留英文及混合词原码；原文、许可与修改说明见 `gboard_abbrev_sources.zip` 和 `WANXIANG-LICENSE`。\n"
        "- 查看映射清单：`abbrev-words.tsv`；版本、数量和校验值：`abbrev-build-info.json`。\n\n"
    )
    notes_path = output / "release-notes.md"
    existing_notes = notes_path.read_text(encoding="utf-8") if notes_path.exists() else ""
    if existing_notes.startswith("## 中文简拼"):
        existing_notes = ""
    notes_path.write_text(notes + "## 全拼补词包\n\n" + existing_notes, encoding="utf-8")
    print(json.dumps({k: info[k] for k in ("upstream_row_count", "full_pair_count", "test_pair_count", "exact_duplicate_pairs_removed", "shortcuts_with_multiple_candidates", "max_candidates_for_one_shortcut")}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--upstream-dir", type=Path, help="Folder containing abbrev.dict.yaml and LICENSE")
    parser.add_argument("--ref", help="Pinned Wanxiang commit SHA")
    args = parser.parse_args()
    build(args.output_dir, args.upstream_dir, args.ref)
