// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System;
using System.Globalization;
using System.IO;
using System.Windows.Data;
using System.Windows.Media.Imaging;

namespace MISS.Views;

public class RoleAvatarConverter : IValueConverter
{
    private static readonly string BaseDir = AppContext.BaseDirectory;

    public object? Convert(object value, Type targetType, object parameter, CultureInfo culture)
    {
        var name = value as string;
        if (string.IsNullOrEmpty(name)) return null;

        var map = new Dictionary<string, string>
        {
            ["傲娇女友"] = "p-tsundere.jpg",
            ["知性姐姐"] = "p-intellectual.jpg",
            ["笨蛋⑨"] = "p-baka.jpg",
            ["冰山美人"] = "p-icequeen.jpg",
            ["病娇女友"] = "p-yandere.jpg",
            ["女王大人"] = "p-queen.jpg",
            ["小恶魔"] = "p-devil.jpg",
            ["天然呆"] = "p-airhead.jpg",
            ["元气少女"] = "p-genki.jpg",
            ["三无少女"] = "p-kuudere.jpg",
            ["中二病"] = "p-chuunibyou.jpg",
            ["邻家女孩"] = "p-neighbor.jpg",
        };

        if (!map.TryGetValue(name, out var filename)) return null;

        try
        {
            var path = Path.Combine(BaseDir, "Resources", "Images", filename);
            if (!File.Exists(path)) return null;
            var bmp = new BitmapImage();
            bmp.BeginInit();
            bmp.CacheOption = BitmapCacheOption.OnLoad;
            bmp.UriSource = new Uri(path);
            bmp.EndInit();
            bmp.Freeze();
            return bmp;
        }
        catch { return null; }
    }

    public object ConvertBack(object value, Type targetType, object parameter, CultureInfo culture)
        => throw new NotSupportedException();
}
