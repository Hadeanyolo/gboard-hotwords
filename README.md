# Gboard 中文补词库

为 Android Gboard 的中文（简体）拼音补充现代词汇、科技与游戏术语、网络表达和精选成语。无需 Root，每周从雾凇拼音更新原始数据并生成个人字典导入包。**这不是实时热搜榜，也不能替换 Gboard 的整句预测模型。**

## 下载

| 文件 | 用途 |
| --- | --- |
| [gboard_hotwords_test.zip](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/gboard_hotwords_test.zip) | 30 条测试词，先验证手机导入和候选效果 |
| [gboard_hotwords.zip](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/gboard_hotwords.zip) | 正式包，最多 5,000 条，包含测试词 |
| [words.tsv](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/words.tsv) | 本次全部词条、拼音、分类和来源 |
| [build-info.json](https://github.com/Hadeanyolo/gboard-hotwords/releases/download/latest/build-info.json) | 实际数量、构建时间、上游版本和校验值 |

[最新 Release](https://github.com/Hadeanyolo/gboard-hotwords/releases/tag/latest) · [构建状态](https://github.com/Hadeanyolo/gboard-hotwords/actions)

## 手机导入与测试

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

## 词条如何选择

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
```

输出在 `dist/`。Release 的 `gboard_sources.zip` 保留本次上游原文、项目脚本、选择规则和词条清单，可用于检查和复现；它**不是手机导入包**。要离线复现，可把 `upstream/cn_dicts/base.dict.yaml`、`ext.dict.yaml` 和 `upstream/LICENSE` 放到同一文件夹后运行：

```sh
python convert.py --upstream-dir /path/to/snapshot --ref 上游提交SHA
```

## 许可与来源

本项目以 GPL-3.0 发布。雾凇拼音词库来源于上游维护者及其收录的词库；保留上游许可和说明。生成文件是按本项目规则筛选、转换后的衍生词表，并非雾凇官方发布的 Gboard 版本。原文及对应许可保存在 `gboard_sources.zip`，Release 另附 `LICENSE`；详见上游词库头部的来源说明。
