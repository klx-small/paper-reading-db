from pathlib import Path

import pandas as pd
import streamlit as st

from database import (
    add_paper,
    delete_paper,
    get_all_papers,
    get_paper,
    import_papers_from_dataframe,
    init_db,
    search_papers,
    update_paper,
)
from utils import (
    DISPLAY_COLUMNS,
    IMPORTANCE_LEVELS,
    READING_STATUSES,
    RESEARCH_DIRECTIONS,
    TEXT_COLUMNS,
    classify_research_direction,
    dataframe_to_excel_bytes,
    empty_paper,
    generate_mentor_report,
    generate_report_card_markdown,
    normalize_import_dataframe,
    value_or_placeholder,
)


APP_TITLE = "研0论文阅读数据库"
BASE_DIR = Path(__file__).resolve().parent
PAGES = ["首页仪表盘", "论文数据库", "论文详情", "新增/编辑论文", "导师汇报生成", "研究方向聚类", "导入导出"]


st.set_page_config(page_title=APP_TITLE, layout="wide")
init_db()

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stMarkdownContainer"] p,
    div[data-testid="stText"] {
        line-height: 1.75;
    }
    .paper-read-block {
        border-left: 4px solid #0f766e;
        padding: 0.35rem 0 0.35rem 1rem;
        margin: 0.45rem 0 1rem 0;
        background: #f8fafc;
    }
    .paper-read-block strong {
        color: #134e4a;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def initialize_state():
    if "selected_paper_id" not in st.session_state:
        st.session_state.selected_paper_id = None
    if "current_page" not in st.session_state:
        st.session_state.current_page = PAGES[0]


def select_index(options, value, default=0):
    if value in options:
        return options.index(value)
    return default


def get_paper_options(df):
    options = {}
    for _, row in df.iterrows():
        title = row.get("论文标题") or "未命名论文"
        year = row.get("期刊年份") or "年份未填"
        options[f"{int(row['id'])} | {title} | {year}"] = int(row["id"])
    return options


def choose_paper(label, df):
    if df.empty:
        st.info("当前还没有论文记录。")
        return None

    options = get_paper_options(df)
    default_id = st.session_state.get("selected_paper_id")
    labels = list(options.keys())
    default_index = 0
    if default_id in options.values():
        default_index = list(options.values()).index(default_id)

    chosen_label = st.selectbox(label, labels, index=default_index)
    paper_id = options[chosen_label]
    st.session_state.selected_paper_id = paper_id
    return get_paper(paper_id)


def filter_dataframe(df, topic, keyword, status):
    return search_papers(
        topic="" if topic == "全部" else topic,
        keyword=keyword.strip(),
        status="" if status == "全部" else status,
    )


def render_field(label, value):
    content = value_or_placeholder(value, label)
    st.markdown(
        f'<div class="paper-read-block"><strong>{label}</strong><br>{content}</div>',
        unsafe_allow_html=True,
    )


def render_report_markdown_box(paper, key_prefix):
    markdown = generate_report_card_markdown(paper)
    st.text_area(
        "Markdown 汇报卡片（可直接全选复制）",
        value=markdown,
        height=360,
        key=f"{key_prefix}_markdown_card",
    )
    st.download_button(
        "下载 Markdown 卡片",
        data=markdown.encode("utf-8-sig"),
        file_name=f"{value_or_placeholder(paper, '论文标题', '导师汇报卡片')}.md",
        mime="text/markdown",
        key=f"{key_prefix}_download_markdown",
    )


def render_report_card(paper, key_prefix="report_card"):
    direction = classify_research_direction(paper)
    report = generate_mentor_report(paper)
    st.markdown("#### 导师汇报卡片")
    st.caption(f"研究方向：{direction}")
    st.markdown(report.replace("\n", "\n\n"))
    with st.expander("复制为 Markdown", expanded=False):
        render_report_markdown_box(paper, key_prefix)


def render_paper_card(paper):
    if not paper:
        st.info("请选择一篇论文。")
        return

    st.subheader(paper.get("论文标题") or "未命名论文")
    meta_cols = st.columns(4)
    meta_cols[0].metric("作者", value_or_placeholder(paper, "作者"))
    meta_cols[1].metric("期刊年份", value_or_placeholder(paper, "期刊年份"))
    meta_cols[2].metric("阅读状态", value_or_placeholder(paper, "阅读状态"))
    meta_cols[3].metric("重要程度", value_or_placeholder(paper, "重要程度"))
    st.caption(f"研究方向：{classify_research_direction(paper)}")

    st.divider()

    render_report_card(paper, key_prefix=f"detail_{paper.get('id', 'new')}")

    tab_position, tab_logic, tab_value = st.tabs(["研究定位", "核心逻辑", "价值与思考"])
    with tab_position:
        for label in ["研究主题", "关键词", "研究现象", "一句话概括"]:
            render_field(label, paper)

    with tab_logic:
        for label in ["核心问题", "核心机制", "核心逻辑链", "研究框架"]:
            render_field(label, paper)

    with tab_value:
        for label in ["创造的价值", "价值创造路径", "我的思考问题", "导师汇报表达", "备注"]:
            render_field(label, paper)


def paper_form(defaults, form_key, submit_label):
    data = empty_paper()
    data.update({key: defaults.get(key, "") for key in TEXT_COLUMNS})

    with st.form(form_key):
        st.markdown("#### 基本信息")
        col1, col2 = st.columns(2)
        data["论文标题"] = col1.text_input("论文标题", value=data["论文标题"])
        data["作者"] = col2.text_input("作者", value=data["作者"])

        col3, col4 = st.columns(2)
        data["期刊年份"] = col3.text_input("期刊年份", value=data["期刊年份"], placeholder="例如：会计研究 2024")
        data["研究主题"] = col4.text_input("研究主题", value=data["研究主题"], placeholder="例如：数字化转型")

        col5, col6, col7 = st.columns(3)
        data["关键词"] = col5.text_input("关键词", value=data["关键词"], placeholder="用分号或逗号分隔")
        data["阅读状态"] = col6.selectbox(
            "阅读状态",
            READING_STATUSES,
            index=select_index(READING_STATUSES, data["阅读状态"]),
        )
        data["重要程度"] = col7.selectbox(
            "重要程度",
            IMPORTANCE_LEVELS,
            index=select_index(IMPORTANCE_LEVELS, data["重要程度"], default=1),
        )

        st.markdown("#### 阅读卡片")
        left, right = st.columns(2)
        with left:
            data["研究现象"] = st.text_area("研究现象", value=data["研究现象"], height=100)
            data["核心问题"] = st.text_area("核心问题", value=data["核心问题"], height=100)
            data["核心机制"] = st.text_area("核心机制", value=data["核心机制"], height=100)
            data["创造的价值"] = st.text_area("创造的价值", value=data["创造的价值"], height=100)
            data["一句话概括"] = st.text_area("一句话概括", value=data["一句话概括"], height=80)
        with right:
            data["研究框架"] = st.text_area("研究框架", value=data["研究框架"], height=100)
            data["核心逻辑链"] = st.text_area("核心逻辑链", value=data["核心逻辑链"], height=100)
            data["价值创造路径"] = st.text_area("价值创造路径", value=data["价值创造路径"], height=100)
            data["我的思考问题"] = st.text_area("我的思考问题", value=data["我的思考问题"], height=100)
            data["备注"] = st.text_area("备注", value=data["备注"], height=80)

        data["导师汇报表达"] = st.text_area("导师汇报表达", value=data["导师汇报表达"], height=120)
        submitted = st.form_submit_button(submit_label, type="primary")

    return submitted, data


def page_dashboard():
    st.title(APP_TITLE)
    df = get_all_papers()

    total = len(df)
    completed = int(df["阅读状态"].isin(["已读完", "已汇报"]).sum()) if not df.empty else 0
    theme_count = int(df["研究主题"].replace("", pd.NA).dropna().nunique()) if not df.empty else 0
    high_count = int((df["重要程度"] == "高").sum()) if not df.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("论文数量", total)
    col2.metric("已读完/已汇报", completed)
    col3.metric("主题数量", theme_count)
    col4.metric("高重要程度", high_count)

    if df.empty:
        st.info("导入或新增论文后，这里会显示主题与阅读进度分布。")
        return

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.markdown("#### 主题分布")
        theme_counts = df["研究主题"].replace("", "未填写").fillna("未填写").value_counts()
        st.bar_chart(theme_counts)

    with chart_right:
        st.markdown("#### 阅读状态分布")
        status_counts = df["阅读状态"].replace("", "未开始").fillna("未开始").value_counts()
        st.bar_chart(status_counts)

    st.markdown("#### 最近加入")
    st.dataframe(df[DISPLAY_COLUMNS].head(8), hide_index=True, width="stretch")


def page_database():
    st.title("论文数据库")
    df = get_all_papers()

    if df.empty:
        st.info("当前数据库为空，可以先到“新增/编辑论文”或“导入导出”页面添加记录。")
        return

    topics = sorted([topic for topic in df["研究主题"].dropna().unique().tolist() if str(topic).strip()])
    filter_cols = st.columns([1, 1, 2])
    selected_topic = filter_cols[0].selectbox("研究主题", ["全部"] + topics)
    selected_status = filter_cols[1].selectbox("阅读状态", ["全部"] + READING_STATUSES)
    keyword = filter_cols[2].text_input("关键词检索", placeholder="标题、作者、关键词、概括或备注")

    filtered = filter_dataframe(df, selected_topic, keyword, selected_status)
    st.caption(f"当前显示 {len(filtered)} 篇论文")

    if filtered.empty:
        st.warning("没有匹配的论文记录。")
        return

    table_df = filtered[DISPLAY_COLUMNS]
    event = st.dataframe(
        table_df,
        hide_index=True,
        width="stretch",
        selection_mode="single-row",
        on_select="rerun",
        key="paper_database_table",
    )

    selected_rows = getattr(event.selection, "rows", []) if hasattr(event, "selection") else []
    if selected_rows:
        paper_id = int(table_df.iloc[selected_rows[0]]["id"])
        st.session_state.selected_paper_id = paper_id
        paper = get_paper(paper_id)
        st.divider()
        render_paper_card(paper)


def page_detail():
    st.title("论文详情")
    df = get_all_papers()
    paper = choose_paper("选择论文", df)
    render_paper_card(paper)


def page_add_edit():
    st.title("新增/编辑论文")
    tab_add, tab_edit = st.tabs(["新增论文", "编辑论文"])

    with tab_add:
        submitted, data = paper_form(empty_paper(), "add_paper_form", "保存新论文")
        if submitted:
            if not data["论文标题"].strip():
                st.error("论文标题不能为空。")
            else:
                paper_id = add_paper(data)
                st.session_state.selected_paper_id = paper_id
                st.success("新论文已保存。")

    with tab_edit:
        df = get_all_papers()
        if df.empty:
            st.info("当前还没有可编辑的论文。")
            return

        paper = choose_paper("选择要编辑的论文", df)
        if not paper:
            return

        submitted, data = paper_form(paper, f"edit_paper_form_{paper['id']}", "保存修改")
        if submitted:
            if not data["论文标题"].strip():
                st.error("论文标题不能为空。")
            else:
                update_paper(paper["id"], data)
                st.session_state.selected_paper_id = paper["id"]
                st.success("论文记录已更新。")

        st.divider()
        confirm_delete = st.checkbox("确认删除这条论文记录", key=f"confirm_delete_{paper['id']}")
        if st.button("删除论文", disabled=not confirm_delete):
            delete_paper(paper["id"])
            st.session_state.selected_paper_id = None
            st.success("论文记录已删除。")
            st.rerun()


def page_report():
    st.title("导师汇报生成")
    df = get_all_papers()
    paper = choose_paper("选择论文", df)
    if not paper:
        return

    generated = generate_mentor_report(paper)
    st.caption(f"研究方向：{classify_research_direction(paper)}")
    edited_report = st.text_area("五句式导师汇报表达", value=generated, height=260)

    cols = st.columns([1, 1, 3])
    if cols[0].button("保存五句式", type="primary"):
        update_paper(paper["id"], {"导师汇报表达": edited_report})
        st.success("已保存到该论文的“导师汇报表达”字段。")
    if cols[1].button("重置为自动生成"):
        update_paper(paper["id"], {"导师汇报表达": generated})
        st.success("已恢复为自动生成的五句式表达。")
        st.rerun()

    st.divider()
    st.markdown("#### Markdown 汇报卡片")
    render_report_markdown_box(paper, key_prefix=f"report_{paper['id']}")

    with st.expander("论文阅读卡片"):
        render_paper_card(paper)


def page_clusters():
    st.title("研究方向聚类")
    df = get_all_papers()
    if df.empty:
        st.info("当前还没有论文记录。")
        return

    clustered = df.copy()
    clustered["研究方向"] = clustered.apply(lambda row: classify_research_direction(row.to_dict()), axis=1)

    direction_counts = clustered["研究方向"].value_counts().reindex(RESEARCH_DIRECTIONS, fill_value=0)
    st.markdown("#### 方向分布")
    st.bar_chart(direction_counts)

    selected_direction = st.selectbox("查看方向", ["全部"] + RESEARCH_DIRECTIONS)
    if selected_direction != "全部":
        clustered = clustered[clustered["研究方向"] == selected_direction]

    st.caption(f"当前显示 {len(clustered)} 篇论文")

    for direction in RESEARCH_DIRECTIONS:
        group = clustered[clustered["研究方向"] == direction]
        if group.empty:
            continue
        with st.expander(f"{direction}（{len(group)}篇）", expanded=selected_direction == direction):
            for _, row in group.iterrows():
                paper = row.to_dict()
                st.markdown(f"##### {paper['论文标题']}")
                st.caption(f"{value_or_placeholder(paper, '作者')}｜{value_or_placeholder(paper, '期刊年份')}")
                st.write(value_or_placeholder(paper, "一句话概括"))
                cols = st.columns([1, 1, 5])
                if cols[0].button("查看详情", key=f"cluster_detail_{paper['id']}"):
                    st.session_state.selected_paper_id = int(paper["id"])
                    st.session_state.current_page = "论文详情"
                    st.rerun()
                with cols[1].popover("Markdown"):
                    render_report_markdown_box(paper, key_prefix=f"cluster_{paper['id']}")
                st.divider()


def page_import_export():
    st.title("导入导出")
    df = get_all_papers()

    st.markdown("#### 导入 Excel")
    sample_path = BASE_DIR / "data" / "sample.xlsx"
    if sample_path.exists():
        template_bytes = sample_path.read_bytes()
        template_name = "sample.xlsx"
    else:
        template_bytes = dataframe_to_excel_bytes(pd.DataFrame(columns=TEXT_COLUMNS))
        template_name = "研0论文阅读数据库_导入模板.xlsx"
    st.download_button(
        "下载 Excel 示例模板",
        data=template_bytes,
        file_name=template_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    uploaded_file = st.file_uploader("上传 Excel 文件", type=["xlsx", "xls"])
    if uploaded_file is not None:
        try:
            uploaded_df = pd.read_excel(uploaded_file)
            preview_df = normalize_import_dataframe(uploaded_df)
        except Exception as exc:
            st.error(f"Excel 读取失败：{exc}")
            return

        st.caption(f"识别到 {len(preview_df)} 条可导入记录")
        st.dataframe(preview_df.head(20), hide_index=True, width="stretch")
        if st.button("确认导入", type="primary"):
            count = import_papers_from_dataframe(uploaded_df)
            st.success(f"已导入 {count} 条论文记录。")
            st.rerun()

    st.divider()
    st.markdown("#### 导出 Excel")
    export_df = get_all_papers()
    if export_df.empty:
        st.info("当前没有可导出的论文记录。")
    else:
        export_bytes = dataframe_to_excel_bytes(export_df)
        st.download_button(
            "导出当前数据库",
            data=export_bytes,
            file_name="研0论文阅读数据库_导出.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


def main():
    initialize_state()
    st.sidebar.title(APP_TITLE)
    st.sidebar.radio("功能导航", PAGES, key="current_page")

    page = st.session_state.current_page
    if page == "首页仪表盘":
        page_dashboard()
    elif page == "论文数据库":
        page_database()
    elif page == "论文详情":
        page_detail()
    elif page == "新增/编辑论文":
        page_add_edit()
    elif page == "导师汇报生成":
        page_report()
    elif page == "研究方向聚类":
        page_clusters()
    elif page == "导入导出":
        page_import_export()


if __name__ == "__main__":
    main()
