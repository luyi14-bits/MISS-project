// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Text.Json.Serialization;

namespace MISS.Services;

public class SettingsData
{
    [JsonPropertyName("openai_api_key")]
    public string? openai_api_key { get; set; }

    [JsonPropertyName("openai_base_url")]
    public string? openai_base_url { get; set; }

    [JsonPropertyName("model")]
    public string? model { get; set; }
}
