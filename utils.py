from io import BytesIO

import pandas as pd


TEXT_COLUMNS = [
    "论文标题",
    "作者",
    "期刊年份",
    "研究主题",
    "研究现象",
    "核心问题",
    "核心机制",
    "创造的价值",
    "研究框架",
    "一句话概括",
    "核心逻辑链",
    "价值创造路径",
    "导师汇报表达",
    "我的思考问题",
    "关键词",
    "阅读状态",
    "重要程度",
    "备注",
]

DISPLAY_COLUMNS = [
    "id",
    "论文标题",
    "作者",
    "期刊年份",
    "研究主题",
    "关键词",
    "阅读状态",
    "重要程度",
]

READING_STATUSES = ["未开始", "泛读中", "精读中", "已读完", "已汇报"]
IMPORTANCE_LEVELS = ["低", "中", "高"]
DEFAULT_VALUES = {"阅读状态": "未开始", "重要程度": "中"}

RESEARCH_DIRECTIONS = [
    "数字化转型与价值创造",
    "财务数字化与管理控制",
    "数据资产与会计处理",
    "商业模式创新与绩效",
    "国企改革与价值创造",
    "ESG/碳披露与企业价值",
    "公司治理与利益输送",
]

DIRECTION_KEYWORDS = {
    "数据资产与会计处理": ["数据资产", "数据资源", "入表", "会计处理", "价值评估", "确权", "披露监管"],
    "财务数字化与管理控制": ["财务数字化", "财务共享", "共享服务", "管理控制", "成本管控", "成本管理", "控制杠杆", "数字控制耦合", "目标成本"],
    "公司治理与利益输送": ["利益输送", "大股东", "控股股东", "定向增发", "公司治理", "掏空", "广告攻势", "RIO"],
    "国企改革与价值创造": ["国有产权", "无偿划转", "国企改革", "国有资本", "央地重组", "中国宝武", "并购重组"],
    "ESG/碳披露与企业价值": ["碳信息", "碳披露", "双碳", "ESG", "低碳", "绿色", "企业社会责任"],
    "商业模式创新与绩效": ["商业模式", "财务绩效", "绩效", "酷特智能", "价值主张", "盈利模式"],
    "数字化转型与价值创造": ["数字化转型", "数字化能力", "工业互联网", "动态能力", "资源编排", "价值创造", "价值链", "平台价值"],
}


def clean_text(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def empty_paper():
    return {column: DEFAULT_VALUES.get(column, "") for column in TEXT_COLUMNS}


def normalize_import_dataframe(df):
    normalized = pd.DataFrame()
    for column in TEXT_COLUMNS:
        if column in df.columns:
            normalized[column] = df[column].map(clean_text)
        else:
            normalized[column] = DEFAULT_VALUES.get(column, "")

    for column, value in DEFAULT_VALUES.items():
        normalized[column] = normalized[column].replace("", value)

    normalized = normalized[normalized["论文标题"].astype(str).str.strip() != ""]
    return normalized.reset_index(drop=True)


def dataframe_to_excel_bytes(df):
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="论文数据库")
    buffer.seek(0)
    return buffer.getvalue()


def value_or_placeholder(paper, key, placeholder="未填写"):
    value = paper.get(key, "")
    if pd.isna(value) or str(value).strip() == "":
        return placeholder
    return str(value).strip()


def with_chinese_period(text):
    text = str(text).strip()
    return text if text.endswith(("。", "？", "！", "；")) else f"{text}。"


def classify_research_direction(paper):
    searchable_text = " ".join(
        value_or_placeholder(paper, key, "")
        for key in ["论文标题", "研究主题", "关键词", "研究现象", "核心问题", "核心机制", "创造的价值", "备注"]
    ).lower()

    best_direction = RESEARCH_DIRECTIONS[0]
    best_score = -1
    for direction in RESEARCH_DIRECTIONS:
        score = sum(1 for keyword in DIRECTION_KEYWORDS[direction] if keyword.lower() in searchable_text)
        if score > best_score:
            best_direction = direction
            best_score = score
    return best_direction


def generate_mentor_report(paper):
    phenomenon = value_or_placeholder(paper, "研究现象")
    question = value_or_placeholder(paper, "核心问题")
    mechanism = value_or_placeholder(paper, "核心机制")
    value = value_or_placeholder(paper, "创造的价值")
    reflection = value_or_placeholder(paper, "我的思考问题")

    sentences = [
        f"1. 我看的是一个什么现象：{with_chinese_period(phenomenon)}",
        f"2. 作者真正想解释什么问题：{with_chinese_period(question)}",
        f"3. 核心机制是什么：{with_chinese_period(mechanism)}",
        f"4. 最终创造了什么价值：{with_chinese_period(value)}",
        f"5. 我自己的疑问是什么：{with_chinese_period(reflection)}",
    ]

    return "\n\n".join(sentences)


def generate_report_card_markdown(paper):
    title = value_or_placeholder(paper, "论文标题", "未命名论文")
    author = value_or_placeholder(paper, "作者")
    journal_year = value_or_placeholder(paper, "期刊年份")
    topic = value_or_placeholder(paper, "研究主题")
    direction = classify_research_direction(paper)
    summary = value_or_placeholder(paper, "一句话概括")
    logic_chain = value_or_placeholder(paper, "核心逻辑链")
    value_path = value_or_placeholder(paper, "价值创造路径")
    report = generate_mentor_report(paper)

    return "\n".join(
        [
            f"## 导师汇报卡片｜{title}",
            "",
            f"**作者：** {author}",
            f"**期刊年份：** {journal_year}",
            f"**研究方向：** {direction}",
            f"**研究主题：** {topic}",
            "",
            "### 五句式汇报",
            report,
            "",
            "### 阅读抓手",
            f"- **一句话概括：** {summary}",
            f"- **核心逻辑链：** {logic_chain}",
            f"- **价值创造路径：** {value_path}",
        ]
    )
