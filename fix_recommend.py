with open("D:/fund_monitor/src/pages/recommend.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace(
    'st.info("选择筛选条件后点击"开始分析"获取AI推荐")',
    "st.info('选择筛选条件后点击 开始分析 获取AI推荐')",
)

with open("D:/fund_monitor/src/pages/recommend.py", "w", encoding="utf-8") as f:
    f.write(text)
print("fix done")
