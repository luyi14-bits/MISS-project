# Tasks

## 第一轮：阻塞性修复（必做）

- [x] Task 1: 启动 Loading 窗口
  - [x] SubTask 1.1: `App.xaml.cs` OnStartup 改为：先 Show MainWindow（Disabled + 标题"正在初始化…MISS"） → `Task.Run` 执行 `_engine.Initialize` + `LocalStore.SetBackend` → `Dispatcher.Invoke` 启用窗口 + `VM.Initialize()`
  - [x] SubTask 1.2: `App.xaml.cs` OnStartup 末尾：若首次启动则 `Dispatcher.Invoke` 弹出 SettingsWindow

- [x] Task 2: 模态窗口 StaticResource → DynamicResource
  - [x] SubTask 2.1: [CreateRoleWindow.xaml](file:///d:/Desktop/MISS/miss-desktop-wpf/Views/CreateRoleWindow.xaml) 全文 `{StaticResource` → `{DynamicResource`（6 处）
  - [x] SubTask 2.2: [SettingsWindow.xaml](file:///d:/Desktop/MISS/miss-desktop-wpf/Views/SettingsWindow.xaml) 全文 `{StaticResource` → `{DynamicResource`（6 处）

- [x] Task 3: 导出/导入 IO 线程隔离
  - [x] SubTask 3.1: [RoleSidebar.xaml.cs](file:///d:/Desktop/MISS/miss-desktop-wpf/Views/RoleSidebar.xaml.cs) `ExportRole_Click`：`File.WriteAllText(dialog.FileName, json)` 包 `Task.Run`
  - [x] SubTask 3.2: `ImportRole_Click`：`File.ReadAllText(dialog.FileName)` 包 `Task.Run`

## 第二轮：可靠性修复（该做）

- [x] Task 4: 4 处静默异常 → logging.warning
  - [x] SubTask 4.1: [prompt_builder.py](file:///d:/Desktop/MISS/miss-backend/services/prompt_builder.py) L37 `except Exception: pass` → `except Exception as e: logging.warning(...)`
  - [x] SubTask 4.2: [memory_summarizer.py](file:///d:/Desktop/MISS/miss-backend/services/memory_summarizer.py) L64 `except Exception: pass` → `except Exception as e: logging.warning(...)`
  - [x] SubTask 4.3: [vector_store.py](file:///d:/Desktop/MISS/miss-backend/services/vector_store.py) L98 `except Exception: pass` → `except Exception as e: logging.warning(...)`
  - [x] SubTask 4.4: [vector_store.py](file:///d:/Desktop/MISS/miss-backend/services/vector_store.py) L138 `except Exception: pass` → `except Exception as e: logging.warning(...)`

- [x] Task 5: config.py 字段定义去重
  - [x] SubTask 5.1: 保留 L19-28 的字段定义（含 `access_token`），删除 L8-18 的重复定义

## 第三轮：技术债清理（可以做）

- [x] Task 6: SliderItem 迁移到 CommunityToolkit.Mvvm
  - [x] SubTask 6.1: [AttributePanel.xaml.cs](file:///d:/Desktop/MISS/miss-desktop-wpf/Views/AttributePanel.xaml.cs) `SliderItem` 改为继承 `ObservableObject`，`_value` 加 `[ObservableProperty]`，删除手写 `INotifyPropertyChanged` 实现

- [x] Task 7: MessageBox 统一入口
  - [x] SubTask 7.1: 创建 `Services/NotificationService.cs`
  - [x] SubTask 7.2: [RoleSidebar.xaml.cs](file:///d:/Desktop/MISS/miss-desktop-wpf/Views/RoleSidebar.xaml.cs) `MessageBox.Show` → `NotificationService.Info/Confirm/Error`
  - [x] SubTask 7.3: [CreateRoleWindow.xaml.cs](file:///d:/Desktop/MISS/miss-desktop-wpf/Views/CreateRoleWindow.xaml.cs) `MessageBox.Show` → `NotificationService`
  - [x] SubTask 7.4: [App.xaml.cs](file:///d:/Desktop/MISS/miss-desktop-wpf/App.xaml.cs) `MessageBox.Show` → `NotificationService.Error`

# Task Dependencies
- Task 1 无依赖
- Task 2-7 均可并行执行
- Task 7.2-7.4 依赖 Task 7.1

# 验收标准
- dotnet build 0 error
- pytest 全量通过（当前 183，无回归）
- 双击 MISS.exe → 窗口即刻出现 → 初始化完成后自动启用
- education_level = -100 → 打开设置窗口 → 窗口内颜色为冰蓝色
- 导出角色 JSON → 不卡 UI
