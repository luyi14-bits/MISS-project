// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.IO;
using System.Threading.Tasks;
using Whisper.net;

namespace MISS.Services;

/// <summary>
/// Speech-to-text service using Whisper.net (local inference, completely offline).
/// Downloads ggml-tiny.bin (~75MB) on first use to %APPDATA%/MISS/whisper/.
/// </summary>
public class WhisperSttService
{
    private readonly string _modelDir;
    private readonly string _modelPath;
    private WhisperFactory? _factory;
    private WhisperProcessor? _processor;
    private bool _initialized;

    public WhisperSttService()
    {
        _modelDir = Path.Combine(
            System.Environment.GetFolderPath(System.Environment.SpecialFolder.ApplicationData),
            "MISS", "whisper");
        _modelPath = Path.Combine(_modelDir, "ggml-tiny.bin");
    }

    /// <summary>
    /// Ensure the Whisper model is downloaded and the processor is initialized.
    /// </summary>
    public async Task InitializeAsync()
    {
        if (_initialized) return;

        Directory.CreateDirectory(_modelDir);

        if (!File.Exists(_modelPath))
        {
            // Download ggml-tiny.bin from HuggingFace
            var url = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin";
            using var httpClient = new System.Net.Http.HttpClient();
            httpClient.Timeout = System.TimeSpan.FromMinutes(5);
            var response = await httpClient.GetAsync(url);
            response.EnsureSuccessStatusCode();

            await using var fileStream = File.Create(_modelPath);
            await response.Content.CopyToAsync(fileStream);
        }

        _factory = WhisperFactory.FromPath(_modelPath);
        _processor = _factory.CreateBuilder()
            .WithLanguage("zh")
            .Build();

        _initialized = true;
    }

    /// <summary>
    /// Transcribe WAV audio bytes to text.
    /// Must call InitializeAsync() first.
    /// </summary>
    public async Task<string> TranscribeAsync(byte[] wavAudio)
    {
        if (!_initialized)
            throw new System.InvalidOperationException("WhisperSttService not initialized. Call InitializeAsync() first.");

        if (_processor == null)
            return "";

        var result = new System.Text.StringBuilder();

        await using var memoryStream = new MemoryStream(wavAudio);
        await foreach (var segment in _processor.ProcessAsync(memoryStream))
        {
            result.Append(segment.Text);
        }

        return result.ToString().Trim();
    }

    /// <summary>
    /// Whether the model is ready.
    /// </summary>
    public bool IsReady => _initialized;

    /// <summary>
    /// Model file size on disk, or 0 if not downloaded.
    /// </summary>
    public long ModelFileSize => File.Exists(_modelPath) ? new FileInfo(_modelPath).Length : 0;
}
