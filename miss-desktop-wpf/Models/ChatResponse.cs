// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace MISS.Models;

public class ChatResponse
{
    [JsonPropertyName("inner_thought")]
    public string InnerThought { get; set; } = "";

    [JsonPropertyName("spoken")]
    public string Spoken { get; set; } = "";

    [JsonPropertyName("intimacy_change")]
    public int IntimacyChange { get; set; }

    [JsonPropertyName("intimacy")]
    public int Intimacy { get; set; }

    [JsonPropertyName("intimacy_reason")]
    public string IntimacyReason { get; set; } = "";

    [JsonPropertyName("active_easter_eggs")]
    public List<string> ActiveEasterEggs { get; set; } = new();

    [JsonPropertyName("active_cross_effects")]
    public List<CrossEffect> ActiveCrossEffects { get; set; } = new();

    [JsonPropertyName("diag")]
    public Dictionary<string, object>? Diag { get; set; }
}

public class CrossEffect
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = "";

    [JsonPropertyName("persona_name")]
    public string PersonaName { get; set; } = "";

    [JsonPropertyName("type")]
    public string Type { get; set; } = "";
}
