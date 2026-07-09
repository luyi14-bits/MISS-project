using System.IO;
using System.Text.Json;
using MISS.Models;
using MISS.Services;
using MISS.Controls;

namespace miss_desktop_wpf.Tests;

public class CoreDomainTests
{
    [Fact]
    public void MISSProfile_Clone_CopiesAllAttributes()
    {
        var original = new MISSProfile
        {
            RationalEmotional = 50, Willpower = -30, IndependentSubmissive = 80,
            EducationLevel = 100, Intimacy = 75, Curiosity = 60,
            Humor = 40, Aggression = -50, SocialEnergy = 20, Adventurousness = 90,
        };
        var clone = original.Clone();
        Assert.Equal(original.RationalEmotional, clone.RationalEmotional);
        Assert.Equal(original.Willpower, clone.Willpower);
        Assert.Equal(original.Intimacy, clone.Intimacy);
    }

    [Fact]
    public void MISSProfile_Clone_IsIndependentCopy()
    {
        var original = new MISSProfile { RationalEmotional = 50 };
        var clone = original.Clone();
        clone.RationalEmotional = 0;
        Assert.Equal(50, original.RationalEmotional);
    }

    [Fact]
    public void MISSProfile_DefaultValues_AreZero()
    {
        var p = new MISSProfile();
        Assert.Equal(0, p.RationalEmotional);
        Assert.Equal(0, p.Intimacy);
    }

    [Fact]
    public void MISSProfile_Indexer_ReturnsCorrectValue()
    {
        var p = new MISSProfile { RationalEmotional = 42 };
        Assert.Equal(42, p["rational_emotional"]);
        Assert.Equal(0, p["nonexistent"]);
    }

    [Fact]
    public void ConversationExporter_ExportToJson_CreatesValidJson()
    {
        var msgs = new List<ChatMessage>
        {
            new() { Sender = "User", Text = "Hello", IsUser = true },
            new() { Sender = "Bot", Text = "Hi", RoleName = "Test", IsUser = false },
        };
        var session = new SessionData { Id = 1, Title = "Test", CreatedAt = DateTime.Now };
        var path = Path.GetTempFileName() + ".json";
        ConversationExporter.ExportToJson(msgs, session, path);
        var json = File.ReadAllText(path);
        Assert.Contains("Hello", json);
        Assert.Contains("Hi", json);
        File.Delete(path);
    }

    [Fact]
    public void ConversationExporter_ExportToHtml_ContainsMarkup()
    {
        var msgs = new List<ChatMessage>
        {
            new() { Sender = "Me", Text = "Hello", IsUser = true },
        };
        var session = new SessionData { Id = 1, Title = "T", CreatedAt = DateTime.Now };
        var path = Path.GetTempFileName() + ".html";
        ConversationExporter.ExportToHtml(msgs, session, null, path);
        var html = File.ReadAllText(path);
        Assert.Contains("<html", html);
        Assert.Contains("Hello", html);
        Assert.Contains("msg", html);
        File.Delete(path);
    }

    [Fact]
    public void ConversationExporter_ExportToMarkdown_ContainsText()
    {
        var msgs = new List<ChatMessage>
        {
            new() { Sender = "Me", Text = "Hi", IsUser = true },
        };
        var session = new SessionData { Id = 1, Title = "D", CreatedAt = DateTime.Now };
        var path = Path.GetTempFileName() + ".md";
        ConversationExporter.ExportToMarkdown(msgs, session, null, path);
        var md = File.ReadAllText(path);
        Assert.Contains("Hi", md);
        Assert.Contains("**我**", md);
        File.Delete(path);
    }

    [Fact]
    public void RoleData_Serialization_RoundTrip()
    {
        var role = new RoleData
        {
            Name = "Test",
            Description = "Desc",
            TavernDescription = "ST Desc",
            TavernFirstMessage = "Hello",
        };
        var json = JsonSerializer.Serialize(role);
        var deserialized = JsonSerializer.Deserialize<RoleData>(json);
        Assert.NotNull(deserialized);
        Assert.Equal("Test", deserialized!.Name);
        Assert.Equal("ST Desc", deserialized.TavernDescription);
    }

    [Fact]
    public void SessionData_Serialization_RoundTrip()
    {
        var session = new SessionData { Id = 42, Title = "Test", RoleName = "Bot" };
        var json = JsonSerializer.Serialize(session);
        var deserialized = JsonSerializer.Deserialize<SessionData>(json);
        Assert.NotNull(deserialized);
        Assert.Equal(42, deserialized!.Id);
        Assert.Equal("Bot", deserialized.RoleName);
    }
}
