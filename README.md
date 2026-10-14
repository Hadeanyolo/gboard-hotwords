# Gboard 中文简拼与补词库

为 Android Gboard 提供两种个人字典包：**万象全量简拼快捷码包**（如 `nsdd` → 你说的对）和**雾凇全拼补词包**。无需 Root，每周自动更新下载文件，手机端手动导入。**这是快捷码和词条映射，不能替换 Gboard 的整句预测模型，也不能保证特定词置顶。**

## 下载

| 文件 | 用途 |
| --- | --- |
| [gboard_abbrev.zip](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/gboard_abbrev.zip) | **全量简拼包**，约 3.4 万条映射，无数量和候选上限 |
| [gboard_abbrev_test.zip](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/gboard_abbrev_test.zip) | 5 条简拼验证映射，正式简拼包包含这些条目 |
| [abbrev-words.tsv](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/abbrev-words.tsv) | 全部简拼映射及转换前编码 |
| [abbrev-build-info.json](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/abbrev-build-info.json) | 简拼实际数量、版本、去重和重码统计 |
| [gboard_hotwords_test.zip](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/gboard_hotwords_test.zip) | 30 条测试词，先验证手机导入和候选效果 |
| [gboard_hotwords.zip](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/gboard_hotwords.zip) | 正式包，最多 5,000 条，包含测试词 |
| [words.tsv](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/words.tsv) | 本次全部词条、拼音、分类和来源 |
| [build-info.json](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/build-info.json) | 实际数量、构建时间、上游版本和校验值 |

[最新 Release](https://github.com/Hadeanyolo/gboard-hotwords/releases/tag/latest) · [构建状态](https://github.com/Hadeanyolo/gboard-hotwords/actions)

## 简拼包：导入与验证

1. 在 Gboard 设置 → 字典 → 个人字典 → 中文（简体）→ 右上角菜单，先**导出备份**。
2. 下载 `gboard_abbrev.zip`，**不要解压**，在同一菜单选择**导入**。已有全拼补词包不必删除。
3. 切到中文（简体）全键盘，输入 `nsdd`、`xswl`、`yysy`，检查候选栏是否出现下表短语。请先确认对应“词语 + 快捷码”已在个人字典中。

| 输入快捷码 | 目标候选 |
| --- | --- |
| `nsdd` | 你说的对 |
| `xswl` | 笑死我了 |
| `yysy` | 有一说一 |
| `qswl` | 千丝万缕、千思万虑 |

不要求排第一位。原生词库也可能已有某些简拼候选；要验证具体导入条目，可在备份后手动删除、重新添加该条“词语 + 快捷码”，对比候选结果。不要清除 Gboard 全部数据。

如果想先试小包，导入 `gboard_abbrev_test.zip` 即可；完整包包含同样的 5 条映射，不要重复导入，切换前可删除这 5 条测试映射。已经直接导入完整包，就不必再导入测试包。

**约 3.4 万条不代表已验证不卡顿**；导入速度、设置列表响应、同码多候选和具体手机版本的快捷码支持，需要你的手机实测。如果快捷码出不来，请告知 Gboard 版本、键盘布局，以及个人字典中是否能找到对应条目。

### 简拼来源和转换规则

- 全量来源：[amzxyz/rime-wanxiang 的简码词表](https://github.com/amzxyz/rime-wanxiang/blob/wanxiang/dicts/abbrev.dict.yaml)。每次固定上游提交，保留完整原文与许可。
- **不按数量、主题、词长、词频或同码候选数筛选**。普通词、成语、较长短语、英文和混合词全部保留。
- 中文简码使用万象的声母约定 `u/i/v`（sh/ch/zh），本项目转换为常用首字母 `s/c/z`；例如 `yyuy` → `yysy`。带声调的 `ǹ` 去调为 `n`。
- 英文和含英文字母的混合词保留原始快捷码，避免将 `PVP` 的 `pvp` 错改为 `pzp`。这里的 `u/i/v` 转换只适用于此简码表，不适用于全拼词库。
- **只去除完全相同的“转换后快捷码 + 词语”重复映射**，保留同码不同词、同词不同码。Gboard 决定候选顺序；文件顺序并不等于置顶设置。
- [abbrev-additions.tsv](abbrev-additions.tsv) 补充 `nsdd` → 你说的对，新增条目不会删除上游同码候选。整张码表不是仅限网络聊天的缩写清单。
- 简拼数据来自万象（amzxyz 与贡献者），采用 **CC BY 4.0**；转换和去重后的数据是本项目转换版，并非万象官方的 Gboard 包。许可、原始词表、修改说明和复现脚本在 `gboard_abbrev_sources.zip`，Release 另附 `WANXIANG-LICENSE`。

## 手机导入与测试

以下是原有**全拼补词包**的说明。它和简拼包独立，不要求同时导入。

1. 在 Gboard 设置 → 字典 → 个人字典 → 中文（简体）→ 右上角菜单，先**导出**现有字典备份。
2. 下载测试包，**不要解压**。
3. 在同一菜单选择**导入**，选择 `gboard_hotwords_test.zip`。不同版本的菜单名称可能略有差异。
4. 切到中文（简体）的全拼键盘，输入下面的完整拼音，检查候选栏是否出现目标词。词典列表能看到词条，仅说明导入成功，候选效果需要另外验证。

| 输入 | 目标候选 |
| --- | --- |
| `tishicizhuru` | 提示词注入 |
| `moxinghuanjue` | 模型幻觉 |
| `shangxiawenchuangkou` | 上下文窗口 |
| `xiancunyichu` | 显存溢出 |
| `saibodagongren` | 赛博打工人 |
| `dianzizhacai` | 电子榨菜 |

5. 测试通过且输入流畅后，再使用正式包。**正式包包含测试词；先删除测试导入的 30 条，再导入正式包，避免重复。** 不要通过清除 Gboard 全部数据来删测试词。

如果导入失败，或词典里有词却无法用全拼打出，请提供 Gboard 版本、键盘布局和测试结果。构建成功不能证明你的手机版本兼容。5,000 条只是当前上限，并不是不会卡顿的保证。

**每周只更新下载包，手机不会自动同步。** Gboard 重复导入时是否去重、是否覆盖旧词，尚未在你的设备上验证；不要每周反复导入整个包。已有常用词也无法从公开数据中准确判断，当前过滤只能减少重复，无法保证全部是手机缺失的词。

## 全拼补词包的词条如何选择

- 来源：[iDvel/rime-ice](https://github.com/iDvel/rime-ice) 的 `cn_dicts/base.dict.yaml`、`cn_dicts/ext.dict.yaml`，以及本项目维护的 [hotwords.tsv](hotwords.tsv)。
- 优先收录 `hotwords.tsv`：写明读音，覆盖科技、网络表达、现代生活、游戏与创作、成语短语。它是可维护的补充清单，不是自动抓取的实时热点。
- 批量词条只选带明确注音的 `base`，按 [selection.json](selection.json) 的主题关键词筛选，再参考上游权重并平衡主题。上游权重是候选排序提示，**不是实测热度**；不能直接截取文件前几千行。
- `ext` 用于检查精选词读音；其权重基本统一，不能据此挑出所谓高频词，不批量导入其字母顺序切片。
- 只收录 3～6 字的纯汉字词条、一字一音节的明确拼音；排除基础日常词、明显不相关的词和常见句子片段，词语去重。批量候选的上游权重至少为 500；此阈值只是降噪规则，不代表真实词频。完整拼音最多对应 3 个词，控制同音候选拥挤。
- 仅建立完整拼音快捷码，不批量创建简拼。拼音里的 `v` 表示 ü，例如 `lv`；以手机实测是否匹配为准。
- 不使用无注音的 `tencent.dict.yaml`，也不自动给多音词猜读音。Python 标准库已经够用，无需安装 `pypinyin`。

新增词可编辑 `hotwords.tsv`：`词语<Tab>分音节拼音<Tab>分类`。修改排除词或主题范围可编辑 `selection.json`。**仓库公开，请勿添加私人姓名、地址、账号或密钥。**

## 自动更新与复现

`push` 到 `main`、手动运行 Actions，或每周一 UTC 02:00（北京时间周一 10:00）会构建并覆盖 `latest` Release 的同名附件。定时任务可能延迟；长期无仓库活动时，GitHub 可能暂停公开仓库的定时工作流，可在 Actions 中重新启用。

每次构建固定一个上游提交，获取完整 `base`、`ext` 和许可；源文件缺失、格式异常或精选词非法时失败，避免发布空包。两个导入 ZIP 内均只有 UTF-8 的 `dictionary.txt`，第一行是 `# Gboard Dictionary version:1`，后续为 `全拼快捷码<Tab>词语<Tab>zh-CN`。

```sh
python -m unittest -v
python convert.py
python build_abbrev.py
```

输出在 `dist/`。Release 的 `gboard_sources.zip` 保留本次上游原文、项目脚本、选择规则和词条清单，可用于检查和复现；它**不是手机导入包**。要离线复现，可把 `upstream/cn_dicts/base.dict.yaml`、`ext.dict.yaml` 和 `upstream/LICENSE` 放到同一文件夹后运行：

```sh
python convert.py --upstream-dir /path/to/snapshot --ref 上游提交SHA
```

简拼包也可单独运行 `python build_abbrev.py`。离线复现时，把源文件包内的 `upstream/dicts/abbrev.dict.yaml` 与 `upstream/LICENSE` 放到同一文件夹，再运行：

```sh
python build_abbrev.py --upstream-dir /path/to/wanxiang-snapshot --ref 上游提交SHA
```

## 许可与来源

转换脚本以 GPL-3.0 发布。雾凇全拼补词包保留其上游 GPL-3.0 许可与来源说明，原文在 `gboard_sources.zip`，Release 另附 `LICENSE`。**万象简拼数据保留 CC BY 4.0 许可**，原文、作者归属、转换说明在 `gboard_abbrev_sources.zip`，Release 另附 `WANXIANG-LICENSE`。两者都是本项目转换版，非上游官方的 Gboard 版本。
