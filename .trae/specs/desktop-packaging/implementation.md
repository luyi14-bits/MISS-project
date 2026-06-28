# 桌面版打包实施文档 —— pywebview 方案

> **管线状态**：架构设计完成，原生窗口验证通过（见 §5）。
> **目标**：生成一个双击即可运行的独立 Windows 桌面程序，不依赖外部浏览器，不需要用户安装 Python / Rust / Node.js。

---

## 1. 架构

```
MISS.exe  (PyInstaller 打包)
  ├── 同进程内 daemon 线程 → uvicorn → FastAPI (127.0.0.1:8000)
  ├── EdgeChromium WebView 嵌入窗口 (pywebview)
  └── 窗口关闭 → 进程退出 → 后端一起终止
```

与 Tauri 方案的本质区别：
- Tauri 用 Rust 编译原生壳 → 受限于当前机器 Rust std::process Windows bug
- pywebview 用 Python + Windows 系统自带 WebView2 控件 → 零外部依赖

---

## 2. 前置依赖

```bash
pip install pywebview pyinstaller
```

**无需安装 Rust、Node.js、npm**。Python 3.10+ 即可。

---

## 3. 文件结构

```
miss-desktop-pywv/
├── launcher.py          ← 入口（见 §4）
├── miss-backend/        ← 从 miss-backend/ 完整复制
├── frontend-desktop/    ← 从 miss-desktop/src/ 复制 (含 assets/)
├── build/               ← PyInstaller 生成，可删除
└── dist/                ← PyInstaller 生成，MISS.exe 在这里
```

---

## 4. launcher.py 完整代码

```python
import sys
import os
import threading
import time

if getattr(sys, "frozen", False):
    DIR = sys._MEIPASS
else:
    DIR = os.path.dirname(os.path.abspath(__file__))

BACKEND_DIR = os.path.join(DIR, "miss-backend")
FRONTEND_DIR = os.path.join(DIR, "frontend-desktop")
os.environ["MISS_FRONTEND_DIR"] = FRONTEND_DIR

sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, os.path.join(BACKEND_DIR, "services"))

DATA_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.dirname(os.path.abspath(sys.argv[0]))),
    "MISS",
)
os.environ["MISS_DATA_DIR"] = DATA_DIR
os.makedirs(DATA_DIR, exist_ok=True)

PORT = 8000
HOST = "127.0.0.1"
URL = f"http://{HOST}:{PORT}/demo/"


def run_backend():
    import uvicorn
    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        log_level="warning",
        access_log=False,
    )


def main():
    t = threading.Thread(target=run_backend, daemon=True)
    t.start()

    for _ in range(60):
        try:
            import urllib.request
            r = urllib.request.urlopen(f"http://{HOST}:{PORT}/health", timeout=1)
            if r.status == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    else:
        sys.exit(1)

    try:
        import webview
        webview.create_window(
            "MISS",
            URL,
            width=1100,
            height=750,
            min_size=(800, 500),
            resizable=True,
        )
        webview.start(gui="edgechromium")
    except Exception:
        import traceback
        traceback.print_exc()
        import webbrowser
        webbrowser.open(URL)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
```

**关键设计点**：
| 行 | 说明 |
|----|------|
| L7-9 | `sys._MEIPASS` 适配 PyInstaller 的临时解压目录 |
| L13 | `MISS_FRONTEND_DIR` 环境变量 → main.py 用它找前端文件 |
| L15-16 | `sys.path.insert` → uvicorn 导入模块时能找到 miss-backend |
| L42-43 | daemon 线程 → 窗口退出时进程自然终止，后端随之结束 |
| L67 | `gui="edgechromium"` → 强制使用 Edge WebView2 |

---

## 5. PyInstaller 打包命令

在 `miss-desktop-pywv/` 目录下执行：

```powershell
python -m PyInstaller ^
  --onedir ^
  --windowed ^
  --name MISS ^
  --add-data "miss-backend;miss-backend" ^
  --add-data "frontend-desktop;frontend-desktop" ^
  --collect-all pythonnet ^
  --collect-all clr_loader ^
  --collect-binaries pythonnet ^
  --collect-binaries clr_loader ^
  --hidden-import fastapi.staticfiles ^
  --hidden-import fastapi.middleware ^
  --hidden-import fastapi.middleware.cors ^
  --hidden-import starlette ^
  --hidden-import starlette.staticfiles ^
  --hidden-import jinja2 ^
  --hidden-import pydantic ^
  --hidden-import pydantic_settings ^
  --hidden-import sqlalchemy ^
  --hidden-import chromadb ^
  --hidden-import openai ^
  --hidden-import uvicorn ^
  --hidden-import uvicorn.loops.auto ^
  --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.lifespan.on ^
  --hidden-import fastapi ^
  --hidden-import python_multipart ^
  --hidden-import webview ^
  --hidden-import webview.platforms.edgechromium ^
  --hidden-import models ^
  --hidden-import models.preset ^
  --hidden-import models.memory ^
  --hidden-import routers ^
  --hidden-import routers.chat ^
  --hidden-import routers.preset ^
  --hidden-import routers.admin ^
  --hidden-import routers.character ^
  --hidden-import routers.settings ^
  --hidden-import services ^
  --hidden-import services.llm_caller ^
  --hidden-import services.prompt_builder ^
  --hidden-import services.attribute_engine ^
  --hidden-import services.memory_manager ^
  --hidden-import services.vector_store ^
  --exclude tkinter ^
  --exclude matplotlib ^
  --exclude numpy ^
  --exclude pandas ^
  --exclude PIL ^
  --exclude cv2 ^
  --exclude PyQt5 ^
  --exclude PySide6 ^
  --exclude PySide2 ^
  --exclude PyQt6 ^
  launcher.py -y
```

打包耗时约 3-5 分钟，输出在 `dist/MISS/MISS.exe`。

---

## 6. 已知踩坑与修复

| # | 问题 | 原因 | 修复 |
|---|------|------|------|
| 1 | `ModuleNotFoundError: fastapi.staticfiles` | PyInstaller 不会自动收集 fastapi.staticfiles 子模块 | 加 `--hidden-import fastapi.staticfiles --hidden-import starlette --hidden-import starlette.staticfiles` |
| 2 | 子进程 uvicorn 无法启动 (`--windowed` 模式) | `subprocess.Popen` 在无控制台窗口模式下受限 | **禁止用 subprocess**。必须用 `threading.Thread(target=run_backend, daemon=True)` 同进程内启动 |
| 3 | webview 窗口弹出后崩溃 | pythonnet/clr_loader 的 .NET DLL 未被收集 | 加 `--collect-all pythonnet --collect-all clr_loader --collect-binaries pythonnet --collect-binaries clr_loader` |
| 4 | `--onefile` 体积 48MB 但解压慢 | 首次启动需解压到临时目录 | 用 `--onedir`（目录模式），启动快，总体积相近 |
| 5 | Qt 冲突 `PyQt5 + PySide6` | pywebview 在 Windows 上不需要 Qt，但已安装的 Qt 包会被 PyInstaller 误收集 | `--exclude PyQt5 --exclude PySide6 --exclude PySide2 --exclude PyQt6` |
| 6 | 浏览器地址栏显示 localhost 而非原生窗口 | webview 未安装或 pythonnet 加载失败 | 确认 `pip install pywebview` 成功；若失败则 fallback 到 `webbrowser.open()` |

---

## 7. 验证清单

- [ ] `pip install pywebview pyinstaller` 无报错
- [ ] 复制 `miss-backend/` 和 `frontend-desktop/` 到项目目录
- [ ] `main.py` 中 `desktop_dir` 读取 `MISS_FRONTEND_DIR` 环境变量（已在 miss-backend/main.py 中完成）
- [ ] PyInstaller 打包成功 → `dist/MISS/MISS.exe` 存在
- [ ] 双击 `MISS.exe` → 弹出独立原生窗口（标题 "MISS"、1100×750）
- [ ] 窗口内加载 `http://127.0.0.1:8000/demo/` → 显示聊天界面
- [ ] 侧边栏标题显示"角色"
- [ ] 设置 API Key → 对话正常
- [ ] 关闭窗口 → 8000 端口释放

---

## 8. 给程序组的备注

1. **不要用 subprocess 启动 uvicorn**。已验证在 PyInstaller `--windowed` 模式下子进程无法启动。用 threading 同进程内跑。
2. **`--hidden-import fastapi.staticfiles` 是必须的**，缺了会在启动时报 `ModuleNotFoundError`。
3. **`--collect-all pythonnet`** 必须保留，否则 pywebview 的 EdgeChromium 后端找不到 .NET CLR loader。
4. 如果打包后在**另一台机器**上测试失败，最可能是缺少 WebView2 Runtime。Windows 10 1809+ / Windows 11 自带，如果是 Windows 10 老版本需安装：https://go.microsoft.com/fwlink/p/?LinkId=2124703
