// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Collections.Concurrent;
using System.Diagnostics;
using System.Text.Json;
using MISS.Models;
using Python.Runtime;

namespace MISS.Services;

public static class PythonBridge
{
    private static dynamic? _bridge;
    private static volatile bool _initialized;
    private static BlockingCollection<Action> _workQueue = new();
    private static Thread? _workerThread;

    public static void StartWorker()
    {
        _workerThread = new Thread(() =>
        {
            using (Py.GIL())
            {
                _bridge = Py.Import("services.desktop_bridge");
            }

            while (true)
            {
                var action = _workQueue.Take();
                if (action == ShutdownSentinel) break;

                using (Py.GIL())
                {
                    action();
                }
            }
        })
        { IsBackground = true, Name = "PythonWorker" };
        _workerThread.SetApartmentState(ApartmentState.STA);
        _workerThread.Start();
    }

    private static readonly Action ShutdownSentinel = () => { };

    public static void StopWorker()
    {
        if (_workerThread == null) return;
        _workQueue.Add(ShutdownSentinel);
        _workerThread.Join(3000);
        _workerThread = null;
    }

    private static T RunOnPythonThread<T>(Func<T> func)
    {
        if (!_initialized)
            throw new InvalidOperationException("PythonBridge not initialized");
        var tcs = new TaskCompletionSource<T>();
        _workQueue.Add(() =>
        {
            try { tcs.SetResult(func()); }
            catch (Exception ex) { tcs.SetException(ex); }
        });
        return tcs.Task.Result;
    }

    private static void RunOnPythonThread(Action action)
    {
        if (!_initialized)
            throw new InvalidOperationException("PythonBridge not initialized");
        var tcs = new TaskCompletionSource<bool>();
        _workQueue.Add(() =>
        {
            try { action(); tcs.SetResult(true); }
            catch (Exception ex) { tcs.SetException(ex); }
        });
        tcs.Task.Wait();
    }

    public static void MarkInitialized() => _initialized = true;
    public static void MarkDisposed() { _initialized = false; _bridge = null; }

    public static ChatResponse Chat(string sessionId, string message, MISSProfile profile, string background = "")
    {
        return RunOnPythonThread(() =>
        {
            var profileDict = ProfileToDict(profile);
            dynamic result = _bridge.chat(sessionId, message, profileDict, background ?? "");
            return DictToChatResponse(result);
        });
    }

    public static IEnumerable<string> ChatStream(string sessionId, string message, MISSProfile profile, string background = "")
    {
        var tokens = new BlockingCollection<string>();
        _workQueue.Add(() =>
        {
            try
            {
                var profileDict = ProfileToDict(profile);
                dynamic gen = _bridge.chat_stream(sessionId, message, profileDict, background ?? "");
                foreach (var token in gen)
                {
                    string? s = token?.ToString();
                    if (s != null) tokens.Add(s);
                }
            }
            catch (Exception ex)
            {
                Trace.TraceError($"[ChatStream] {ex}");
                var errorPayload = System.Text.Json.JsonSerializer.Serialize(new
                {
                    _error = true,
                    message = "后端流处理失败"
                });
                tokens.Add($"data: {errorPayload}\n\n");
            }
            finally { tokens.CompleteAdding(); }
        });
        return tokens.GetConsumingEnumerable();
    }

    public static Dictionary<string, int> AnalyzeCharacter(string description)
    {
        return RunOnPythonThread(() =>
        {
            dynamic result = _bridge.analyze_character(description);
            dynamic json_module = Py.Import("json");
            string jsonStr = json_module.dumps(result).ToString() ?? "{}";
            return JsonSerializer.Deserialize<Dictionary<string, int>>(jsonStr) ?? new();
        });
    }

    public static bool IsApiKeyConfigured()
    {
        return RunOnPythonThread(() =>
        {
            try
            {
                dynamic config = Py.Import("config");
                dynamic settings = config.get_runtime_settings();
                return settings["openai_api_key_set"] == true;
            }
            catch { return false; }
        });
    }

    public static Dictionary<string, string> GetSettings()
    {
        return RunOnPythonThread(() =>
        {
            try
            {
                dynamic config = Py.Import("config");
                dynamic settings = config.get_runtime_settings();
                dynamic json_module = Py.Import("json");
                string jsonStr = json_module.dumps(settings).ToString() ?? "{}";
                return JsonSerializer.Deserialize<Dictionary<string, string>>(jsonStr) ?? new();
            }
            catch { return new Dictionary<string, string>(); }
        });
    }

    public static void ApplySettings(SettingsData settings)
    {
        RunOnPythonThread(() =>
        {
            dynamic dict = new PyDict();
            if (!string.IsNullOrEmpty(settings.openai_api_key))
                dict["openai_api_key"] = settings.openai_api_key.ToPython();
            if (!string.IsNullOrEmpty(settings.openai_base_url))
                dict["openai_base_url"] = settings.openai_base_url.ToPython();
            if (!string.IsNullOrEmpty(settings.model))
                dict["model"] = settings.model.ToPython();
            _bridge.apply_settings(dict);
        });
    }

    public static (bool ok, string message) PingTest()
    {
        return RunOnPythonThread(() =>
        {
            dynamic result = _bridge.ping_test();
            try
            {
                bool ok = result["ok"]?.ToString() == "True";
                string msg = result["message"]?.ToString() ?? "未知错误";
                return (ok, msg);
            }
            catch { return (false, "PingTest 解析失败"); }
        });
    }

    public static string EncryptMessage(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        return RunOnPythonThread(() =>
        {
            dynamic crypto = Py.Import("services.crypto");
            return (string)crypto.encrypt(text);
        });
    }

    public static string DecryptMessage(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        return RunOnPythonThread(() =>
        {
            dynamic crypto = Py.Import("services.crypto");
            return (string)crypto.decrypt(text);
        });
    }

    private static PyDict ProfileToDict(MISSProfile p)
    {
        var d = new PyDict();
        d["rational_emotional"] = new PyInt(p.RationalEmotional);
        d["willpower"] = new PyInt(p.Willpower);
        d["independent_submissive"] = new PyInt(p.IndependentSubmissive);
        d["education_level"] = new PyInt(p.EducationLevel);
        d["intimacy"] = new PyInt(p.Intimacy);
        d["curiosity"] = new PyInt(p.Curiosity);
        d["humor"] = new PyInt(p.Humor);
        d["aggression"] = new PyInt(p.Aggression);
        d["social_energy"] = new PyInt(p.SocialEnergy);
        d["adventurousness"] = new PyInt(p.Adventurousness);
        return d;
    }

    private static ChatResponse DictToChatResponse(dynamic d)
    {
        return new ChatResponse
        {
            InnerThought = GetStr(d, "inner_thought"),
            Spoken = GetStr(d, "spoken"),
            IntimacyChange = GetInt(d, "intimacy_change"),
            Intimacy = GetInt(d, "intimacy"),
            IntimacyReason = GetStr(d, "intimacy_reason"),
        };
    }

    private static string GetStr(dynamic d, string key)
    {
        try { return d[key]?.ToString() ?? ""; } catch { return ""; }
    }
    private static int GetInt(dynamic d, string key)
    {
        try { return (int)d[key]; } catch { return 0; }
    }
}
