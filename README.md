# 研0论文阅读数据库

这是一个中文 Streamlit 论文阅读数据库，面向会计学/财务管理方向研0学生，用来积累论文阅读笔记、管理阅读进度，并生成适合向导师汇报的中文表达。

项目包含两个入口：

- `showcase_app.py`：公开展示版，适合部署到 Streamlit Community Cloud 后分享给别人浏览。
- `app.py`：本地管理版，适合自己新增、编辑、导入和导出论文数据。

## 功能

- 首页仪表盘：展示论文数量、主题分布、阅读状态分布。
- 论文数据库：表格展示论文，支持按研究主题、关键词、阅读状态筛选。
- 论文详情：展示完整论文阅读卡片和导师汇报卡片。
- 新增/编辑论文：支持新增、修改、删除论文记录。
- 导师汇报生成：自动生成“五句式”导师汇报表达，并支持复制为 Markdown。
- 研究方向聚类：自动按研究方向归类论文。
- 导入导出：支持 Excel 导入与导出。

## 项目结构

```text
paper-reading-db/
├── app.py
├── showcase_app.py
├── database.py
├── utils.py
├── requirements.txt
├── README.md
├── data/
│   ├── papers.db
│   └── sample.xlsx
└── exports/
```

说明：

- `data/papers.db` 是本地 SQLite 数据库文件。
- `data/sample.xlsx` 是 Excel 导入示例模板。
- `exports/` 用于存放后续导出的文件或备份文件。

## 安装

进入项目目录后运行：

```bash
pip install -r requirements.txt
```

如果 Windows 终端提示找不到 `pip`，可以改用：

```bash
py -m pip install -r requirements.txt
```

## 启动公开展示版

```bash
streamlit run showcase_app.py
```

展示版只用于浏览，不提供数据修改入口，适合上线分享。

## 启动本地管理版

```bash
streamlit run app.py
```

如果 Windows 终端提示找不到 `streamlit`，可以改用：

```bash
py -m streamlit run app.py
```

启动后，浏览器会打开本地页面。若没有自动打开，可以在终端提示中复制本地地址访问。

## 上线到 Streamlit Community Cloud

1. 将本项目上传到 GitHub 仓库。
2. 打开 Streamlit Community Cloud。
3. 创建新应用时选择该 GitHub 仓库。
4. 入口文件填写：

```text
showcase_app.py
```

5. 部署完成后，Streamlit 会生成一个可以分享给别人访问的网址。

注意：`data/papers.db` 会随仓库一起公开，适合展示样例数据。如果后续要让多人在线写入和长期保存数据，建议改用云数据库。

## Excel 导入

1. 打开应用左侧的“导入导出”页面。
2. 可使用 `data/sample.xlsx` 作为填写模板。
3. 在模板中填写论文信息。
4. 上传填写后的 `.xlsx` 或 `.xls` 文件。
5. 预览无误后点击“确认导入”。

导入时会识别以下字段：

```text
论文标题、作者、期刊年份、研究主题、研究现象、核心问题、核心机制、创造的价值、
研究框架、一句话概括、核心逻辑链、价值创造路径、导师汇报表达、我的思考问题、
关键词、阅读状态、重要程度、备注
```

如果 Excel 缺少某些字段，系统会自动补为空值；`阅读状态` 默认是“未开始”，`重要程度` 默认是“中”。空标题记录不会导入。

## Excel 导出

1. 打开应用左侧的“导入导出”页面。
2. 在“导出 Excel”区域点击“导出当前数据库”。
3. 下载得到当前论文数据库的 Excel 文件。

## 建议填写方式

- `研究主题`：用稳定主题词，例如“数字化转型”“数据资产入表”“碳信息披露”。
- `核心问题`：写成一个清楚的问题句。
- `核心机制`：记录为什么会产生影响。
- `核心逻辑链`：可以写成“现象 -> 问题 -> 机制 -> 结果 -> 价值”。
- `导师汇报表达`：系统会自动生成五句式表达，也可以手动修改。

## 运行测试

```bash
python -m unittest -v tests.test_core
```
