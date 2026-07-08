// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Diagnostics;
using System.Threading.Channels;
using System.Windows;
using System.Windows.Data;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.ML.Tokenizers;
using MISS.Controls;
using MISS.Models;
using MISS.Services;

namespace MISS.ViewModels;

public partial class MainViewModel : ObservableObject, IDisposable
{
    private static MainViewModel? _instance;
    public static MainViewModel Instance => _instance ??= new();

    private readonly object _lockObject = new();
    private CancellationTokenSource? _saveDebounceToken;

    private static readonly Tokenizer _tokenizer = TiktokenTokenizer.CreateForModel("gpt-4o");
    private const int MaxContextTokenLimit = 2048;

    #region Observable Properties

    [ObservableProperty]
    private ObservableCollection<SessionData> _sessions = new();

    [ObservableProperty]
    private ObservableCollection<RoleData> _roles = new();

    [ObservableProperty]
    private SessionData? _currentSession;

    [ObservableProperty]
    private RoleData? _currentRole;

    [ObservableProperty]
    private bool _isInnerThoughtVisible;

    [ObservableProperty]
    private bool _isCirnoMode;

    [ObservableProperty]
    private bool _isPanelCollapsed;

    #endregion

    private readonly ObservableCollection<ChatMessage> _allMessages = new();
    private readonly CollectionViewSource _messagesViewSource = new();

    public ICollectionView MessagesView => _messagesViewSource.View;

    public MainViewModel()
    {
        BindingOperations.EnableCollectionSynchronization(_allMessages, _lockObject);

        _messagesViewSource.Source = _allMessages;
        _messagesViewSource.View.Filter = msg =>
        {
            if (msg is not ChatMessage m) return true;
            if (string.IsNullOrEmpty(_currentRole?.Name)) return true;
            return m.RoleName == _currentRole.Name;
        };
    }

    public void Initialize()
    {
        LoadRoles();
        LoadSessions();
    }

    partial void OnCurrentRoleChanged(RoleData? value)
    {
        if (value != null)
        {
            IsCirnoMode = value.Profile.EducationLevel == -100;
        }

        DispatcherHelper.Run(() =>
        {
            if (_currentSession != null)
            {
                try
                {
                    // ① 保存当前消息到 LiteDB（防切换丢失）
                    LocalStore.SaveMessages(_currentSession.Id, _allMessages.ToList());

                    // ② 清空当前消息集合
                    _allMessages.Clear();

                    // ③ 按角色重新加载：用户消息 OR RoleName 匹配
                    var msgs = LocalStore.LoadMessages(_currentSession.Id);
                    foreach (var m in msgs)
                    {
                        if (m.IsUser || m.RoleName == value?.Name)
                            _allMessages.Add(m);
                    }

                    // ④ 更新当前会话的角色名
                    if (value != null)
                        _currentSession.RoleName = value.Name;
                }
                catch (Exception ex)
                {
                    Trace.TraceError($"[OnCurrentRoleChanged] 消息隔离失败: {ex}");
                }
            }

            _messagesViewSource.View.Refresh();
        });
    }

    partial void OnIsCirnoModeChanged(bool value)
    {
        App.SetTheme(value);
    }

    partial void OnIsInnerThoughtVisibleChanged(bool value)
    {
        var msgs = _allMessages.Where(m => !m.IsUser).ToList();
        foreach (var m in msgs)
            m.IsInnerVisible = value;
    }

    partial void OnCurrentSessionChanged(SessionData? value)
    {
        if (value == null) return;
        DispatcherHelper.Run(() =>
        {
            if (!string.IsNullOrEmpty(value.RoleName))
            {
                var role = _roles.FirstOrDefault(r => r.Name == value.RoleName);
                if (role != null) _currentRole = role;
            }
            _allMessages.Clear();
            var messages = LocalStore.LoadMessages(value.Id);
            foreach (var msg in messages)
                _allMessages.Add(msg);
            _messagesViewSource.View.Refresh();
        });
    }

    #region Load / Save

    private void LoadRoles()
    {
        _roles.Clear();
        foreach (var r in LocalStore.GetBuiltinRoles())
            _roles.Add(r);
        foreach (var r in LocalStore.LoadRoles())
            _roles.Add(r);
    }

    private void LoadSessions()
    {
        _sessions.Clear();
        var sessions = LocalStore.LoadSessions();
        if (sessions.Count == 0)
        {
            sessions = new List<SessionData>
            {
                new() { Id = 1, Title = "今天的闲聊", CreatedAt = DateTime.Now },
                new() { Id = 2, Title = "昨天的讨论", CreatedAt = DateTime.Now.AddDays(-1) },
                new() { Id = 3, Title = "属性调试", CreatedAt = DateTime.Now.AddHours(-6) },
            };
        }
        foreach (var s in sessions)
            _sessions.Add(s);

        _currentSession = _sessions.FirstOrDefault() ?? _sessions.First();
    }

    private void DebouncedSaveSessions()
    {
        _saveDebounceToken?.Cancel();
        _saveDebounceToken = new CancellationTokenSource();
        var token = _saveDebounceToken.Token;

        Task.Run(async () =>
        {
            try
            {
                await Task.Delay(300, token);
                LocalStore.SaveSessions(_sessions.ToList());

                if (_currentSession != null)
                    LocalStore.SaveMessages(_currentSession.Id, _allMessages.ToList());
            }
            catch (TaskCanceledException) { }
            catch (Exception ex)
            {
                Trace.TraceError($"[Save] {ex.Message}");
            }
        }, token);
    }

    public void ImmediatelySave()
    {
        Task.Run(() =>
        {
            try
            {
                LocalStore.SaveSessions(_sessions.ToList());
                if (_currentSession != null)
                    LocalStore.SaveMessages(_currentSession.Id, _allMessages.ToList());
            }
            catch (Exception ex)
            {
                Trace.TraceError($"[Save] {ex.Message}");
            }
        });
    }

    #endregion

    #region Commands

    [RelayCommand]
    private void CreateSession()
    {
        var nextId = _sessions.Count > 0 ? _sessions.Max(s => s.Id) + 1 : 1;
        var session = new SessionData
        {
            Id = nextId,
            Title = "新对话",
            RoleName = _currentRole?.Name ?? "",
            CreatedAt = DateTime.Now,
        };

        DispatcherHelper.Run(() =>
        {
            _sessions.Add(session);
            _currentSession = session;
            _allMessages.Clear();
            _messagesViewSource.View.Refresh();
        });

        ImmediatelySave();
    }

    [RelayCommand]
    private void DeleteSession(SessionData? session)
    {
        if (session == null || _sessions.Count <= 1) return;

        Task.Run(() =>
        {
            LocalStore.DeleteMessages(session.Id);
            LocalStore.DeleteSession(session.Id);
        });

        DispatcherHelper.Run(() =>
        {
            _sessions.Remove(session);
            if (_currentSession == session)
            {
                _currentSession = _sessions.FirstOrDefault();
            }
        });

        ImmediatelySave();
    }

    [RelayCommand]
    private void ToggleInnerThought()
    {
        IsInnerThoughtVisible = !IsInnerThoughtVisible;
    }

    #endregion

    #region Message Sending

    public async Task SendMessage(string text)
    {
        if (string.IsNullOrWhiteSpace(text) || _currentSession == null) return;

        string sessionId = $"sess_{_currentSession.Id}";
        string pySessionId = $"sess_{_currentSession.Id}_{_currentRole?.Name ?? "default"}";
        var profile = _currentRole?.Profile ?? new MISSProfile();
        string background = _currentRole?.Background ?? "";

        var userMsg = new ChatMessage
        {
            SessionId = sessionId,
            Sender = "我",
            RoleName = _currentRole?.Name ?? "",
            Text = text,
            IsUser = true,
            IsInnerVisible = false,
            Timestamp = DateTime.Now,
        };
        var missMsg = new ChatMessage
        {
            SessionId = sessionId,
            Sender = _currentRole?.Name ?? "MISS",
            RoleName = _currentRole?.Name ?? "MISS",
            Text = "思考中...",
            IsUser = false,
            IsInnerVisible = _isInnerThoughtVisible,
            Timestamp = DateTime.Now,
        };

        DispatcherHelper.Run(() => { _allMessages.Add(userMsg); _allMessages.Add(missMsg); });

        try
        {
            var resp = await Task.Run(() => PythonBridge.Chat(pySessionId, text, profile, background, _currentRole?.Tags));

            DispatcherHelper.Run(() =>
            {
                missMsg.Text = resp.Spoken;
                missMsg.InnerThought = resp.InnerThought;
                missMsg.TotalTokenCount = EstimateTokens(resp.Spoken + resp.InnerThought);
                missMsg.SpokenTokenCount = EstimateTokens(resp.Spoken);

                if (resp.IntimacyChange != 0)
                {
                    profile.Intimacy = resp.Intimacy;
                }
            });

            DebouncedSaveSessions();
        }
        catch (Exception ex)
        {
            Trace.TraceError($"[SendMessage] {ex}");
            DispatcherHelper.Run(() =>
            {
                missMsg.Text = "生成失败，请稍后重试";
            });
        }
    }

    public async IAsyncEnumerable<string> SendMessageStream(string text)
    {
        if (string.IsNullOrWhiteSpace(text) || _currentSession == null) yield break;

        string sessionId = $"sess_{_currentSession.Id}";
        string pySessionId = $"sess_{_currentSession.Id}_{_currentRole?.Name ?? "default"}";
        var profile = _currentRole?.Profile ?? new MISSProfile();
        string background = _currentRole?.Background ?? "";

        var userMsg = new ChatMessage
        {
            SessionId = sessionId,
            Sender = "我",
            RoleName = _currentRole?.Name ?? "",
            Text = text,
            IsUser = true,
            Timestamp = DateTime.Now,
        };
        var missMsg = new ChatMessage
        {
            SessionId = sessionId,
            Sender = _currentRole?.Name ?? "MISS",
            RoleName = _currentRole?.Name ?? "MISS",
            Text = "",
            IsUser = false,
            IsInnerVisible = _isInnerThoughtVisible,
            Timestamp = DateTime.Now,
        };

        DispatcherHelper.Run(() => { _allMessages.Add(userMsg); _allMessages.Add(missMsg); });

        var channel = Channel.CreateUnbounded<string>();

        string fullSpoken = "";
        Exception? streamError = null;

        _ = Task.Run(() =>
        {
            try
            {
                foreach (var token in PythonBridge.ChatStream(pySessionId, text, profile, background, _currentRole?.Tags))
                    channel.Writer.TryWrite(token);
            }
            catch (Exception ex) { streamError = ex; }
            finally { channel.Writer.Complete(); }
        });

        await foreach (var token in channel.Reader.ReadAllAsync())
        {
            if (token.StartsWith("data: "))
            {
                var json = token[6..];
                try
                {
                    var chunk = System.Text.Json.JsonSerializer.Deserialize<ChatResponse>(
                        json, new System.Text.Json.JsonSerializerOptions
                        { PropertyNameCaseInsensitive = true });
                    if (chunk?.Spoken != null)
                    {
                        fullSpoken = chunk.Spoken;
                        missMsg.Text = fullSpoken;
                        if (!string.IsNullOrEmpty(chunk.InnerThought))
                            missMsg.InnerThought = chunk.InnerThought;
                    }
                }
                catch { }
            }
            else
            {
                fullSpoken += token;
                missMsg.Text = fullSpoken;
            }
            yield return token;
        }

        if (streamError != null)
        {
            Trace.TraceError($"[SendMessageStream] {streamError}");
            DispatcherHelper.Run(() => { missMsg.Text = "流式生成失败，请稍后重试"; });
            yield break;
        }

        DispatcherHelper.Run(() =>
        {
            missMsg.TotalTokenCount = EstimateTokens(fullSpoken + (missMsg.InnerThought ?? ""));
            missMsg.SpokenTokenCount = EstimateTokens(fullSpoken);
        });
        DebouncedSaveSessions();
    }

    public List<ChatMessage> BuildContextMessages()
    {
        var roleName = _currentRole?.Name;

        var validHistory = _allMessages
            .Where(m => string.IsNullOrEmpty(roleName) || m.RoleName == roleName)
            .OrderBy(m => m.Timestamp)
            .ToList();

        int tokenCount = 0;
        var result = new List<ChatMessage>();
        for (int i = validHistory.Count - 1; i >= 0; i--)
        {
            var msg = validHistory[i];
            int msgTokens = msg.TotalTokenCount > 0
                ? msg.TotalTokenCount
                : EstimateTokens((msg.Text ?? "") + (msg.InnerThought ?? ""));
            if (tokenCount + msgTokens > MaxContextTokenLimit)
                break;
            tokenCount += msgTokens;
            result.Insert(0, msg);
        }

        return result;
    }

    private static int EstimateTokens(string text)
    {
        if (string.IsNullOrEmpty(text)) return 0;
        try { return _tokenizer.CountTokens(text); }
        catch { return text.Length / 2; }
    }

    #endregion

    public void Dispose()
    {
        _saveDebounceToken?.Cancel();
        _saveDebounceToken?.Dispose();
    }

    public static class DispatcherHelper
    {
        public static void Run(Action action)
        {
            if (Application.Current?.Dispatcher.CheckAccess() == true)
                action();
            else
                Application.Current?.Dispatcher.Invoke(action);
        }
    }
}
