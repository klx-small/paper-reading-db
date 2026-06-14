import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ShowcaseAppTest(unittest.TestCase):
    def test_showcase_app_exists_and_is_read_only(self):
        source = (ROOT / "showcase_app.py").read_text(encoding="utf-8")

        self.assertIn("SHOWCASE_PAGES", source)
        self.assertIn("论文展厅", source)
        self.assertIn("导师汇报卡片", source)

        blocked_terms = [
            "新增/编辑论文",
            "导入导出",
            "add_paper",
            "update_paper",
            "delete_paper",
            "import_papers_from_dataframe",
        ]
        for term in blocked_terms:
            self.assertNotIn(term, source)

    def test_readme_mentions_showcase_deployment_entry(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("showcase_app.py", readme)
        self.assertIn("Streamlit Community Cloud", readme)

    def test_readme_mentions_full_version_deployment_entry(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("完整版", readme)
        self.assertIn("app.py", readme)
        self.assertIn("新增、编辑、导入和导出", readme)

    def test_full_app_does_not_mutate_radio_key_after_render(self):
        source = (ROOT / "app.py").read_text(encoding="utf-8")

        self.assertIn("def navigate_to_page", source)
        self.assertNotIn('st.session_state.current_page = "论文详情"', source)


if __name__ == "__main__":
    unittest.main()
