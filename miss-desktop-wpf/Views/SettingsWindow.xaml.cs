// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System;
using System.Linq;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using MISS.Services;

namespace MISS.Views;

public partial class SettingsWindow : Window
{
    public SettingsWindow()
    {
        InitializeComponent();
        Loaded += (_, _) => LoadSettings();
    }

    private void LoadSettings()
    {
        var local = LocalStore.LoadSettings() ?? new SettingsData();

        // Try to get runtime settings from Python
        try
        {
            var remote = PythonBridge.GetSettings();
            if (remote.TryGetValue("openai_api_key_set", out var keySet) && keySet == "True")
            {
                if (local.openai_api_key == null)
                    local.openai_api_key = "••••••••"; // placeholder for already-configured key
            }
            if (remote.TryGetValue("openai_base_url", out var url) && !string.IsNullOrEmpty(url))
                local.openai_base_url = url;
            if (remote.TryGetValue("model", out var model) && !string.IsNullOrEmpty(model))
                local.model = model;
        }
        catch { }

        if (!string.IsNullOrEmpty(local.openai_api_key) && local.openai_api_key != "••••••••")
            ApiKeyInput.Password = local.openai_api_key;

        if (!string.IsNullOrEmpty(local.openai_base_url))
        {
            BaseUrlInput.Text = local.openai_base_url;
            // Auto-detect provider from URL
            var url = local.openai_base_url.ToLower();
            if (url.Contains("api.deepseek.com"))
                SetProvider("deepseek");
            else if (url.Contains("api.openai.com"))
                SetProvider("openai");
            else if (!string.IsNullOrEmpty(url))
                SetProvider("custom");
            else
                SetProvider("openai");
        }
        else
        {
            SetProvider("openai");
        }

        if (!string.IsNullOrEmpty(local.model))
        {
            foreach (ComboBoxItem item in ModelCombo.Items)
            {
                if (item.Tag?.ToString() == local.model)
                {
                    ModelCombo.SelectedItem = item;
                    return;
                }
            }
            ModelCombo.Text = local.model;
        }
    }

    private void SetProvider(string tag)
    {
        foreach (ComboBoxItem item in ProviderCombo.Items)
        {
            if (item.Tag?.ToString() == tag)
            {
                ProviderCombo.SelectedItem = item;
                return;
            }
        }
    }

    private void ProviderCombo_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (BaseUrlInput == null) return; // not yet loaded
        var item = ProviderCombo.SelectedItem as ComboBoxItem;
        var tag = item?.Tag?.ToString() ?? "openai";
        BaseUrlInput.Text = tag switch
        {
            "openai" => "https://api.openai.com/v1",
            "deepseek" => "https://api.deepseek.com/v1",
            _ => BaseUrlInput.Text, // keep current for openai-compat / custom
        };
    }

    private async void TestConnection_Click(object sender, RoutedEventArgs e)
    {
        var key = ApiKeyInput.Password.Trim();
        var baseUrl = BaseUrlInput.Text.Trim();

        if (string.IsNullOrEmpty(key))
        {
            StatusText.Text = "请输入 API Key";
            return;
        }

        StatusText.Text = "测试中...";
        IsEnabled = false;

        try
        {
            var settings = new SettingsData
            {
                openai_api_key = key,
                openai_base_url = baseUrl,
                model = "gpt-4o-mini",
            };
            PythonBridge.ApplySettings(settings);

            var (ok, message) = await Task.Run(() => PythonBridge.PingTest());
            StatusText.Text = message;
        }
        catch (Exception ex)
        {
            StatusText.Text = $"连接失败: {ex.Message}";
        }
        finally
        {
            IsEnabled = true;
        }
    }

    private void Save_Click(object sender, RoutedEventArgs e)
    {
        var modelItem = ModelCombo.SelectedItem as ComboBoxItem;
        var model = modelItem?.Tag?.ToString() ?? ModelCombo.Text.Trim();

        var settings = new SettingsData
        {
            openai_api_key = ApiKeyInput.Password.Trim(),
            openai_base_url = BaseUrlInput.Text.Trim(),
            model = string.IsNullOrEmpty(model) ? "gpt-4o-mini" : model,
        };

        LocalStore.SaveSettings(settings);
        PythonBridge.ApplySettings(settings);

        DialogResult = true;
        Close();
    }

    private void Cancel_Click(object sender, RoutedEventArgs e)
    {
        DialogResult = false;
        Close();
    }
}