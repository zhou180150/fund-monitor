with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

# 修复 save_ai_report 的调用——去掉错误的 f-string
old = '''    if news_data and ai.api_key:
        save_ai_report("market", 
            f"新闻{len(news_data)}条, 沪深300:{index_data}
            , list(all_funds_data.keys()))
    except Exception:'''

new = '''    if news_data and ai.api_key:
        save_ai_report("market",
            '" + f"新闻{len(news_data)}条" + '",
            list(all_funds_data.keys()))
    except Exception:'''

text = text.replace(old, new)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("fixed")
