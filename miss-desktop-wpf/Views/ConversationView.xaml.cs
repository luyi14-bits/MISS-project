// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
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
