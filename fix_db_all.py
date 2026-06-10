# ======== 1. recommend.py：排行榜保存 ========
with open("D:/fund_monitor/src/pages/recommend.py", "r", encoding="utf-8") as f:
    text = f.read()

# 在 st.session_state.rank_result = {"raw": raw[:20], "ai_analysis": result} 之后加保存
old = """                    st.session_state.rank_result = {"raw": raw[:20], "ai_analysis": result}
                except Exception as e:"""

new = """                    st.session_state.rank_result = {"raw": raw[:20], "ai_analysis": result}
                    try:
                        from src.data.db import save_ranking
                        save_ranking(rank_by, raw[:20])
                    except Exception:
                        pass
                except Exception as e:"""

text = text.replace(old, new)

with open("D:/fund_monitor/src/pages/recommend.py", "w", encoding="utf-8") as f:
    f.write(text)
print("recommend.py: done")

# ======== 2. app_v2.py：AI 报告保存 ========
with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

old2 = """        st.session_state.ai_report = report
        st.session_state.ai_loading = False
    except Exception as e:"""

new2 = """        st.session_state.ai_report = report
        st.session_state.ai_loading = False
        try:
            from src.data.db import save_ai_report
            fund_codes = list(all_funds_data.keys())
            save_ai_report("risk", report.get("risk", ""), fund_codes)
            if report.get("market"):
                save_ai_report("market", report.get("market", ""), fund_codes)
        except Exception:
            pass
    except Exception as e:"""

text = text.replace(old2, new2)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("app_v2.py AI report: done")

# ======== 3. app_v2.py：聊天保存 ========
with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

old3 = """            st.session_state.chat_history.append({"role": "assistant", "content": resp})
        except Exception as e:
            st.session_state.chat_history.append({"role": "assistant", "content": f"[分析失败: {e}]"})
    st.rerun()"""

new3 = """            st.session_state.chat_history.append({"role": "assistant", "content": resp})
            try:
                from src.data.db import save_chat
                save_chat(user_input, resp)
            except Exception:
                pass
        except Exception as e:
            st.session_state.chat_history.append({"role": "assistant", "content": f"[分析失败: {e}]"})
            try:
                from src.data.db import save_chat
                save_chat(user_input, f"[分析失败: {e}]")
            except Exception:
                pass
    st.rerun()"""

text = text.replace(old3, new3)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("app_v2.py chat_logs: done")
