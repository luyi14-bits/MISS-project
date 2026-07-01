// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Windows;
using System.Windows.Controls;
using MISS.ViewModels;

namespace MISS.Views;

public partial class AttributePanel : UserControl
{
    public AttributePanel()
    {
        InitializeComponent();
    }

    public void ShowIntimacyChange(int value, int change)
    {
        IntimacyChangeText.Text = change > 0 ? $"+{change}" : $"{change}";
    }

    private void EducationLevel_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        MainViewModel.Instance.IsCirnoMode = (int)e.NewValue == -100;
    }
}
