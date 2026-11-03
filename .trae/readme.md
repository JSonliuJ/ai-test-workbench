## 虚拟环境运行
```
# 创建.venv文件夹
python -m venv .venv
# 激活虚拟环境
& ".\.venv\Scripts\Activate.ps1"
# 退出虚拟环境
deactivate
# 删除虚拟环境
rmdir /s /q .venv
Scripts\activate
# 运行项目
切到虚拟环境后 python xxxx.py
直接运行 .\.venv\Scripts\python.exe xxxx.py
```