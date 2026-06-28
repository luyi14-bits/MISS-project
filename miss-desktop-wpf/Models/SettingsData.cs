using System.Text.Json.Serialization;

namespace MISS.Services;

public class SettingsData
{
    [JsonPropertyName("openai_api_key")]
    public string? openai_api_key { get; set; }

    [JsonPropertyName("openai_base_url")]
    public string? openai_base_url { get; set; }

    [JsonPropertyName("model")]
    public string? model { get; set; }
}
