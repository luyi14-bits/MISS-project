// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Windows;

namespace MISS.Services;

public static class NotificationService
{
    public static void Info(string message) =>
        MessageBox.Show(message, "MISS", MessageBoxButton.OK, MessageBoxImage.Information);

    public static bool Confirm(string message) =>
        MessageBox.Show(message, "确认", MessageBoxButton.YesNo, MessageBoxImage.Warning) == MessageBoxResult.Yes;

    public static void Error(string message) =>
        MessageBox.Show(message, "错误", MessageBoxButton.OK, MessageBoxImage.Error);
}
