# Checklist

## 第一轮：阻塞性修复

### 启动 Loading 窗口
- [x] `App.xaml.cs` OnStartup 中先 `new MainWindow().Show()`（立即出窗口）
- [x] Show 后设置 `mainWindow.IsEnabled = false` + `mainWindow.Title = "MISS — 正在初始化…"`
- [x] `Task.Run` 包 `_engine.Initialize(dataDir)` + `LocalStore.SetBackend`
- [x] 引擎就绪后 `Dispatcher.Invoke` 启用窗口 + 重置 Title
- [x] 首次启动弹 SettingsWindow 在 Dispatcher.Invoke 内执行

### 模态窗口 DynamicResource
- [x] `CreateRoleWindow.xaml` 中 6 处 `{StaticResource XxxBrush}` → `{DynamicResource XxxBrush}`
- [x] `SettingsWindow.xaml` 中 6 处 `{StaticResource XxxBrush}` → `{DynamicResource XxxBrush}`
- [x] 启动后设置 education_level = -100 → 打开创建角色窗口 → 窗口颜色为冰蓝色

### IO 线程隔离
- [x] `RoleSidebar.ExportRole_Click` 中 `File.WriteAllText` 包 `await Task.Run(() => ...)`
- [x] `RoleSidebar.ImportRole_Click` 中 `File.ReadAllText` 包 `await Task.Run(() => ...)`

## 第二轮：可靠性修复

### 静默异常加日志
- [x] `prompt_builder.py` L37 `except Exception: pass` → `logging.warning`
- [x] `memory_summarizer.py` L64 `except Exception: pass` → `logging.warning`
- [x] `vector_store.py` L98 `except Exception: pass` → `logging.warning`
- [x] `vector_store.py` L138 `except Exception: pass` → `logging.warning`

### config.py 去重
- [x] Settings 类字段定义只有一份（含 `access_token`）

## 第三轮：技术债清理

### SliderItem MVVM 化
- [x] `SliderItem` 继承 `ObservableObject`（非手写 `INotifyPropertyChanged`）
- [x] `_value` 字段使用 `[ObservableProperty]` 源生成器

### NotificationService
- [x] `Services/NotificationService.cs` 存在，含 `Info/Confirm/Error` 静态方法
- [x] `RoleSidebar.xaml.cs` 不再直接调 `MessageBox.Show`
- [x] `CreateRoleWindow.xaml.cs` 不再直接调 `MessageBox.Show`
- [x] `App.xaml.cs` 不再直接调 `MessageBox.Show`

## 验收

- [x] dotnet build 0 error
- [x] pytest 全量通过无回归（当前基线 183）
- [x] 双击 MISS.exe → 窗口即刻出现（< 500ms）
- [x] 初始化完成后窗口自动变为可用状态
- [x] ⑨模式下所有窗口（含模态）为冰蓝色
- [x] 导出角色 JSON → UI 不卡顿
