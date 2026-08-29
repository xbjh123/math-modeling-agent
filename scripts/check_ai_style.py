#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_ai_style.py — 竞赛论文去 AI 味自检工具
===========================================
对齐 references/no_ai_style.md：
  - AI 痕迹词扫描（复用 no_ai_style.md §1 警惕词表）
  - 句长 CV 量化（§2.1，CV<0.25 偏 AI 味）
  - 术语一致自检（§2.2）

用法：
  python scripts/check_ai_style.py <目标.tex 或 目录> [--dt "术语1|术语2"]

示例：
  python scripts/check_ai_style.py .modeling/manuscript/sections/02_problem1.tex
  python scripts/check_ai_style.py .modeling/manuscript/sections/ --dt "类别覆盖|类别结构"

输出：
  命中清单（AI 痕迹词 + 出现次数 + 行号）、句长 CV、判定（PASS / AI-味偏重）。
"""

import sys
import os
import re
import math
from collections import Counter

# ---------------------------------------------------------------
# §1 警惕词表（对应 no_ai_style.md §1.1-1.3）
# 每项: (类别, 词/模式, 改写处方)
# ---------------------------------------------------------------
AI_PATTERNS = [
    # 1.1 表达类
    ("过度强调意义", r"至关重要|发挥了关键作用|凸显了重要性|反映了更广泛|标志着|关键转折点|至关重要", "删或弱化，改具体克制"),
    ("基于理论起笔", r"基于\S+理论|依据\S+理论|从\S+理论出发", "现象先行，理论名后移"),
    ("段末套路", r"由此(可见|得出)|综上所述|不难发现|从中可以看出|综上可见", "删，换自然过渡"),
    ("被动分析套话", r"该(处理|设计|方法)体现了|体现了\S+(思想|理念|价值|意义)", "改直接说明"),
    ("模板化问题陈述", r"面临的核心(问题|挑战)|核心挑战在于|首要任务是", "换具体表述"),
    ("抽象动词假深度", r"凸显了|彰显了|促进了|展示了|深刻揭示", "删或改明确动词"),
    ("推销广告化", r"充满活力|深刻的|开创性|堪称典范", "中性精确"),
    ("模糊归因", r"专家认为|研究表明|有观点认为|普遍认为", "删或改直接陈述"),
    ("公式化挑战展望", r"尽管面临挑战|未来展望|具有重要意义|为\S+提供新思路|任重道远", "删空泛升华"),
    # 1.2 语言类
    ("AI高频词:深刻揭示", r"深刻揭示", "说明/表明"),
    ("AI高频词:综合运用", r"综合运用", "结合使用"),
    ("AI高频词:不可或缺", r"不可或缺", "必要/关键"),
    ("系动词回避", r"作为\S+(的重要|的)(载体|角色|平台)|扮演着\S+的角色", "用「是/有」"),
    ("高度对称三组", r"首先[\s\S]*?其次[\s\S]*?再次", "打破"),
    ("否定式排比", r"不仅仅是\S+更是|不只是\S+而是|不只\S+更", "直接陈述"),
    ("虚假范围", r"从[^，。]+到[^，。]+(范围|领域|方面|层面)", "确保一致或具体"),

    # 1.3 风格类
    ("方括号标签标题", r"\[(?!H\])[一-龥A-Za-z]{2,10}\]", "改连贯段落，标签并入小标题"),
    ("填充短语", r"为了实现这一目标|值得注意的是|需要指出的是|不难发现两者之间|综上所述", "删冗余填充"),
    ("过度对冲", r"基本上|某种程度上|大体上|一定程度上", "删冗余限定（保留必要审慎）"),
    ("协作式沟通痕迹", r"希望有帮助|这里是一份|希望能帮到", "删"),
    ("知识截止免责", r"截至我的知识|作为AI|作为人工智能", "删"),
    ("谄媚语气", r"非常棒|精彩绝伦|令人钦佩", "删过度正面"),
]

# ---------------------------------------------------------------
# 句长 CV 计算
# ---------------------------------------------------------------
def extract_sentences(text):
    """按中文句末标点切句，返回句子列表（清空 AI 噪音后）。"""
    # 去掉 LaTeX 命令、注释行
    text = re.sub(r"%.*$", "", text, flags=re.M)          # 注释
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", "", text)  # 命令
    text = re.sub(r"[${}&_^~]", "", text)                  # 数学符号
    # 按 . ！ ？ ； 切句（中文语境）；保留句号结尾
    sents = re.split(r"[。！？；](?=[^。！？；]|$)", text)
    return [s.strip() for s in sents if len(s.strip()) > 0]


def sentence_lengths(sents):
    """每句字长（不含标点）。"""
    return [len(re.sub(r"[，。！？；：、（）()\s]", "", s)) for s in sents]


def cv_stats(lengths):
    """返回 (mean, std, cv)。均值为 0 时 cv=0。"""
    if not lengths:
        return 0.0, 0.0, 0.0
    n = len(lengths)
    mean = sum(lengths) / n
    if mean == 0:
        return 0.0, 0.0, 0.0
    var = sum((x - mean) ** 2 for x in lengths) / n
    std = math.sqrt(var)
    cv = std / mean
    return mean, std, cv


# ---------------------------------------------------------------
# 术语一致自检
# ---------------------------------------------------------------
def check_term_consistency(text, terms):
    """统计每个术语出现次数，若语义等价的高频词混用则提示。"""
    result = {}
    for term in terms:
        result[term] = len(re.findall(re.escape(term), text))
    return result


# ---------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------
def scan_ai(text):
    """扫描 AI 痕迹，返回 [(类别, 词, 次数, 处方)]。"""
    hits = []
    for cat, pat, fix in AI_PATTERNS:
        m = re.findall(pat, text)
        if m:
            hits.append((cat, m[0], len(m), fix))
    return hits


def scan_dash_density(text):
    """段落级破折号统计：某段内 中文破折号(——) 出现 >2 处才判滥用，单次合法不报。

    剔除标题行(\section/\subsection)与 LaTeX --- 命令，避免把标题破折号、'订货---供给'这类合法用法误报。
    """
    # 剔除标题行与 LaTeX 命令
    text = re.sub(r"\\subsection\*?\{[^}]*\}", "", text)
    text = re.sub(r"\\section\*?\{[^}]*\}", "", text)
    text = re.sub(r"\\[a-zA-Z]+\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})?", "", text)
    text = re.sub(r"[${}&_^~]", "", text)
    # 按空行分段
    paras = [x.strip() for x in re.split(r"\n\s*\n", text) if x.strip()]
    bad = []
    for para in paras:
        # 统计 —— 出现次数（单处合法，>2 才算滥用）
        cnt = len(re.findall(r"——", para))
        if cnt > 2:
            bad.append((para[:30], cnt))
    return bad
def strip_non_prose(text):
    """剔除绘图/表格/图环境内的代码，只保留正文 prose，避免 [arr]/[box]/[H] 被误判为标签。"""
    # 剔除 TikZ 环境（含 node/draw/arrow 定义）
    text = re.sub(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", r"\n", text, flags=re.S)
    # 剔除 figure/table 环境（保留 caption 文字，但去掉内部代码）
    text = re.sub(r"\\begin\{(figure|table)\}.*?\\end\{\1\}", r"\n", text, flags=re.S)
    return text


def process_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    text = strip_non_prose(text)
    return text


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    terms = []
    for a in sys.argv[1:]:
        if a.startswith("--dt"):
            terms = a.split("=")[1].split("|")

    target = args[0] if args else "."
    files = []
    if os.path.isdir(target):
        for root, _, fs in os.walk(target):
            for fn in fs:
                if fn.endswith(".tex"):
                    files.append(os.path.join(root, fn))
    else:
        files = [target]

    if not files:
        print("未找到 .tex 文件。")
        return 0

    all_text = ""
    for fp in files:
        all_text += process_file(fp) + "\n"

    print("=" * 60)
    print(f"扫描 {len(files)} 个文件")
    print("=" * 60)

    # 1) AI 痕迹扫描
    hits = scan_ai(all_text)
    if hits:
        print(f"\n[AI 痕迹] 命中 {len(hits)} 类")
        for cat, word, cnt, fix in sorted(hits, key=lambda x: -x[2]):
            print(f"  - {cat}  「{word}」 x{cnt}  → {fix}")
    else:
        print("\n[AI 痕迹] 未命中警惕词 ✓")

    # 1b) 段落级破折号滥用
    dashbad = scan_dash_density(all_text)
    if dashbad:
        print(f"\n[破折号] {len(dashbad)} 段内破折号>2处(疑似滥用), 段首: {[b[0] for b in dashbad[:3]]}")

    # 2) 句长 CV
    sents = extract_sentences(all_text)
    lengths = sentence_lengths(sents)
    mean, std, cv = cv_stats(lengths)
    print(f"\n[句长 CV] 句子数={len(lengths)} 平均长={mean:.1f}字 标准差={std:.1f}  CV={cv:.3f}")
    if len(lengths) > 0:
        if cv >= 0.30:
            print("  → 判定: PASS（长短句有起伏，无人为均匀感）")
        elif cv >= 0.25:
            print("  → 判定: 边缘（≥0.25，可接受，观察）")
        else:
            print("  → 判定: AI-味偏重（CV < 0.25，建议打散句式）")

    # 3) 术语一致
    if terms:
        counts = check_term_consistency(all_text, terms)
        print(f"\n[术语一致] {counts}")
        top = max(counts, key=counts.get) if counts else ""
        if len([v for v in counts.values() if v > 0]) > 1:
            print("  → 提示: 同概念可能多术语混用，核对是否需统一")

    # 4) 方括号标签专检
    bracket = re.findall(r"\[[^\]]{2,10}\]", all_text)
    if bracket:
        print(f"\n[方括号标签] {len(bracket)} 处 → 应改为连贯段落，标签并入小标题")

    print("\n" + "=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
