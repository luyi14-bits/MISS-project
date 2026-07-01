// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
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

    private async Task SendMessage()
    {
        var text = MessageInput.Text.Trim();
        if (string.IsNullOrEmpty(text)) return;
        MessageInput.Clear();
        await VM.SendMessage(text);
    }
}
