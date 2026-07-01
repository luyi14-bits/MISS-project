// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Windows;
using MISS.Views;
using MISS.ViewModels;

namespace MISS;

public partial class MainWindow : Window
{
    public MainWindow()
    {
        InitializeComponent();
        DataContext = MainViewModel.Instance;
    }

    public void OpenSettings()
    {
        new SettingsWindow { Owner = this }.ShowDialog();
    }
}
