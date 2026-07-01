// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using NAudio.Wave;
using System;
using System.IO;
using System.Threading.Tasks;

namespace MISS.Services;

public static class AudioPlayer
{
    private static WaveOutEvent? _output;
    private static MemoryStream? _stream;
    private static WaveStream? _reader;
    private static readonly object _lock = new();

    public static bool IsPlaying
    {
        get { lock (_lock) return _output?.PlaybackState == PlaybackState.Playing; }
    }

    public static async Task PlayAsync(byte[] mp3Data)
    {
        if (mp3Data == null || mp3Data.Length == 0) return;
        await Task.Run(() =>
        {
            lock (_lock)
            {
                StopInternal();
                _stream = new MemoryStream(mp3Data);
                _reader = new Mp3FileReader(_stream);
                _output = new WaveOutEvent();
                _output.PlaybackStopped += (s, e) => Cleanup();
                _output.Init(_reader);
                _output.Play();
            }
        });
    }

    public static void Stop()
    {
        lock (_lock) StopInternal();
    }

    private static void StopInternal()
    {
        _output?.Stop();
        Cleanup();
    }

    private static void Cleanup()
    {
        _output?.Dispose();
        _output = null;
        _reader?.Dispose();
        _reader = null;
        _stream?.Dispose();
        _stream = null;
    }
}
