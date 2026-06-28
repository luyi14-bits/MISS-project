using System.IO;
using System.Text.Json;
using MISS.Controls;
using MISS.Models;

namespace MISS.Services;

public static class LocalStore
{
    private static ILocalStore? _backend;

    public static void SetBackend(ILocalStore backend) => _backend = backend;

    private static ILocalStore B => _backend ?? throw new InvalidOperationException("LocalStore backend not initialized");

    static LocalStore() => Directory.CreateDirectory(
        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MISS"));

    public static List<RoleData> LoadRoles() => B.LoadRoles();
    public static void SaveRoles(List<RoleData> roles) => B.SaveRoles(roles);
    public static void SaveRole(RoleData role) => B.SaveRole(role);
    public static void DeleteRole(string name) => B.DeleteRole(name);
    public static List<RoleData> GetBuiltinRoles() => B.GetBuiltinRoles();
    public static SettingsData? LoadSettings() => B.LoadSettings();
    public static void SaveSettings(SettingsData settings) => B.SaveSettings(settings);

    public static List<SessionData> LoadSessions() => B.LoadSessions();
    public static void SaveSessions(List<SessionData> sessions) => B.SaveSessions(sessions);
    public static List<ChatMessage> LoadMessages(int sessionId) => B.LoadMessages(sessionId);
    public static void SaveMessages(int sessionId, List<ChatMessage> messages) => B.SaveMessages(sessionId, messages);
    public static void DeleteMessages(int sessionId) => B.DeleteMessages(sessionId);
    public static void DeleteSession(int sessionId) => B.DeleteSession(sessionId);
}
