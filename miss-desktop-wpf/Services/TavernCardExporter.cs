// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.IO;
using System.Text;
using System.Text.Json;
using MISS.Models;

namespace MISS.Services;

/// <summary>
/// Exports MISS RoleData to SillyTavern / TavernAI V3 character card PNG files.
/// </summary>
public static class TavernCardExporter
{
    private static readonly JsonSerializerOptions JsonOpts = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower,
        WriteIndented = false,
    };

    private static readonly uint[] Crc32Table = BuildCrc32Table();

    private static uint[] BuildCrc32Table()
    {
        var table = new uint[256];
        for (uint i = 0; i < 256; i++)
        {
            uint crc = i;
            for (int j = 0; j < 8; j++)
                crc = (crc & 1) != 0 ? (0xEDB88320 ^ (crc >> 1)) : (crc >> 1);
            table[i] = crc;
        }
        return table;
    }

    private static uint Crc32(byte[] data)
    {
        uint crc = 0xFFFFFFFF;
        foreach (byte b in data)
            crc = Crc32Table[(crc ^ b) & 0xFF] ^ (crc >> 8);
        return crc ^ 0xFFFFFFFF;
    }

    /// <summary>
    /// Export a MISS RoleData to a SillyTavern V3 character card PNG file.
    /// </summary>
    public static void ExportToPng(RoleData role, string outputPath)
    {
        var card = MapToTavernCard(role);
        string json = JsonSerializer.Serialize(card, JsonOpts);
        string base64Json = Convert.ToBase64String(Encoding.UTF8.GetBytes(json));

        byte[] png = BuildPngWithTextChunk("ccv3", base64Json);
        File.WriteAllBytes(outputPath, png);
    }

    private static TavernCardV3 MapToTavernCard(RoleData role)
    {
        var card = new TavernCardV3
        {
            Name = role.Name,
            Description = !string.IsNullOrEmpty(role.TavernDescription)
                ? role.TavernDescription
                : role.Description,
            Personality = role.TavernPersonality,
            Scenario = !string.IsNullOrEmpty(role.TavernScenario)
                ? role.TavernScenario
                : role.Background,
            FirstMes = role.TavernFirstMessage,
            Creator = role.TavernCreator,
            CharacterVersion = role.TavernCharacterVersion,
        };

        card.Tags = new List<string>(role.Tags);

        return card;
    }

    private static byte[] BuildPngWithTextChunk(string keyword, string textValue)
    {
        using var ms = new MemoryStream();

        // PNG signature
        ms.Write(new byte[] { 137, 80, 78, 71, 13, 10, 26, 10 }, 0, 8);

        // IHDR chunk: 1x1, 8-bit RGB
        var ihdrData = new byte[13];
        WriteBigEndian(ihdrData, 0, 1);
        WriteBigEndian(ihdrData, 4, 1);
        ihdrData[8] = 8;
        ihdrData[9] = 2;
        ihdrData[10] = 0;
        ihdrData[11] = 0;
        ihdrData[12] = 0;
        WriteChunk(ms, "IHDR", ihdrData);

        // IDAT chunk: minimal 1x1 RGB pixel (zlib compressed)
        byte[] idatData =
        [
            0x78, 0x01,
            0x62, 0x60, 0x60, 0x60, 0x00, 0x02, 0x00,
            0x00, 0x00, 0xff, 0xff,
        ];
        WriteChunk(ms, "IDAT", idatData);

        // tEXt chunk: keyword + text
        byte[] textBytes = Encoding.Latin1.GetBytes(keyword + "\0" + textValue);
        WriteChunk(ms, "tEXt", textBytes);

        // IEND chunk
        WriteChunk(ms, "IEND", []);

        return ms.ToArray();
    }

    private static void WriteBigEndian(byte[] buffer, int offset, uint value)
    {
        buffer[offset]     = (byte)((value >> 24) & 0xFF);
        buffer[offset + 1] = (byte)((value >> 16) & 0xFF);
        buffer[offset + 2] = (byte)((value >> 8) & 0xFF);
        buffer[offset + 3] = (byte)(value & 0xFF);
    }

    private static void WriteChunk(MemoryStream ms, string type, byte[] data)
    {
        byte[] lenBytes = new byte[4];
        WriteBigEndian(lenBytes, 0, (uint)data.Length);
        ms.Write(lenBytes, 0, 4);

        byte[] typeBytes = Encoding.ASCII.GetBytes(type);
        ms.Write(typeBytes, 0, 4);
        ms.Write(data, 0, data.Length);

        byte[] crcInput = new byte[4 + data.Length];
        Buffer.BlockCopy(typeBytes, 0, crcInput, 0, 4);
        Buffer.BlockCopy(data, 0, crcInput, 4, data.Length);
        uint crcValue = Crc32(crcInput);

        byte[] crcBytes = new byte[4];
        WriteBigEndian(crcBytes, 0, crcValue);
        ms.Write(crcBytes, 0, 4);
    }
}
