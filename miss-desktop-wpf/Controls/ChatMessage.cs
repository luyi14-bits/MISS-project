// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using CommunityToolkit.Mvvm.ComponentModel;

namespace MISS.Controls;

public partial class ChatMessage : ObservableObject
{
    public ChatMessage() { }

    public int Id { get; set; }
    public string SessionId { get; set; } = "";
    public string Sender { get; set; } = "";
    public string RoleName { get; set; } = "";

    private string _text = "";
    public string Text
    {
        get => _text;
        set => SetProperty(ref _text, value);
    }

    private string? _innerThought;
    public string? InnerThought
    {
        get => _innerThought;
        set => SetProperty(ref _innerThought, value);
    }

    public bool IsUser { get; set; }

    private bool _isInnerVisible;
    public bool IsInnerVisible
    {
        get => _isInnerVisible;
        set => SetProperty(ref _isInnerVisible, value);
    }

    public DateTime Timestamp { get; set; } = DateTime.Now;

    public int SpokenTokenCount { get; set; }
    public int TotalTokenCount { get; set; }
}
