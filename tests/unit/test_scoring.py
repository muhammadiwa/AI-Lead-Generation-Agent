import pytest

def calculate_score(lead_data, weights):
    """
    Placeholder scoring logic based on architecture.md Section 7.1
    """
    icp_fit = lead_data.get("icp_fit", 0) * weights.get("icp_fit", 0.3)
    tech_signal = lead_data.get("tech_signal", 0) * weights.get("tech_signal", 0.25)
    budget = lead_data.get("budget", 0) * weights.get("budget", 0.2)
    engagement = lead_data.get("engagement", 0) * weights.get("engagement", 0.15)
    urgency = lead_data.get("urgency", 0) * weights.get("urgency", 0.1)
    
    return icp_fit + tech_signal + budget + engagement + urgency

def test_scoring_calculation_perfect_match():
    lead = {
        "icp_fit": 100,
        "tech_signal": 100,
        "budget": 100,
        "engagement": 100,
        "urgency": 100
    }
    weights = {
        "icp_fit": 0.3,
        "tech_signal": 0.25,
        "budget": 0.2,
        "engagement": 0.15,
        "urgency": 0.1
    }
    score = calculate_score(lead, weights)
    assert score == 100.0

def test_scoring_calculation_no_match():
    lead = {
        "icp_fit": 0,
        "tech_signal": 0,
        "budget": 0,
        "engagement": 0,
        "urgency": 0
    }
    weights = {
        "icp_fit": 0.3,
        "tech_signal": 0.25,
        "budget": 0.2,
        "engagement": 0.15,
        "urgency": 0.1
    }
    score = calculate_score(lead, weights)
    assert score == 0.0

def test_scoring_calculation_partial_match():
    lead = {
        "icp_fit": 50,
        "tech_signal": 0,
        "budget": 100,
        "engagement": 0,
        "urgency": 0
    }
    weights = {
        "icp_fit": 0.3,
        "tech_signal": 0.25,
        "budget": 0.2,
        "engagement": 0.15,
        "urgency": 0.1
    }
    # (50 * 0.3) + (100 * 0.2) = 15 + 20 = 35
    score = calculate_score(lead, weights)
    assert score == 35.0

def test_scoring_handles_missing_dimensions():
    lead = {
        "icp_fit": 50
        # Other dimensions missing
    }
    weights = {
        "icp_fit": 0.3,
        "tech_signal": 0.25,
        "budget": 0.2,
        "engagement": 0.15,
        "urgency": 0.1
    }
    score = calculate_score(lead, weights)
    assert score == 15.0
