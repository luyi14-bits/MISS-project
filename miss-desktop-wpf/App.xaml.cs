using System.Diagnostics;
using System.IO;
using System.Windows;
using System.Windows.Media;
using System.Windows.Threading;
using MISS.Services;
using MISS.ViewModels;

namespace MISS;

public partial class App : Application
{
    private readonly PythonEngineService _engine = new();
    private LiteDbLocalStore? _db;

    private async void OnStartup(object sender, StartupEventArgs e)
    {
        DispatcherUnhandledException += (s, args) =>
        {
            var msg = $"致命崩溃:\n{args.Exception.Message}\n\n{args.Exception.StackTrace}";
            File.AppendAllText(
                Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MISS", "crash.log"),
                $"\n[{DateTime.Now}] {args.Exception}");
            MessageBox.Show(msg, "程序崩溃");
            args.Handled = true;
        };

        var dataDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MISS");
        Directory.CreateDirectory(dataDir);

        var mainWindow = new MainWindow();
        mainWindow.IsEnabled = false;
        mainWindow.Title = "MISS — 正在初始化…";
        mainWindow.Show();

        try
        {
            await Task.Run(() =>
            {
                _db = new LiteDbLocalStore();
                LocalStore.SetBackend(_db);
                _engine.Initialize(dataDir);

                var settings = LocalStore.LoadSettings();
                if (settings != null)
                    PythonBridge.ApplySettings(settings);
            });
        }
        catch (Exception ex)
        {
            File.AppendAllText(
                Path.Combine(dataDir, "crash.log"),
                $"\n[{DateTime.Now:yyyy/MM/d HH:mm:ss}] Init error: {ex}");
            MessageBox.Show($"启动失败:\n{ex.Message}", "MISS 启动失败");
            Shutdown();
            return;
        }

        try
        {
            mainWindow.Title = "MISS";
            mainWindow.IsEnabled = true;
            MainViewModel.Instance.Initialize();

            if (!PythonBridge.IsApiKeyConfigured())
            {
                var settingsWin = new Views.SettingsWindow { Owner = Current.MainWindow };
                settingsWin.ShowDialog();
            }
        }
        catch (Exception ex)
        {
            File.AppendAllText(
                Path.Combine(dataDir, "crash.log"),
                $"\n[{DateTime.Now:yyyy/MM/d HH:mm:ss}] Post-init error: {ex}");
            MessageBox.Show($"初始化界面失败:\n{ex.Message}", "MISS 启动失败");
            Shutdown();
        }
    }

    private void OnExit(object sender, ExitEventArgs e)
    {
        try { MainViewModel.Instance.ImmediatelySave(); } catch { }
        try { MainViewModel.Instance.Dispose(); } catch { }
        try { _db?.Dispose(); } catch { }
        try { PythonBridge.StopWorker(); } catch { }
        try { PythonBridge.MarkDisposed(); } catch { }
        try { _engine.Dispose(); } catch { }
    }

    public static void SetTheme(bool isCirno)
    {
        var warm = new Dictionary<string, Color>
        {
            ["PrimaryBrush"] = Color.FromRgb(0xD4, 0x78, 0x6E),
            ["PrimaryHoverBrush"] = Color.FromRgb(0xC0, 0x5A, 0x4E),
            ["PrimaryLightBrush"] = Color.FromRgb(0xFB, 0xE5, 0xE0),
            ["BgBrush"] = Color.FromRgb(0xFD, 0xF8, 0xF0),
            ["SurfaceBrush"] = Color.FromRgb(0xFF, 0xFB, 0xFA),
            ["SurfaceAltBrush"] = Color.FromRgb(0xF5, 0xED, 0xE3),
            ["BorderBrush"] = Color.FromRgb(0xE8, 0xDD, 0xD4),
            ["TextBrush"] = Color.FromRgb(0x4A, 0x37, 0x28),
            ["TextSecondaryBrush"] = Color.FromRgb(0x8B, 0x73, 0x55),
            ["UserBubbleBrush"] = Color.FromRgb(0xF0, 0xE6, 0xDA),
            ["MissBubbleBrush"] = Color.FromRgb(0xFB, 0xE5, 0xE0),
        };
        var cirno = new Dictionary<string, Color>
        {
            ["PrimaryBrush"] = Color.FromRgb(0x00, 0xBF, 0xFF),
            ["PrimaryHoverBrush"] = Color.FromRgb(0x00, 0x9A, 0xCC),
            ["PrimaryLightBrush"] = Color.FromRgb(0xD0, 0xF0, 0xFF),
            ["BgBrush"] = Color.FromRgb(0xF0, 0xF8, 0xFF),
            ["SurfaceBrush"] = Color.FromRgb(0xF5, 0xFA, 0xFE),
            ["SurfaceAltBrush"] = Color.FromRgb(0xE8, 0xF4, 0xFC),
            ["BorderBrush"] = Color.FromRgb(0xB8, 0xE0, 0xF0),
            ["TextBrush"] = Color.FromRgb(0x2A, 0x4A, 0x5A),
            ["TextSecondaryBrush"] = Color.FromRgb(0x5A, 0x8A, 0x9A),
            ["UserBubbleBrush"] = Color.FromRgb(0xE8, 0xF4, 0xFC),
            ["MissBubbleBrush"] = Color.FromRgb(0xE0, 0xF0, 0xFA),
        };
        var dict = isCirno ? cirno : warm;
        foreach (var kv in dict)
            Current.Resources[kv.Key] = new SolidColorBrush(kv.Value);
    }
}
