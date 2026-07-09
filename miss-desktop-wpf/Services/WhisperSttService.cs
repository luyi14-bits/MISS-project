// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using Whisper.net;
using Whisper.net.Ggml;

namespace MISS.Services;

/// <summary>
/// Speech-to-text service using Whisper.net (local inference, completely offline after model download).
/// Downloads ggml-tiny.bin (~75MB) on first use.
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
    /// Returns human-readable error message on failure, null on success.
    /// </summary>
    public async Task<string?> InitializeAsync()
    {
        if (_initialized) return null;

        try
        {
            Directory.CreateDirectory(_modelDir);

            if (!File.Exists(_modelPath))
            {
                Trace.TraceInformation("[WhisperSttService] 开始下载识别模型 ggml-tiny.bin (~75MB)...");
                var downloader = WhisperGgmlDownloader.Default;
                await using var modelStream = await downloader.GetGgmlModelAsync(GgmlType.Tiny);
                await using var fileWriter = File.Create(_modelPath);
                await modelStream.CopyToAsync(fileWriter);
                Trace.TraceInformation("[WhisperSttService] 模型下载完成");
            }

            _factory = WhisperFactory.FromPath(_modelPath);
            _processor = _factory.CreateBuilder()
                .WithLanguage("zh")
                .Build();

            _initialized = true;
            Trace.TraceInformation("[WhisperSttService] 语音识别引擎就绪");
            return null;
        }
        catch (Exception ex)
        {
            Trace.TraceError($"[WhisperSttService] 初始化失败: {ex.Message}");
            return $"语音模型初始化失败，请检查网络连接后重启应用。\n详情: {ex.Message}";
        }
    }

    /// <summary>
    /// Transcribe 16-bit 16kHz mono PCM WAV audio bytes to text.
    /// Call InitializeAsync() first.
    /// </summary>
    public async Task<string> TranscribeAsync(byte[] wavAudio)
    {
        if (!_initialized)
            throw new System.InvalidOperationException("WhisperSttService 未初始化，请先调用 InitializeAsync()");

        if (_processor == null) return "";

        var result = new System.Text.StringBuilder();

        try
        {
            await using var memoryStream = new MemoryStream(wavAudio);
            await foreach (var segment in _processor.ProcessAsync(memoryStream))
            {
                result.Append(segment.Text);
            }
        }
        catch (Exception ex)
        {
            Trace.TraceError($"[WhisperSttService] 转写失败: {ex.Message}");
            return $"[识别错误: {ex.Message}]";
        }

        return result.ToString().Trim();
    }

    public bool IsReady => _initialized;
    public long ModelFileSize => File.Exists(_modelPath) ? new FileInfo(_modelPath).Length : 0;
}
