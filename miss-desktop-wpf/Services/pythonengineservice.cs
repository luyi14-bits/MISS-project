using System;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using Python.Runtime;

namespace MISS.Services;

public class PythonEngineService : IDisposable
{
    private bool _initialized;

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern IntPtr AddDllDirectory(string lpPathName);

    public void Initialize(string dataDir)
    {
        if (_initialized) return;

        LoggingService.Info("PythonEngineService.Initialize() starting");
        var baseDir = AppDomain.CurrentDomain.BaseDirectory;
        LoggingService.Info($"BaseDirectory = {baseDir}");

        var pythonHome = Path.Combine(baseDir, "python");
        if (!Directory.Exists(pythonHome))
        {
            LoggingService.Info($"embedded python/ not found, searching system Python...");
            pythonHome = FindPythonHome();
        }
        LoggingService.Info($"PythonHome = {pythonHome}");

        // Register python dir as DLL search path so python312.dll can find its dependencies
        // (python3.dll, vcruntime140.dll, etc.) when loaded from subdirectory
        AddDllDirectory(pythonHome);
        LoggingService.Info($"AddDllDirectory({pythonHome}) OK");

        var dllPath = Path.Combine(pythonHome, "python312.dll");
        if (!File.Exists(dllPath))
            dllPath = Path.Combine(pythonHome, "python3.dll");
        LoggingService.Info($"PythonDLL = {dllPath} (exists={File.Exists(dllPath)})");

        Environment.SetEnvironmentVariable("PYTHONNET_PYDLL", dllPath);
        Environment.SetEnvironmentVariable("PYTHONHOME", pythonHome);
        Environment.SetEnvironmentVariable("PYTHONPATH",
            Path.Combine(pythonHome, "Lib") + ";" +
            Path.Combine(pythonHome, "Lib", "site-packages"));

        Runtime.PythonDLL = dllPath;
        PythonEngine.PythonHome = pythonHome;
        LoggingService.Info("Calling PythonEngine.Initialize()...");
        PythonEngine.Initialize();
        LoggingService.Info("PythonEngine.Initialize() OK");
        PythonEngine.BeginAllowThreads();
        LoggingService.Info("BeginAllowThreads OK");

        using (Py.GIL())
        {
            LoggingService.Info("GIL acquired, setting sys.path...");
            dynamic sys = Py.Import("sys");
            sys.path.insert(0, Path.Combine(pythonHome, "Lib"));
            sys.path.insert(0, Path.Combine(pythonHome, "Lib", "site-packages"));

            var backendDir = FindBackendDir();
            if (backendDir == null)
            {
                LoggingService.Error("FindBackendDir() returned null — miss-backend not found!");
                throw new ApplicationException("miss-backend/ 目录未找到");
            }
            LoggingService.Info($"BackendDir = {backendDir}");
            sys.path.insert(0, backendDir);

            LoggingService.Info("Importing services.desktop_bridge...");
            dynamic bridge = Py.Import("services.desktop_bridge");
            LoggingService.Info("bridge module imported, calling init()...");
            dynamic result = bridge.init(dataDir);
            LoggingService.Info($"bridge.init() returned: ok={result?["ok"]}");
            try
            {
                if (result != null)
                {
                    foreach (var w in result["warnings"])
                    {
                        Trace.WriteLine($"[MISS] Warning: {w}");
                        LoggingService.Info($"  Warning: {w}");
                    }
                }
            }
            catch { }
        }

        LoggingService.Info("Calling PythonBridge.MarkInitialized()");
        PythonBridge.MarkInitialized();
        LoggingService.Info("Calling PythonBridge.StartWorker()");
        PythonBridge.StartWorker();
        LoggingService.Info("PythonEngineService.Initialize() complete");
        _initialized = true;
    }

    private static string? FindBackendDir()
    {
        var baseDir = AppDomain.CurrentDomain.BaseDirectory;
        var candidates = new[]
        {
            Path.Combine(baseDir, "miss-backend"),
            Path.Combine(baseDir, "..", "..", "..", "miss-backend"),
            Path.Combine(baseDir, "..", "..", "..", "..", "miss-backend"),
            Path.Combine(baseDir, "..", "..", "..", "..", "..", "miss-backend"),
        };
        return candidates.FirstOrDefault(Directory.Exists);
    }

    private static string FindPythonHome()
    {
        var baseDir = AppDomain.CurrentDomain.BaseDirectory;
        var candidates = new[]
        {
            Path.Combine(baseDir, "python"),
            Path.Combine(baseDir, "..", "python"),
            @"C:\Program Files\Python312",
            @"C:\Python312",
        };
        foreach (var d in candidates)
        {
            var dll = Path.Combine(d, "python312.dll");
            if (File.Exists(dll)) return d;
        }
        return candidates.FirstOrDefault(Directory.Exists) ?? baseDir;
    }

    public void Dispose()
    {
        if (_initialized)
        {
            try { PythonBridge.StopWorker(); } catch { }
            try { PythonEngine.Shutdown(); } catch { }
            _initialized = false;
        }
    }
}
