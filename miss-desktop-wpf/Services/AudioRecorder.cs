// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.IO;
using NAudio.Wave;

namespace MISS.Services;

/// <summary>
/// Push-to-talk microphone recorder. Press to record, release to get WAV bytes.
/// </summary>
public class AudioRecorder : IDisposable
{
    private WaveInEvent? _waveIn;
    private MemoryStream? _stream;
    private bool _isRecording;

    public event Action<byte[]>? OnRecordingFinished;

    /// <summary>
    /// Start recording from the default microphone.
    /// </summary>
    public void Start()
    {
        if (_isRecording) return;
        _isRecording = true;

        _stream = new MemoryStream();
        _waveIn = new WaveInEvent
        {
            WaveFormat = new WaveFormat(16000, 16, 1), // 16kHz 16-bit mono (Whisper input format)
            BufferMilliseconds = 100,
        };
        _waveIn.DataAvailable += OnDataAvailable;
        _waveIn.RecordingStopped += OnRecordingStopped;
        _waveIn.StartRecording();
    }

    /// <summary>
    /// Stop recording and invoke OnRecordingFinished with WAV bytes.
    /// </summary>
    public void Stop()
    {
        if (!_isRecording) return;
        _isRecording = false;
        _waveIn?.StopRecording();
    }

    private void OnDataAvailable(object? sender, WaveInEventArgs e)
    {
        _stream?.Write(e.Buffer, 0, e.BytesRecorded);
    }

    private void OnRecordingStopped(object? sender, StoppedEventArgs e)
    {
        if (_stream != null)
        {
            var wavBytes = CreateWavFile(_stream.ToArray());
            _stream.Dispose();
            _stream = null;
            OnRecordingFinished?.Invoke(wavBytes);
        }
        _waveIn?.Dispose();
        _waveIn = null;
    }

    /// <summary>
    /// Wraps raw PCM data in a proper WAV header.
    /// </summary>
    private static byte[] CreateWavFile(byte[] pcmData)
    {
        int sampleRate = 16000;
        int bitsPerSample = 16;
        int channels = 1;

        using var ms = new MemoryStream();
        using var writer = new BinaryWriter(ms);

        // RIFF header
        writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF"));
        writer.Write(36 + pcmData.Length);
        writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVE"));

        // fmt chunk
        writer.Write(System.Text.Encoding.ASCII.GetBytes("fmt "));
        writer.Write(16); // chunk size
        writer.Write((short)1); // PCM
        writer.Write((short)channels);
        writer.Write(sampleRate);
        writer.Write(sampleRate * channels * bitsPerSample / 8);
        writer.Write((short)(channels * bitsPerSample / 8));
        writer.Write((short)bitsPerSample);

        // data chunk
        writer.Write(System.Text.Encoding.ASCII.GetBytes("data"));
        writer.Write(pcmData.Length);
        writer.Write(pcmData);

        return ms.ToArray();
    }

    public void Dispose()
    {
        Stop();
        _waveIn?.Dispose();
        _stream?.Dispose();
    }
}
