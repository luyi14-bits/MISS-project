// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Linq;
using System.IO;
using System.Text.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using Microsoft.Win32;
using MISS.Models;
using MISS.Services;
using MISS.ViewModels;

namespace MISS.Views;

public partial class RoleSidebar : UserControl
{
    private MainViewModel VM => MainViewModel.Instance;
    private bool _isCollapsed;

    public RoleSidebar()
    {
        InitializeComponent();
        DataContext = VM;
    }

    public void Refresh()
    {
        VM.Initialize();
    }

    private void CreateRole_Click(object sender, RoutedEventArgs e)
    {
        var win = new CreateRoleWindow();
        win.Owner = Window.GetWindow(this);
        if (win.ShowDialog() == true && win.CreatedRole != null)
        {
            LocalStore.SaveRole(win.CreatedRole);
            VM.Roles.Add(win.CreatedRole);
        }
    }

    private async void ExportRole_Click(object sender, RoutedEventArgs e)
    {
        if (VM.CurrentRole is not RoleData role) return;
        var dialog = new SaveFileDialog
        {
            Filter = "JSON files (*.json)|*.json",
            FileName = $"miss_role_{role.Name}.json",
        };
        if (dialog.ShowDialog() != true) return;

        var json = JsonSerializer.Serialize(role, new JsonSerializerOptions
        {
            WriteIndented = true,
            PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        });
        await Task.Run(() => File.WriteAllText(dialog.FileName, json));
        NotificationService.Info("已导出");
    }

    private async void ImportRole_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Filter = "JSON files (*.json)|*.json" };
        if (dialog.ShowDialog() != true) return;

        try
        {
            var json = await Task.Run(() => File.ReadAllText(dialog.FileName));
            var role = JsonSerializer.Deserialize<RoleData>(json, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
            });
            if (role?.Name == null) { NotificationService.Error("JSON 格式无效"); return; }

            LocalStore.SaveRole(role);
            VM.Roles.Add(role);
            NotificationService.Info($"已导入：{role.Name}");
        }
        catch (Exception ex)
        {
            NotificationService.Error(ex.Message);
        }
    }

    private void ExportTavernCard_Click(object sender, RoutedEventArgs e)
    {
        if (VM.CurrentRole is not RoleData role) return;
        var dialog = new SaveFileDialog
        {
            Filter = "SillyTavern 角色卡 (*.png)|*.png",
            FileName = $"{role.Name}_ST.png",
            Title = "导出为 SillyTavern 角色卡",
        };
        if (dialog.ShowDialog() != true) return;

        try
        {
            TavernCardExporter.ExportToPng(role, dialog.FileName);
            NotificationService.Info($"已导出 ST 角色卡：{role.Name}");
        }
        catch (Exception ex)
        {
            NotificationService.Error($"导出失败：{ex.Message}");
        }
    }

    private void AddToRoom_Click(object sender, RoutedEventArgs e)
    {
        if (VM.CurrentRole is not RoleData role) return;
        if (VM.RoomRoles.Any(r => r.Name == role.Name))
        {
            NotificationService.Info($"「{role.Name}」已在房间中");
            return;
        }
        VM.AddRoleToRoom(role);
        NotificationService.Info($"「{role.Name}」已加入房间");
    }

    private void DeleteRole_Click(object sender, RoutedEventArgs e)
    {
        if (VM.CurrentRole is not RoleData role) return;
        if (!NotificationService.Confirm($"确定要删除角色「{role.Name}」吗？此操作不可撤销。")) return;
        LocalStore.DeleteRole(role.Name);
        VM.Roles.Remove(role);
    }

    private void ToggleCollapse_Click(object sender, RoutedEventArgs e)
    {
        _isCollapsed = !_isCollapsed;
        VM.IsPanelCollapsed = _isCollapsed;
        Width = _isCollapsed ? 38 : 200;
        SessionListBox.Visibility = _isCollapsed ? Visibility.Collapsed : Visibility.Visible;
        RoleListBox.Visibility = _isCollapsed ? Visibility.Collapsed : Visibility.Visible;
        if (sender is Button btn)
            btn.Content = _isCollapsed ? "»" : "«";
    }
}
