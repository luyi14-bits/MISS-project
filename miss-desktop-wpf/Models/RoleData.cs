using System.Text.Json.Serialization;

namespace MISS.Models;

public class RoleData
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = "";

    [JsonPropertyName("description")]
    public string Description { get; set; } = "";

    [JsonPropertyName("background")]
    public string Background { get; set; } = "";

    [JsonPropertyName("profile")]
    public MISSProfile Profile { get; set; } = new();

    [JsonPropertyName("avatar_path")]
    public string AvatarPath { get; set; } = "";
}
