// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using Microsoft.Win32;
using MISS.Services;
using MISS.ViewModels;

namespace MISS.Views;

public partial class ConversationView : UserControl
{
    private MainViewModel VM => MainViewModel.Instance;
    private readonly AudioRecorder _audioRecorder = new();
    private readonly WhisperSttService _whisperStt = new();

    public ConversationView()
    {
        InitializeComponent();
        DataContext = VM;
    }

    private async void SendButton_Click(object sender, RoutedEventArgs e) => await SendMessage();

    private async void PlayTts_Click(object sender, RoutedEventArgs e)
    {
        if (sender is Button btn && btn.Tag is string text && !string.IsNullOrEmpty(text))
        {
            var voice = VM.CurrentRole?.VoicePreset;
            if (string.IsNullOrEmpty(voice)) voice = "zh-CN-XiaoxiaoNeural";
            btn.IsEnabled = false;
            try
            {
                var mp3 = await Task.Run(() => PythonBridge.TtsSpeak(text, voice));
                if (mp3.Length > 0)
                    await AudioPlayer.PlayAsync(mp3);
            }
            catch { }
            finally { btn.IsEnabled = true; }
        }
    }

    private void MessageInput_KeyDown(object sender, KeyEventArgs e)
    {
        if (e.Key == Key.Enter && Keyboard.Modifiers == ModifierKeys.None)
        {
            e.Handled = true;
            _ = SendMessage();
        }
    }

    private void OpenSettings_Click(object sender, RoutedEventArgs e)
    {
        var parent = Window.GetWindow(this);
        if (parent is MainWindow mw)
            mw.OpenSettings();
    }

    private void ExportConversation_Click(object sender, RoutedEventArgs e)
    {
        var vm = MainViewModel.Instance;
        if (vm.CurrentSession == null) return;

        var dialog = new SaveFileDialog
        {
            Filter = "HTML 文件 (*.html)|*.html|JSON 文件 (*.json)|*.json|Markdown 文件 (*.md)|*.md",
            FileName = $"对话_{vm.CurrentSession.Title}_{DateTime.Now:yyyyMMdd}.html",
            Title = "导出对话",
        };
        if (dialog.ShowDialog() != true) return;

        try
        {
            var messages = vm.Messages.ToList();
            if (messages.Count == 0) { NotificationService.Info("当前对话无消息"); return; }

            string ext = System.IO.Path.GetExtension(dialog.FileName).ToLower();
            switch (ext)
            {
                case ".json":
                    ConversationExporter.ExportToJson(messages, vm.CurrentSession, dialog.FileName);
                    break;
                case ".md":
                    ConversationExporter.ExportToMarkdown(messages, vm.CurrentSession, vm.CurrentRole, dialog.FileName);
                    break;
                default:
                    ConversationExporter.ExportToHtml(messages, vm.CurrentSession, vm.CurrentRole, dialog.FileName);
                    break;
            }
            NotificationService.Info($"已导出：{System.IO.Path.GetFileName(dialog.FileName)}");
        }
        catch (Exception ex)
        {
            NotificationService.Error($"导出失败：{ex.Message}");
        }
    }

    private void SttButton_PreviewMouseDown(object sender, MouseButtonEventArgs e)
    {
        SttButton.Content = "🔴";
        SttButton.FontSize = 14;
        SttButton.ToolTip = "录音中... 松开结束";
        _audioRecorder.OnRecordingFinished += OnSttFinished;
        _audioRecorder.Start();
    }

    private void SttButton_PreviewMouseUp(object sender, MouseButtonEventArgs e)
    {
        _audioRecorder.Stop();
        SttButton.Content = "🎤";
        SttButton.FontSize = 16;
        SttButton.ToolTip = "按住说话 (语音输入)";
    }

    private async void OnSttFinished(byte[] wavAudio)
    {
        _audioRecorder.OnRecordingFinished -= OnSttFinished;

        if (wavAudio.Length == 0) return;

        SttButton.IsEnabled = false;
        SttButton.Content = "⋯";
        SttButton.ToolTip = "识别中...";

        try
        {
            // 模型初始化（可能会下载 ~75MB，在后台线程执行）
            string? initError = null;
            if (!_whisperStt.IsReady)
            {
                SttButton.Content = "↓";
                SttButton.ToolTip = "下载模型...";
                initError = await Task.Run(() => _whisperStt.InitializeAsync());
            }

            await Dispatcher.InvokeAsync(() =>
            {
                if (initError != null)
                {
                    NotificationService.Error(initError);
                    return;
                }

                _ = TranscribeAndFillAsync(wavAudio);
            });
        }
        catch (Exception ex)
        {
            await Dispatcher.InvokeAsync(() =>
                NotificationService.Error($"语音识别失败：{ex.Message}"));
        }
        finally
        {
            await Dispatcher.InvokeAsync(() =>
            {
                SttButton.IsEnabled = true;
                SttButton.Content = "🎤";
                SttButton.FontSize = 16;
                SttButton.ToolTip = "按住说话 (语音输入)";
            });
        }
    }

    private async Task TranscribeAndFillAsync(byte[] wavAudio)
    {
        try
        {
            string text = await Task.Run(() => _whisperStt.TranscribeAsync(wavAudio));
            await Dispatcher.InvokeAsync(() =>
            {
                if (!string.IsNullOrEmpty(text) && !text.StartsWith("[识别错误"))
                {
                    MessageInput.Text = text;
                    MessageInput.CaretIndex = text.Length;
                }
                else if (text.StartsWith("[识别错误"))
                {
                    NotificationService.Error(text);
                }
            });
        }
        catch (Exception ex)
        {
            Trace.TraceError($"[STT] 转写异常: {ex}");
            await Dispatcher.InvokeAsync(() =>
                NotificationService.Error($"语音识别失败：{ex.Message}"));
        }
    }

    private async Task SendMessage()
    {
        var text = MessageInput.Text.Trim();
        if (string.IsNullOrEmpty(text)) return;
        MessageInput.Clear();
        await VM.SendMessage(text);
    }
}
