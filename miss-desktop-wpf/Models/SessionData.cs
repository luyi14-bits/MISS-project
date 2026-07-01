// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using CommunityToolkit.Mvvm.ComponentModel;

namespace MISS.Models;

public partial class SessionData : ObservableObject
{
    public SessionData() { }

    public int Id { get; set; }

    private string _title = "新对话";
    public string Title
    {
        get => _title;
        set => SetProperty(ref _title, value);
    }

    private string _roleName = "";
    public string RoleName
    {
        get => _roleName;
        set => SetProperty(ref _roleName, value);
    }

    public DateTime CreatedAt { get; set; } = DateTime.Now;
}
