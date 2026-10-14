#!/usr/bin/env python3
"""Build small, inspectable Gboard supplements. SPDX-License-Identifier: GPL-3.0-only."""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.error import URLError
from urllib.request import Request, urlopen
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
HEADER = "# Gboard Dictionary version:1"
MAX_WORDS = 5000
TEST_WORDS = 30
HAN = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]{3,6}\Z")
PINYIN = re.compile(r"[a-z]+(?: [a-z]+)*\Z")


@dataclass(frozen=True)
class Entry:
    word: str
    pinyin: str
    weight: int
    source: str
    category: str = ""


def fetch(url):
    for attempt in range(3):
        try:
            request = Request(url, headers={"User-Agent": "gboard-hotwords/1.0"})
            with urlopen(request, timeout=60) as response:
                return response.read()
        except (URLError, TimeoutError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def valid_pair(word, pinyin):
    # Rime uses v for ü; preserve nve/lve rather than silently changing readings.
    return bool(HAN.fullmatch(word) and PINYIN.fullmatch(pinyin)) and len(pinyin.split()) == len(word)


def parse_rime(text, source):
    in_body = False
    for line in text.splitlines():
        line = line.strip()
        if not in_body:
            if line == "...":
                in_body = True
            continue
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) < 2:
            continue
        word, pinyin = fields[0].strip(), " ".join(fields[1].lower().split())
        if not valid_pair(word, pinyin):
            continue
        weight = int(fields[2]) if len(fields) > 2 and fields[2].isdigit() else 0
        yield Entry(word, pinyin, weight, source)
    if not in_body:
        raise ValueError(f"{source}: missing YAML end marker")


def load_curated(path):
    result = []
    seen = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.startswith("#"):
            continue
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError(f"{path.name}:{number}: expected word, spaced pinyin, category")
        word, pinyin, category = fields
        if not valid_pair(word, pinyin) or not category or word in seen:
            raise ValueError(f"{path.name}:{number}: invalid or duplicate curated entry")
        seen.add(word)
        result.append(Entry(word, pinyin, 0, "curated", category))
    return result


def categorize(word, rules):
    for category, markers in rules["topics"].items():
        if any(marker in word for marker in markers):
            return category
    return ""


def select_entries(base, curated, rules, limit=MAX_WORDS):
    excluded = set(rules["exclude_words"])
    blocked = rules["exclude_fragments"]
    selected = []
    seen = set()
    shortcuts = Counter()

    def add(entry):
        shortcut = entry.pinyin.replace(" ", "")
        if entry.word in seen or entry.word in excluded or any(part in entry.word for part in blocked):
            return False
        if len(selected) >= limit or shortcuts[shortcut] >= 3:
            return False
        selected.append(entry)
        seen.add(entry.word)
        shortcuts[shortcut] += 1
        return True

    for entry in curated:
        if not add(entry):
            raise ValueError(f"Curated entry excluded or limit exceeded: {entry.word}")

    groups = defaultdict(list)
    for entry in base:
        if entry.weight < rules.get("min_upstream_weight", 1) or entry.word in seen:
            continue
        if any(entry.word.startswith(s) for s in rules.get("exclude_prefixes", [])):
            continue
        if any(entry.word.endswith(s) for s in rules.get("exclude_suffixes", [])):
            continue
        category = categorize(entry.word, rules)
        if category:
            groups[category].append(replace(entry, category=category))
    # Weight is an editorial hint, not measured hotness. Balance topics and avoid
    # alphabetic head slicing, especially ext's uniform weight of 100.
    for entries in groups.values():
        entries.sort(key=lambda e: (-e.weight, e.word, e.pinyin))
    iterators = [iter(groups[category]) for category in rules["topics"]]
    while iterators and len(selected) < limit:
        active = []
        for entries in iterators:
            for entry in entries:
                if add(entry):
                    active.append(entries)
                    break
        iterators = active
    return selected


def dictionary_text(entries):
    return HEADER + "\n" + "".join(f"{e.pinyin.replace(' ', '')}\t{e.word}\tzh-CN\n" for e in entries)


def write_dictionary(path, entries):
    if not entries or len(entries) > MAX_WORDS or len({e.word for e in entries}) != len(entries):
        raise ValueError("Empty, oversized or duplicate dictionary")
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("dictionary.txt", dictionary_text(entries).encode("utf-8"))
    with ZipFile(path) as archive:
        if archive.namelist() != ["dictionary.txt"] or archive.testzip() is not None:
            raise ValueError("Invalid import archive")
        if archive.read("dictionary.txt").decode("utf-8") != dictionary_text(entries):
            raise ValueError("Dictionary round-trip mismatch")


def build(output, upstream_dir=None, ref=None):
    rules = json.loads((ROOT / "selection.json").read_text(encoding="utf-8"))
    curated = load_curated(ROOT / "hotwords.tsv")
    output.mkdir(parents=True, exist_ok=True)
    snapshot = {}
    if upstream_dir:
        ref = ref or "local-snapshot"
        for name in ("base", "ext"):
            snapshot[f"cn_dicts/{name}.dict.yaml"] = (upstream_dir / f"{name}.dict.yaml").read_bytes()
        snapshot["LICENSE"] = (upstream_dir / "LICENSE").read_bytes()
    else:
        if ref is None:
            info = json.loads(fetch("https://api.github.com/repos/iDvel/rime-ice/git/ref/heads/main"))
            ref = info["object"]["sha"]
        if not re.fullmatch(r"[0-9a-f]{40}", ref):
            raise ValueError("Upstream ref must be a full commit SHA")
        for path in ("cn_dicts/base.dict.yaml", "cn_dicts/ext.dict.yaml", "LICENSE"):
            snapshot[path] = fetch(f"https://raw.githubusercontent.com/iDvel/rime-ice/{ref}/{path}")

    base = list(parse_rime(snapshot["cn_dicts/base.dict.yaml"].decode("utf-8-sig"), "base"))
    curated_words = {e.word for e in curated}
    readings = defaultdict(set)
    for name in ("base", "ext"):
        for entry in parse_rime(snapshot[f"cn_dicts/{name}.dict.yaml"].decode("utf-8-sig"), name):
            if entry.word in curated_words:
                readings[entry.word].add(entry.pinyin)
    # Keep explicit curated readings; ext helps audit them, never supplies a
    # supposedly high-frequency alphabetic slice. New curated words need review.
    unmatched = [e.word for e in curated if e.pinyin not in readings[e.word]]
    selected = select_entries(base, curated, rules)
    if len(selected) < len(curated) or len(base) < 1000:
        raise ValueError("Upstream dictionary unexpectedly small")
    test = curated[:TEST_WORDS]
    write_dictionary(output / "gboard_hotwords.zip", selected)
    write_dictionary(output / "gboard_hotwords_test.zip", test)
    words = "word\tpinyin\tcategory\tsource\tupstream_weight\n" + "".join(
        f"{e.word}\t{e.pinyin}\t{e.category}\t{e.source}\t{e.weight}\n" for e in selected
    )
    (output / "words.tsv").write_text(words, encoding="utf-8")
    info = {
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "upstream_repository": "iDvel/rime-ice", "upstream_commit": ref,
        "full_count": len(selected), "test_count": len(test), "max_count": MAX_WORDS,
        "categories": dict(Counter(e.category for e in selected)),
        "sources": dict(Counter(e.source for e in selected)),
        "curated_readings_not_found_upstream": unmatched,
        "upstream_sha256": {path: hashlib.sha256(data).hexdigest() for path, data in snapshot.items()},
        "zip_sha256": {name: hashlib.sha256((output / name).read_bytes()).hexdigest()
                       for name in ("gboard_hotwords.zip", "gboard_hotwords_test.zip")},
        "limitation": "Topic-filtered supplement; not real-time trending statistics or a Gboard language model.",
    }
    (output / "build-info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "LICENSE").write_bytes(snapshot["LICENSE"])
    with ZipFile(output / "gboard_sources.zip", "w", compression=ZIP_DEFLATED) as archive:
        for path, data in snapshot.items():
            archive.writestr(f"upstream/{path}", data)
        for path in ("convert.py", "hotwords.tsv", "selection.json", "README.md", "LICENSE", "test_convert.py", ".github/workflows/build.yml"):
            archive.write(ROOT / path, f"project/{path}")
        for path in ("words.tsv", "build-info.json"):
            archive.write(output / path, path)
    notes = (
        f"中文全拼补词包，构建时间：{info['built_at_utc']}。\n\n"
        f"- 正式包：**{len(selected)} 条**；测试包：**{len(test)} 条**。\n"
        "- 先导入测试包验证，再按需导入正式包；ZIP 不要解压。\n"
        "- 两个包存在重叠；正式包包含测试词。导入前导出备份，先删除测试词以免重复导入。\n"
        "- 每周更新的是下载包；手机需要手动导入，不保证自动去重或替换旧词。\n"
        "- 个人词典补词不能移植整句预测模型；5000 条是上限，不是性能保证。\n"
        f"- 雾凇快照：[`{ref}`](https://github.com/iDvel/rime-ice/tree/{ref})。\n"
        "- 词条清单见 `words.tsv`，复现与上游原文见 `gboard_sources.zip`，许可见 `LICENSE`。\n"
    )
    (output / "release-notes.md").write_text(notes, encoding="utf-8")
    print(json.dumps({"full_count": len(selected), "test_count": len(test), "categories": info["categories"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--upstream-dir", type=Path, help="Local snapshot folder with base/ext.dict.yaml and LICENSE")
    parser.add_argument("--ref", help="Pin upstream commit SHA")
    args = parser.parse_args()
    build(args.output_dir, args.upstream_dir, args.ref)
