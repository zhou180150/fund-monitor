with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. 加 import
text = text.replace(
    "from src.pages.compare import render_compare_page",
    "from src.pages.compare import render_compare_page\nfrom src.pages.recommend import render_recommend_page"
)

# 2. 侧边栏导航加"推荐"选项
text = text.replace(
    'page = st.sidebar.radio("导航", ["盯盘", "复盘", "对比"], horizontal=True)',
    'page = st.sidebar.radio("导航", ["盯盘", "复盘", "对比", "推荐"], horizontal=True)'
)

# 3. 页面路由加推荐
old_routes = '''elif page == "对比":
    render_compare_page(all_funds_data, index_history)'''

new_routes = '''elif page == "对比":
    render_compare_page(all_funds_data, index_history)

elif page == "推荐":
    render_recommend_page(ai)'''

text = text.replace(old_routes, new_routes)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("集成完成")
