import pytest
from app.api.v1.scoring import _calculate_lead_score, _determine_status
from app.models import Lead

def test_calculate_lead_score_perfect_match():
    # Construct a lead that should hit all the high marks
    lead = Lead(
        industry="Technology",
        employee_count=100,
        location_country="USA",
        founded_year=2020,
        tech_stack={"detected_technologies": ["React", "Python", "Node", "AWS"]},
        company_github_url="https://github.com/testcorp",
        description="We are building a React and Python platform. Extremely high growth.",
        funding_total=5000000,
        funding_rounds=[{"type": "Seed"}],
        social_links={"linkedin": "test"},
        company_url="https://testcorp.com",
        status="discovered",
        notes="URGENT project needed"
    )
    
    result = _calculate_lead_score(lead)
    
    assert result["total"] == 100.0
    assert result["breakdown"]["icp_fit"] == 30
    assert result["breakdown"]["tech_signal"] == 25
    assert result["breakdown"]["budget_indicator"] == 20
    assert result["breakdown"]["engagement_potential"] == 15
    assert result["breakdown"]["urgency"] == 10

def test_calculate_lead_score_minimal():
    lead = Lead(
        company_name="Minimal Corp",
        source="manual"
    )
    
    result = _calculate_lead_score(lead)
    
    # Expected base scores:
    # icp_fit: 0
    # tech_signal: 5 (base)
    # budget_indicator: 5 (base)
    # engagement_potential: 3 (base)
    # urgency: 2 (base)
    # total: 15
    assert result["total"] == 15.0

def test_determine_status_thresholds():
    assert _determine_status(70.0) == "qualified_hot"
    assert _determine_status(69.9) == "qualified_warm"
    assert _determine_status(50.0) == "qualified_warm"
    assert _determine_status(49.9) == "qualified_cool"
    assert _determine_status(30.0) == "qualified_cool"
    assert _determine_status(29.9) == "cold"

def test_calculate_lead_score_missing_fields_handling():
    # Lead with some nulls that might cause issues if not handled
    lead = Lead(
        industry=None,
        employee_count=None,
        tech_stack=None
    )
    
    result = _calculate_lead_score(lead)
    assert "total" in result
    assert isinstance(result["total"], float)
