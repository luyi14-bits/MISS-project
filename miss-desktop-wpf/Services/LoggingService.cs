// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System;
using System.IO;

namespace MISS.Services;

public static class LoggingService
{
    private static readonly string LogPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MISS", "miss.log");

    private static readonly object _lock = new();

    static LoggingService()
    {
        var dir = Path.GetDirectoryName(LogPath);
        if (dir != null) Directory.CreateDirectory(dir);
    }

    public static void Info(string message) => Write("INFO", message);
    public static void Error(string message, Exception? ex = null) => Write("ERROR", $"{message}{(ex != null ? " | " + ex : "")}");
    public static void Debug(string message) => Write("DEBUG", message);

    private static void Write(string level, string message)
    {
        var line = $"{DateTime.Now:yyyy-MM-dd HH:mm:ss.fff} [{level}] {message}";
        lock (_lock)
        {
            File.AppendAllText(LogPath, line + Environment.NewLine);
        }
        // Also output to debug trace (captured by Process Monitor / VS output)
        System.Diagnostics.Trace.WriteLine($"[MISS:{level}] {message}");
    }
}
