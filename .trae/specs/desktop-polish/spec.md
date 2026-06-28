# MISS Desktop 打磨 Spec — 全线问题修复

## Why
全项目自查发现 12 个缺陷，分为三轮打磨：
- 第一轮：影响用户体验的阻塞性问题（启动白屏、主题不一致、IO 卡 UI）
- 第二轮：影响运维排查的静默失败（except:pass 无日志、config 代码重复）
- 第三轮：技术债清理（手写 INotifyPropertyChanged、MessageBox 耦合）

## What Changes
- 启动流程从同步阻塞改为异步 Loading 窗口
- 模态窗口 `StaticResource` → `DynamicResource`，⑨模式下颜色一致
- `File.ReadAllText/WriteAllText` 包 `Task.Run` 避免 UI 卡顿
- 4 处 `except Exception: pass` → `logging.warning`
- `config.py` 字段定义去重
- `SliderItem` 从手写 INotifyPropertyChanged → `CommunityToolkit.Mvvm`
- 新增 `NotificationService` 统一 MessageBox 调用入口

## Impact
- Affected code: `App.xaml.cs`, `CreateRoleWindow.xaml`, `SettingsWindow.xaml`, `RoleSidebar.xaml.cs`, `prompt_builder.py`, `memory_summarizer.py`, `vector_store.py`, `config.py`, `AttributePanel.xaml.cs`
- 新增: `Services/NotificationService.cs`
- 不改: `MainViewModel.cs`, `PythonBridge.cs`, `LiteDbLocalStore.cs`, `desktop_bridge.py`, `llm_caller.py`

---

## ADDED Requirements

### Requirement: 启动加载窗口
The system SHALL 双击 MISS.exe 后立即显示窗口（Disabled 状态，标题显示"正在初始化…"），Python 引擎和数据库初始化在后台线程执行，完成后启用窗口。

#### Scenario: 启动流程
- **WHEN** 用户双击 MISS.exe
- **THEN** 即刻弹出 MainWindow（Disabled + 标题"正在初始化…"）→ `Task.Run` 执行引擎初始化 → `Dispatcher.Invoke` 启用窗口 + 加载数据

### Requirement: NotificationService
The system SHALL 提供统一的消息通知入口类 `NotificationService`，所有 View 通过该服务调用 MessageBox 而非直接依赖 `System.Windows.MessageBox`。

#### API 面
```csharp
public static class NotificationService
{
    public static void Info(string message);
    public static bool Confirm(string message);
    public static void Error(string message);
}
```

## MODIFIED Requirements

### Requirement: 模态窗口主题响应
修改前：`CreateRoleWindow.xaml` 和 `SettingsWindow.xaml` 全部使用 `{StaticResource}`，切换⑨模式时不影响这两个窗口。
修改后：改为 `{DynamicResource}`，与主窗口主题保持一致。

### Requirement: 导出/导入 IO 线程隔离
修改前：`RoleSidebar.xaml.cs` 中 `File.ReadAllText`/`File.WriteAllText` 在 UI 线程同步执行。
修改后：`await Task.Run(() => File.WriteAllText(...))` 包装到后台线程。

### Requirement: 静默异常加日志
修改前：4 处 `except Exception: pass` 静默吞掉向量库降级异常。
修改后：每处改为 `except Exception as e: logging.warning(f"[降级] xxx失败: {e}")`。

### Requirement: config.py 字段去重
修改前：[config.py](file:///d:/Desktop/MISS/miss-backend/config.py) 第 8-28 行定义了两份几乎相同的 Settings 类字段。
修改后：保留一份定义（含 `access_token`），删除重复部分。

### Requirement: SliderItem 迁移到 CommunityToolkit.Mvvm
修改前：[AttributePanel.xaml.cs](file:///d:/Desktop/MISS/miss-desktop-wpf/Views/AttributePanel.xaml.cs) 中 `SliderItem` 手写 `INotifyPropertyChanged`。
修改后：继承 `ObservableObject`，`_value` 字段加 `[ObservableProperty]`。

---

## REMOVED Requirements
无。只修改不删除。
