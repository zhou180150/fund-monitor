with open("D:/fund_monitor/app_v2.py", "r", encoding="utf-8-sig") as f:
    text = f.read()

# 把 except pass 改成打印异常
text = text.replace(
    "except Exception:\n    pass",
    "except Exception as e:\n    import sys; print(f\"[DB ERROR] {e}\", file=sys.stderr)"
)

with open("D:/fund_monitor/app_v2.py", "w", encoding="utf-8") as f:
    f.write(text)
print("fixed")
