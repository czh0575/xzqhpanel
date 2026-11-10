# 行政区划面板生成工具 v2.1

Flask 网站，使用本地 SQLite 数据库生成行政区划长面板和宽面板，支持 Excel、Stata 与打包下载。

## 数据

- `resources/adminarea.sqlite3`：运行时数据库，包含 1980—2026 年区划记录。
- `resources/县级行政区划1980-2026.xlsx`：数据库更新源文件。
- 需要更新本地库时运行 `python sync_local_db.py`。

## 本地启动

```powershell
pip install -r requirements.txt
python app.py
```

页面路径为 `/xzqh/`。下载文件保存在内存缓存中，30 分钟后自动清理。
