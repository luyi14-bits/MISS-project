// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
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

    private async Task SendMessage()
    {
        var text = MessageInput.Text.Trim();
        if (string.IsNullOrEmpty(text)) return;
        MessageInput.Clear();
        await VM.SendMessage(text);
    }
}
