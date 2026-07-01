// Copyright (C) 2026  MISS Project Contributors
// SPDX-License-Identifier: AGPL-3.0-or-later
// This file is part of MISS <https://github.com/luyi14-bits/MISS-project>.
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace MISS.Models;

public class MISSProfile
{
    [JsonPropertyName("rational_emotional")]
    public int RationalEmotional { get; set; }

    [JsonPropertyName("willpower")]
    public int Willpower { get; set; }

    [JsonPropertyName("independent_submissive")]
    public int IndependentSubmissive { get; set; }

    [JsonPropertyName("education_level")]
    public int EducationLevel { get; set; }

    [JsonPropertyName("intimacy")]
    public int Intimacy { get; set; }

    [JsonPropertyName("curiosity")]
    public int Curiosity { get; set; }

    [JsonPropertyName("humor")]
    public int Humor { get; set; }

    [JsonPropertyName("aggression")]
    public int Aggression { get; set; }

    [JsonPropertyName("social_energy")]
    public int SocialEnergy { get; set; }

    [JsonPropertyName("adventurousness")]
    public int Adventurousness { get; set; }

    public static readonly Dictionary<string, (string Label, int Min, int Max)> AttrMeta = new()
    {
        ["rational_emotional"] = ("理性←→情绪", -100, 100),
        ["willpower"] = ("意志力", -100, 100),
        ["independent_submissive"] = ("独立←→顺从", -100, 100),
        ["education_level"] = ("文化水平", -100, 100),
        ["intimacy"] = ("亲密度", 0, 100),
        ["curiosity"] = ("好奇心", -100, 100),
        ["humor"] = ("幽默感", -100, 100),
        ["aggression"] = ("攻击性", -100, 100),
        ["social_energy"] = ("社交能量", -100, 100),
        ["adventurousness"] = ("冒险精神", -100, 100),
    };

    public int this[string attr]
    {
        get => attr switch
        {
            "rational_emotional" => RationalEmotional,
            "willpower" => Willpower,
            "independent_submissive" => IndependentSubmissive,
            "education_level" => EducationLevel,
            "intimacy" => Intimacy,
            "curiosity" => Curiosity,
            "humor" => Humor,
            "aggression" => Aggression,
            "social_energy" => SocialEnergy,
            "adventurousness" => Adventurousness,
            _ => 0
        };
        set
        {
            switch (attr)
            {
                case "rational_emotional": RationalEmotional = value; break;
                case "willpower": Willpower = value; break;
                case "independent_submissive": IndependentSubmissive = value; break;
                case "education_level": EducationLevel = value; break;
                case "intimacy": Intimacy = value; break;
                case "curiosity": Curiosity = value; break;
                case "humor": Humor = value; break;
                case "aggression": Aggression = value; break;
                case "social_energy": SocialEnergy = value; break;
                case "adventurousness": Adventurousness = value; break;
            }
        }
    }

    public static List<string> AttrNames = new()
    {
        "rational_emotional", "willpower", "independent_submissive", "education_level",
        "intimacy", "curiosity", "humor", "aggression", "social_energy", "adventurousness"
    };

    public MISSProfile Clone()
    {
        return new MISSProfile
        {
            RationalEmotional = RationalEmotional,
            Willpower = Willpower,
            IndependentSubmissive = IndependentSubmissive,
            EducationLevel = EducationLevel,
            Intimacy = Intimacy,
            Curiosity = Curiosity,
            Humor = Humor,
            Aggression = Aggression,
            SocialEnergy = SocialEnergy,
            Adventurousness = Adventurousness,
        };
    }
}
