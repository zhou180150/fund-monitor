with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

# 1. 修复重复 import — 删除 L229 的 import
old1 = '    with st.spinner("AI 思考中..."):\n        try:\n            from src.analysis.advisor import AIAdvisor\n            import json'
new1 = '    with st.spinner("AI 思考中..."):\n        try:\n            import json'
text = text.replace(old1, new1)

# 2. 修复 container() 换成 expander
text = text.replace('chat_container = st.sidebar.container(height=300)\nwith chat_container:',
                    'with st.sidebar.expander("聊天记录", expanded=True):')

# 3. 数据加载完成后存 session_state
old3 = '# AI 分析：在数据加载完成后触发（由 session_state 控制）\nai_analysis = None'
new3 = '# 缓存基金数据供 AI 管家使用\nst.session_state._funds_cache = all_funds_data\nst.session_state._news_cache = news_data\nst.session_state._index_cache = index_data\n\n# AI 分析：在数据加载完成后触发（由 session_state 控制）\nai_analysis = None'
text = text.replace(old3, new3)

# 4. 修复聊天区读取数据的逻辑
old4 = '''            fund_names = \"\"\"
            if 'all_funds_data' in dir() or 'all_funds_data' in locals():
                for code, fd in all_funds_data.items() if hasattr(all_funds_data, 'items') else []:
                    nm = fd.get(\"name\", code) if fd else code
                    fund_names += f\"- {nm}\\n\"
                    fd_list.append(fd)
            
            context = f"用户当前持仓基金：\\n{fund_names}\\n用户问题：{user_input}\\n\\n请用中文回答，300字以内。"
            resp = ai.call_api("你是一个专业的中国基金分析管家，回答要简洁、有依据。", context, max_tokens=500)'''

new4 = '''            fd_cache = st.session_state.get("_funds_cache", {})
            ns_cache = st.session_state.get("_news_cache", [])
            ix_cache = st.session_state.get("_index_cache", [])
            fund_lines = "\\n".join([f"- {v.get(\"name\",k) if v else k}" for k,v in fd_cache.items()])
            idx_line = ""
            if ix_cache:
                i = ix_cache[0] if isinstance(ix_cache, list) else ix_cache
                if i and "error" not in i:
                    idx_line = f"\\n沪深300: {i.get('price','')} ({i.get('change_pct','')}%)"
            ctx = f"用户持仓:\\n{fund_lines}{idx_line}\\n\\n新闻: {len(ns_cache)}条今天的\\n\\n问题: {user_input}"
            resp = ai.call_api("你是一个专业的中国基金分析管家，回答简洁有依据。", ctx, max_tokens=500)'''

text = text.replace(old4, new4)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("修复完成")
