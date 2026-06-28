import pytest
from pydantic import ValidationError
from services.attribute_engine import MISSProfile

BIDIRECTIONAL_FIELDS = [
    "rational_emotional", "willpower", "independent_submissive",
    "education_level", "curiosity", "humor", "aggression",
    "social_energy", "adventurousness"
]

ALL_FIELDS = BIDIRECTIONAL_FIELDS + ["intimacy"]


def test_default_values():
    profile = MISSProfile()
    assert profile.rational_emotional == 0
    assert profile.willpower == 0
    assert profile.independent_submissive == 0
    assert profile.education_level == 0
    assert profile.intimacy == 0
    assert profile.curiosity == 0
    assert profile.humor == 0
    assert profile.aggression == 0
    assert profile.social_energy == 0
    assert profile.adventurousness == 0
    assert profile.allowed_domains == []


def test_allowed_domains_multi_value():
    profile = MISSProfile(allowed_domains=["艺术", "人文"])
    assert profile.allowed_domains == ["艺术", "人文"]


@pytest.mark.parametrize("field", ALL_FIELDS)
def test_upper_bound_valid(field):
    profile = MISSProfile(**{field: 100})
    assert getattr(profile, field) == 100


@pytest.mark.parametrize("field", BIDIRECTIONAL_FIELDS)
def test_lower_bound_valid(field):
    profile = MISSProfile(**{field: -100})
    assert getattr(profile, field) == -100


def test_intimacy_zero_is_valid():
    profile = MISSProfile(intimacy=0)
    assert profile.intimacy == 0


def test_intimacy_negative_raises():
    with pytest.raises(ValidationError):
        MISSProfile(intimacy=-1)


@pytest.mark.parametrize("field", ALL_FIELDS)
def test_upper_overflow_raises(field):
    with pytest.raises(ValidationError):
        MISSProfile(**{field: 101})


@pytest.mark.parametrize("field", BIDIRECTIONAL_FIELDS)
def test_lower_overflow_raises(field):
    with pytest.raises(ValidationError):
        MISSProfile(**{field: -101})


def test_json_serialization_roundtrip():
    profile = MISSProfile(
        rational_emotional=50,
        willpower=-30,
        education_level=-100,
        intimacy=80,
        allowed_domains=["艺术"],
    )
    json_str = profile.model_dump_json()
    profile2 = MISSProfile.model_validate_json(json_str)
    assert profile2.rational_emotional == 50
    assert profile2.education_level == -100
    assert profile2.intimacy == 80
    assert profile2.allowed_domains == ["艺术"]
