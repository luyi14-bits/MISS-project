// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.IO;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace MISS.Services;

/// <summary>
/// SillyTavern / TavernAI Character Card V3 format (embedded in PNG tEXt chunk "ccv3").
/// </summary>
public class TavernCardV3
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("personality")]
    public string Personality { get; set; } = "";

    [JsonPropertyName("scenario")]
    public string Scenario { get; set; } = "";

    [JsonPropertyName("first_mes")]
    public string FirstMes { get; set; } = "";

    [JsonPropertyName("mes_example")]
    public string MesExample { get; set; } = "";

    [JsonPropertyName("creator_notes")]
    public string CreatorNotes { get; set; } = "";

    [JsonPropertyName("system_prompt")]
    public string SystemPrompt { get; set; } = "";

    [JsonPropertyName("post_history_instructions")]
    public string PostHistoryInstructions { get; set; } = "";

    [JsonPropertyName("alternate_greetings")]
    public List<string> AlternateGreetings { get; set; } = new();

    [JsonPropertyName("tags")]
    public List<string> Tags { get; set; } = new();

    [JsonPropertyName("creator")]
    public string Creator { get; set; } = "";

    [JsonPropertyName("character_version")]
    public string CharacterVersion { get; set; } = "";

    [JsonPropertyName("extensions")]
    public Dictionary<string, JsonElement> Extensions { get; set; } = new();

    [JsonPropertyName("avatar")]
    public string Avatar { get; set; } = "";
}

/// <summary>
/// Parses TavernAI V3 character cards from PNG files by extracting the "ccv3" tEXt chunk.
/// </summary>
public static class TavernCardParser
{
    private static readonly byte[] PngSignature = { 137, 80, 78, 71, 13, 10, 26, 10 };
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        PropertyNameCaseInsensitive = true,
    };

    /// <summary>
    /// Parse a SillyTavern V3 character card from a PNG file.
    /// Returns null if the file is not a valid TavernAI card.
    /// </summary>
    public static TavernCardV3? ParseFromPng(string pngPath)
    {
        if (!File.Exists(pngPath))
            return null;

        var data = File.ReadAllBytes(pngPath);
        if (data.Length < 8)
            return null;

        // Validate PNG signature
        for (int i = 0; i < 8; i++)
        {
            if (data[i] != PngSignature[i])
                return null;
        }

        int offset = 8;

        // Walk PNG chunks to find tEXt "ccv3"
        while (offset + 12 <= data.Length)
        {
            // Read chunk length (big-endian)
            int chunkLen = (data[offset] << 24) | (data[offset + 1] << 16)
                         | (data[offset + 2] << 8) | data[offset + 3];
            offset += 4;

            // Read chunk type (4 bytes)
            if (offset + 4 > data.Length) break;
            string chunkType = Encoding.ASCII.GetString(data, offset, 4);
            offset += 4;

            // Read chunk data
            if (offset + chunkLen > data.Length) break;

            if (chunkType == "tEXt" && chunkLen > 0)
            {
                // tEXt format: keyword (null-terminated) + text
                int nullPos = offset;
                int maxSearch = Math.Min(offset + chunkLen, data.Length);
                while (nullPos < maxSearch && data[nullPos] != 0)
                    nullPos++;

                if (nullPos < maxSearch)
                {
                    int keywordLen = nullPos - offset;
                    string keyword = Encoding.Latin1.GetString(data, offset, keywordLen);

                    if (keyword == "ccv3")
                    {
                        int textStart = nullPos + 1;
                        int textLen = chunkLen - keywordLen - 1;
                        if (textLen > 0 && textStart + textLen <= data.Length)
                        {
                            string base64Json = Encoding.Latin1.GetString(data, textStart, textLen);
                            return ParseFromBase64(base64Json);
                        }
                    }
                }
            }

            // Skip CRC
            offset += chunkLen + 4;
        }

        return null;
    }

    /// <summary>
    /// Parse TavernAI card JSON from a base64 string (for testing or non-PNG sources).
    /// </summary>
    public static TavernCardV3? ParseFromBase64(string base64Json)
    {
        try
        {
            byte[] jsonBytes = Convert.FromBase64String(base64Json.Trim());
            string json = Encoding.UTF8.GetString(jsonBytes);
            return JsonSerializer.Deserialize<TavernCardV3>(json, JsonOpts);
        }
        catch
        {
            return null;
        }
    }
}
