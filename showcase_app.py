import pandas as pd
import streamlit as st

from database import get_all_papers
from utils import (
    RESEARCH_DIRECTIONS,
    classify_research_direction,
    generate_mentor_report,
    generate_report_card_markdown,
    value_or_placeholder,
)


APP_TITLE = "研0论文阅读数据库"
SHOWCASE_PAGES = ["展示首页", "研究方向", "论文展厅", "导师汇报卡片"]


st.set_page_config(page_title=f"{APP_TITLE}｜展示版", layout="wide")

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1120px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stText"] {
        line-height: 1.8;
    }
    .showcase-note {
        border-left: 4px solid #0f766e;
        padding: 0.5rem 0 0.5rem 1rem;
        margin: 0.5rem 0 1rem 0;
        background: #f8fafc;
    }
    .paper-card {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem 1.1rem;
        margin-bottom: 0.85rem;
        background: #ffffff;
    }
    .paper-card h4 {
        margin-top: 0;
        margin-bottom: 0.4rem;
        line-height: 1.45;
    }
    .paper-meta {
        color: #64748b;
        font-size: 0.92rem;
        line-height: 1.6;
        margin-bottom: 0.6rem;
    }
    .paper-section-title {
        color: #134e4a;
        font-weight: 700;
        margin-top: 0.7rem;
        margin-bottom: 0.25rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_showcase_data():
    df = get_all_papers()
    if df.empty:
        return df

    df = df.copy()
    df["研究方向"] = df.apply(lambda row: classify_research_direction(row.to_dict()), axis=1)
    return df


def build_paper_options(df):
    options = {}
    for _, paper in df.iterrows():
        label = f"{int(paper['id'])}｜{paper['论文标题']}｜{paper['期刊年份'] or '年份未填'}"
        options[label] = int(paper["id"])
    return options


def filter_papers(df, direction, keyword):
    filtered = df.copy()
    if direction != "全部":
        filtered = filtered[filtered["研究方向"] == direction]

    keyword = keyword.strip()
    if keyword:
        search_columns = ["论文标题", "作者", "研究主题", "关键词", "一句话概括"]
        mask = pd.Series(False, index=filtered.index)
        for column in search_columns:
            mask = mask | filtered[column].fillna("").str.contains(keyword, case=False, na=False)
        filtered = filtered[mask]

    return filtered.reset_index(drop=True)


def render_overview_metrics(df):
    total = len(df)
    direction_count = df["研究方向"].nunique() if not df.empty else 0
    high_count = int((df["重要程度"] == "高").sum()) if not df.empty else 0
    finished_count = int(df["阅读状态"].isin(["已读完", "已汇报"]).sum()) if not df.empty else 0

    cols = st.columns(4)
    cols[0].metric("论文总数", total)
    cols[1].metric("研究方向", direction_count)
    cols[2].metric("高重要程度", high_count)
    cols[3].metric("已完成阅读", finished_count)


def render_paper_card(paper, compact=False):
    title = value_or_placeholder(paper, "论文标题", "未命名论文")
    author = value_or_placeholder(paper, "作者")
    journal_year = value_or_placeholder(paper, "期刊年份")
    direction = value_or_placeholder(paper, "研究方向")
    topic = value_or_placeholder(paper, "研究主题")
    summary = value_or_placeholder(paper, "一句话概括")

    st.markdown(
        f"""
        <div class="paper-card">
            <h4>{title}</h4>
            <div class="paper-meta">{author}｜{journal_year}<br>{direction}｜{topic}</div>
            <div class="paper-section-title">一句话概括</div>
            <div>{summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if compact:
        return

    with st.expander("展开阅读卡片"):
        st.markdown(f"**研究现象：** {value_or_placeholder(paper, '研究现象')}")
        st.markdown(f"**核心问题：** {value_or_placeholder(paper, '核心问题')}")
        st.markdown(f"**核心机制：** {value_or_placeholder(paper, '核心机制')}")
        st.markdown(f"**创造的价值：** {value_or_placeholder(paper, '创造的价值')}")
        st.markdown(f"**我的思考问题：** {value_or_placeholder(paper, '我的思考问题')}")


def page_home(df):
    st.title(APP_TITLE)
    st.caption("会计学 / 财务管理方向研0论文阅读展示板")

    st.markdown(
        """
        <div class="showcase-note">
        这个展示版用于公开浏览论文阅读积累，重点呈现研究方向、核心问题、机制逻辑和导师汇报表达。
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df.empty:
        st.info("当前还没有论文记录。")
        return

    render_overview_metrics(df)

    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        st.markdown("#### 研究方向分布")
        direction_counts = df["研究方向"].value_counts().reindex(RESEARCH_DIRECTIONS, fill_value=0)
        st.bar_chart(direction_counts)

    with right:
        st.markdown("#### 重要程度分布")
        importance_counts = df["重要程度"].value_counts()
        st.bar_chart(importance_counts)

    st.markdown("#### 代表性论文")
    representative = df.sort_values(["重要程度", "id"], ascending=[True, False]).head(4)
    for _, paper in representative.iterrows():
        render_paper_card(paper, compact=True)


def page_directions(df):
    st.title("研究方向")

    if df.empty:
        st.info("当前还没有论文记录。")
        return

    direction_counts = df["研究方向"].value_counts().reindex(RESEARCH_DIRECTIONS, fill_value=0)
    st.bar_chart(direction_counts)

    for direction in RESEARCH_DIRECTIONS:
        papers = df[df["研究方向"] == direction]
        with st.expander(f"{direction}（{len(papers)}篇）", expanded=len(papers) > 0):
            if papers.empty:
                st.caption("暂无论文。")
                continue
            for _, paper in papers.iterrows():
                render_paper_card(paper, compact=True)


def page_gallery(df):
    st.title("论文展厅")

    if df.empty:
        st.info("当前还没有论文记录。")
        return

    cols = st.columns([1, 1.2])
    direction = cols[0].selectbox("研究方向", ["全部"] + RESEARCH_DIRECTIONS)
    keyword = cols[1].text_input("关键词检索", placeholder="输入标题、作者、主题或关键词")

    filtered = filter_papers(df, direction, keyword)
    st.caption(f"当前显示 {len(filtered)} 篇论文")

    for _, paper in filtered.iterrows():
        render_paper_card(paper)


def page_report_cards(df):
    st.title("导师汇报卡片")

    if df.empty:
        st.info("当前还没有论文记录。")
        return

    options = build_paper_options(df)
    chosen = st.selectbox("选择论文", list(options.keys()))
    paper_id = options[chosen]
    paper = df[df["id"] == paper_id].iloc[0].to_dict()

    st.markdown(f"#### {value_or_placeholder(paper, '论文标题', '未命名论文')}")
    st.caption(f"{value_or_placeholder(paper, '作者')}｜{value_or_placeholder(paper, '期刊年份')}")

    st.markdown("##### 五句式导师汇报")
    st.text_area("导师汇报表达", generate_mentor_report(paper), height=260, label_visibility="collapsed")

    st.markdown("##### Markdown 汇报卡片")
    markdown = generate_report_card_markdown(paper)
    st.text_area("Markdown 汇报卡片", markdown, height=320, label_visibility="collapsed")
    st.download_button(
        "下载 Markdown 卡片",
        data=markdown.encode("utf-8"),
        file_name=f"{value_or_placeholder(paper, '论文标题', '导师汇报卡片')}.md",
        mime="text/markdown",
    )


def main():
    df = load_showcase_data()
    st.sidebar.title(APP_TITLE)
    st.sidebar.caption("公开展示版")
    page = st.sidebar.radio("浏览导航", SHOWCASE_PAGES)

    if page == "展示首页":
        page_home(df)
    elif page == "研究方向":
        page_directions(df)
    elif page == "论文展厅":
        page_gallery(df)
    elif page == "导师汇报卡片":
        page_report_cards(df)


if __name__ == "__main__":
    main()
