// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Text.Json.Serialization;

namespace MISS.Models;

public class RoleData
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = Guid.NewGuid().ToString("N")[..8];

    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("background")]
    public string Background { get; set; } = "";

    [JsonPropertyName("profile")]
    public MISSProfile Profile { get; set; } = new();

    [JsonPropertyName("avatar_path")]
    public string AvatarPath { get; set; } = "";

    [JsonPropertyName("tags")]
    public List<string> Tags { get; set; } = new();

    [JsonPropertyName("voice_preset")]
    public string VoicePreset { get; set; } = "";

    [JsonPropertyName("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.Now;

    // SillyTavern / TavernAI 角色卡兼容字段
    [JsonPropertyName("tavern_description")]
    public string TavernDescription { get; set; } = "";

    [JsonPropertyName("tavern_personality")]
    public string TavernPersonality { get; set; } = "";

    [JsonPropertyName("tavern_scenario")]
    public string TavernScenario { get; set; } = "";

    [JsonPropertyName("tavern_first_message")]
    public string TavernFirstMessage { get; set; } = "";

    [JsonPropertyName("tavern_creator")]
    public string TavernCreator { get; set; } = "";

    [JsonPropertyName("tavern_character_version")]
    public string TavernCharacterVersion { get; set; } = "";
}
