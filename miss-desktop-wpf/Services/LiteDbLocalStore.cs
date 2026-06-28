using System.IO;
using System.Diagnostics;
using LiteDB;
using MISS.Controls;
using MISS.Models;

namespace MISS.Services;

public class LiteDbLocalStore : ILocalStore, IDisposable
{
    private readonly string _dbPath;
    private LiteDatabase? _db;

    private LiteDatabase Db => _db ??= OpenDb();

    public LiteDbLocalStore()
    {
        var appData = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MISS");
        Directory.CreateDirectory(appData);
        _dbPath = Path.Combine(appData, "miss.db");
    }

    private LiteDatabase OpenDb()
    {
        var db = new LiteDatabase($"Filename={_dbPath};Connection=direct");
        return db;
    }

    public void Dispose()
    {
        _db?.Dispose();
        _db = null;
    }

    #region Sessions

    public List<SessionData> LoadSessions()
    {
        var col = Db.GetCollection<SessionData>("sessions");
        col.EnsureIndex(x => x.Id, true);
        return col.FindAll().OrderByDescending(x => x.CreatedAt).ToList();
    }

    public void SaveSessions(List<SessionData> sessions)
    {
        var col = Db.GetCollection<SessionData>("sessions");
        col.Upsert(sessions);
    }

    public void DeleteSession(int sessionId)
    {
        var col = Db.GetCollection<SessionData>("sessions");
        col.DeleteMany(s => s.Id == sessionId);
    }

    #endregion

    #region Messages

    public List<ChatMessage> LoadMessages(int sessionId)
    {
        var col = Db.GetCollection<ChatMessage>("messages");
        var messages = col.Find(m => m.SessionId == $"sess_{sessionId}")
                          .OrderBy(m => m.Timestamp)
                          .ToList();

        foreach (var msg in messages)
        {
            try
            {
                if (!string.IsNullOrEmpty(msg.Text))
                    msg.Text = PythonBridge.DecryptMessage(msg.Text);
                if (!string.IsNullOrEmpty(msg.InnerThought))
                    msg.InnerThought = PythonBridge.DecryptMessage(msg.InnerThought);
            }
            catch (Exception ex)
            {
                Trace.TraceError($"[LiteDB] DecryptMessage failed: {ex.Message}");
            }
        }

        return messages;
    }

    public void SaveMessages(int sessionId, List<ChatMessage> messages)
    {
        var col = Db.GetCollection<ChatMessage>("messages");
        col.DeleteMany(m => m.SessionId == $"sess_{sessionId}");
        if (messages.Count == 0) return;

        var copied = new List<ChatMessage>();
        foreach (var msg in messages)
        {
            var clone = new ChatMessage
            {
                Id = msg.Id,
                SessionId = msg.SessionId,
                Sender = msg.Sender,
                RoleName = msg.RoleName,
                IsUser = msg.IsUser,
                IsInnerVisible = msg.IsInnerVisible,
                Timestamp = msg.Timestamp,
                TotalTokenCount = msg.TotalTokenCount,
                SpokenTokenCount = msg.SpokenTokenCount,
                Text = EncryptIfNotEmpty(msg.Text),
                InnerThought = EncryptIfNotEmpty(msg.InnerThought),
            };
            copied.Add(clone);
        }
        col.InsertBulk(copied);
    }

    private static string EncryptIfNotEmpty(string text)
    {
        if (string.IsNullOrEmpty(text)) return text;
        try { return PythonBridge.EncryptMessage(text); }
        catch (Exception ex)
        {
            Trace.TraceError($"[LiteDB] EncryptMessage failed: {ex.Message}");
            return text;
        }
    }

    public void DeleteMessages(int sessionId)
    {
        var col = Db.GetCollection<ChatMessage>("messages");
        col.DeleteMany(m => m.SessionId == $"sess_{sessionId}");
    }

    #endregion

    #region Roles (kept as JSON for backward compat)

    private static readonly string AppDataDir = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "MISS");
    private static readonly string RolesPath = Path.Combine(AppDataDir, "roles.json");
    private static readonly string SettingsPath = Path.Combine(AppDataDir, "settings.json");

    private static readonly System.Text.Json.JsonSerializerOptions JsonOpts = new()
    {
        WriteIndented = true,
        PropertyNamingPolicy = System.Text.Json.JsonNamingPolicy.SnakeCaseLower,
    };

    public List<RoleData> LoadRoles()
    {
        if (!File.Exists(RolesPath)) return new();
        try
        {
            var json = File.ReadAllText(RolesPath);
            return System.Text.Json.JsonSerializer.Deserialize<List<RoleData>>(json, JsonOpts) ?? new();
        }
        catch { return new(); }
    }

    public void SaveRoles(List<RoleData> roles)
    {
        var json = System.Text.Json.JsonSerializer.Serialize(roles, JsonOpts);
        File.WriteAllText(RolesPath, json);
    }

    public void SaveRole(RoleData role)
    {
        var roles = LoadRoles();
        var idx = roles.FindIndex(r => r.Name == role.Name);
        if (idx >= 0) roles[idx] = role;
        else roles.Add(role);
        SaveRoles(roles);
    }

    public void DeleteRole(string name)
    {
        var roles = LoadRoles();
        roles.RemoveAll(r => r.Name == name);
        SaveRoles(roles);
    }

    public List<RoleData> GetBuiltinRoles()
    {
        return new List<RoleData>
        {
            new() { Name = "傲娇女友", Profile = new MISSProfile { IndependentSubmissive = -100, Intimacy = 100, Aggression = 40, RationalEmotional = 60 } },
            new() { Name = "知性姐姐", Profile = new MISSProfile { EducationLevel = 90, Curiosity = 80, Humor = 40, Aggression = -50, SocialEnergy = 30 } },
            new() { Name = "笨蛋⑨", Profile = new MISSProfile { EducationLevel = -100, Curiosity = 100, Humor = 60, SocialEnergy = 30 } },
            new() { Name = "冰山美人", Profile = new MISSProfile { RationalEmotional = -100, Aggression = -100, IndependentSubmissive = -100, SocialEnergy = -100 } },
            new() { Name = "病娇女友", Profile = new MISSProfile { Aggression = 80, Intimacy = 100, RationalEmotional = 60 } },
            new() { Name = "女王大人", Profile = new MISSProfile { IndependentSubmissive = -100, Willpower = 100, Aggression = 40 } },
            new() { Name = "小恶魔", Profile = new MISSProfile { Humor = 80, SocialEnergy = 80, Adventurousness = 60 } },
            new() { Name = "天然呆", Profile = new MISSProfile { EducationLevel = -60, SocialEnergy = -30, Curiosity = 100 } },
            new() { Name = "元气少女", Profile = new MISSProfile { SocialEnergy = 100, Adventurousness = 80, Willpower = 80 } },
            new() { Name = "三无少女", Profile = new MISSProfile { RationalEmotional = -100, SocialEnergy = -100, Intimacy = 50 } },
            new() { Name = "中二病", Profile = new MISSProfile { Adventurousness = 100, Humor = 60, EducationLevel = -50 } },
            new() { Name = "邻家女孩", Profile = new MISSProfile() },
        };
    }

    public SettingsData? LoadSettings()
    {
        if (!File.Exists(SettingsPath)) return null;
        try
        {
            var json = File.ReadAllText(SettingsPath);
            var loaded = System.Text.Json.JsonSerializer.Deserialize<SettingsData>(json, JsonOpts);
            if (loaded != null && !string.IsNullOrEmpty(loaded.openai_api_key))
            {
                try { loaded.openai_api_key = PythonBridge.DecryptMessage(loaded.openai_api_key); }
                catch { /* decrypt failed — may be plaintext from older version, keep as-is */ }
            }
            return loaded;
        }
        catch { return null; }
    }

    public void SaveSettings(SettingsData settings)
    {
        var apiKey = settings.openai_api_key;
        try
        {
            if (!string.IsNullOrEmpty(apiKey))
            {
                try { settings.openai_api_key = PythonBridge.EncryptMessage(apiKey); }
                catch { /* encryption unavailable, store as-is */ }
            }
            var json = System.Text.Json.JsonSerializer.Serialize(settings, JsonOpts);
            File.WriteAllText(SettingsPath, json);
        }
        finally
        {
            settings.openai_api_key = apiKey;
        }
    }

    #endregion
}
