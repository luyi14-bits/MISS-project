// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.IO;
using System.Windows;
using System.Windows.Media.Imaging;
using Microsoft.Win32;
using MISS.Models;
using MISS.Services;

namespace MISS.Views;

public partial class CreateRoleWindow : Window
{
    public RoleData? CreatedRole { get; private set; }
    private string _avatarPath = "";

    public CreateRoleWindow()
    {
        InitializeComponent();
        LoadDefaultAvatar();
    }

    private void LoadDefaultAvatar()
    {
        var path = Path.Combine(AppContext.BaseDirectory, "Resources", "Images", "avatar-miss-default.jpg");
        if (File.Exists(path))
        {
            try
            {
                var bmp = new BitmapImage();
                bmp.BeginInit();
                bmp.CacheOption = BitmapCacheOption.OnLoad;
                bmp.UriSource = new Uri(path);
                bmp.EndInit();
                bmp.Freeze();
                AvatarImage.Source = bmp;
            }
            catch { }
        }
    }

    private void PickAvatar_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Filter = "图片文件 (*.jpg;*.jpeg;*.png)|*.jpg;*.jpeg;*.png",
            Title = "选择角色头像",
        };
        if (dialog.ShowDialog() == true)
        {
            _avatarPath = dialog.FileName;
            AvatarPathText.Text = System.IO.Path.GetFileName(_avatarPath);
            try
            {
                AvatarImage.Source = new BitmapImage(new Uri(_avatarPath));
            }
            catch { }
        }
    }

    private async void Create_Click(object sender, RoutedEventArgs e)
    {
        var name = NameInput.Text.Trim();
        var desc = DescInput.Text.Trim();
        if (string.IsNullOrEmpty(name)) { NotificationService.Error("请输入角色名称"); return; }
        if (string.IsNullOrEmpty(desc)) { NotificationService.Error("请输入角色描述"); return; }

        StatusText.Text = "正在分析角色属性...";
        IsEnabled = false;

        try
        {
            var profile = new MISSProfile();
            var attrs = await Task.Run(() => PythonBridge.AnalyzeCharacter(desc));
            foreach (var kv in attrs)
                profile[kv.Key] = kv.Value;

            var bg = BgInput.Text.Trim();
            CreatedRole = new RoleData
            {
                Name = name,
                Description = desc,
                Background = bg,
                Profile = profile,
                AvatarPath = _avatarPath,
            };

            DialogResult = true;
            Close();
        }
        catch (Exception ex)
        {
            StatusText.Text = "";
            IsEnabled = true;
            NotificationService.Error($"生成失败：{ex.Message}");
        }
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}
