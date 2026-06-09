"""Personalization engine — LLM-powered template variable replacement and content generation."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from app.config import settings
from app.qualification.llm_analyzer import LeadAnalysis

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """Personalize outreach templates using lead data and optional LLM enhancement."""

    def __init__(self):
        self.openai_key = settings.openai_api_key
        self.anthropic_key = settings.anthropic_api_key

    def fill_template(
        self,
        template_body: str,
        template_subject: Optional[str],
        lead_data: Dict[str, Any],
        contact_data: Optional[Dict[str, Any]] = None,
        sender_data: Optional[Dict[str, Any]] = None,
        analysis: Optional[LeadAnalysis] = None,
    ) -> Dict[str, str]:
        """Fill template variables with lead/person/sender data."""
        variables = self._build_variable_map(lead_data, contact_data, sender_data, analysis)

        filled_subject = self._replace_vars(template_subject or "", variables)
        filled_body = self._replace_vars(template_body, variables)

        return {
            "subject": filled_subject,
            "body": filled_body,
            "variables_used": list(variables.keys()),
        }

    def _build_variable_map(
        self,
        lead: Dict[str, Any],
        contact: Optional[Dict[str, Any]],
        sender: Optional[Dict[str, Any]],
        analysis: Optional[LeadAnalysis],
    ) -> Dict[str, str]:
        """Build the complete variable substitution map."""
        vars_dict: Dict[str, str] = {}

        # Lead variables
        vars_dict["{{company_name}}"] = lead.get("company_name", "your company")
        vars_dict["{{company_domain}}"] = lead.get("company_domain", "")
        vars_dict["{{industry}}"] = lead.get("industry", "technology")
        vars_dict["{{tech_stack}}"] = self._format_tech_stack(lead.get("tech_stack"))
        vars_dict["{{tech}}"] = self._get_primary_tech(lead.get("tech_stack"))
        vars_dict["{{location}}"] = ", ".join(
            filter(None, [lead.get("location_city", ""), lead.get("location_state", ""), lead.get("location_country", "")])
        ) or "your area"

        # Contact variables
        if contact:
            vars_dict["{{first_name}}"] = contact.get("first_name", contact.get("full_name", "there"))
            vars_dict["{{last_name}}"] = contact.get("last_name", "")
            vars_dict["{{full_name}}"] = contact.get("full_name", vars_dict["{{first_name}}"])
            vars_dict["{{role}}"] = contact.get("role_title", contact.get("role", "team member"))
            vars_dict["{{role_category}}"] = contact.get("role", "")

        # Sender variables
        if sender:
            vars_dict["{{sender_name}}"] = sender.get("name", "Team")
            vars_dict["{{sender_title}}"] = sender.get("title", "")
            vars_dict["{{sender_company}}"] = sender.get("company", "Ship Studio")
            vars_dict["{{sender_email}}"] = sender.get("email", "")

        # Analysis variables
        if analysis:
            if analysis.pain_points:
                vars_dict["{{pain_point}}"] = analysis.pain_points[0]
            if analysis.tech_needs:
                vars_dict["{{service_relevance}}"] = analysis.tech_needs[0]
            if analysis.recommended_approach:
                vars_dict["{{specific_observation}}"] = analysis.recommended_approach
            vars_dict["{{engagement_score}}"] = str(analysis.engagement_score)

        # Defaults for missing values
        defaults = {
            "{{first_name}}": "there",
            "{{pain_point}}": "building and scaling your product",
            "{{service_relevance}}": "software development and product engineering",
            "{{specific_observation}}": "the great work you're doing",
            "{{value_add_topic}}": "engineering productivity",
            "{{similar_company}}": "companies in your space",
            "{{result}}": "accelerate their delivery timelines",
            "{{sender_name}}": "Alex",
            "{{sender_company}}": "Ship Studio",
            "{{sender_title}}": "Engineering Partner",
        }
        for key, default in defaults.items():
            if key not in vars_dict or not vars_dict[key]:
                vars_dict[key] = default

        return vars_dict

    def _replace_vars(self, text: str, variables: Dict[str, str]) -> str:
        """Replace all {{variable}} patterns in text."""
        result = text
        for var, value in variables.items():
            result = result.replace(var, value)
        return result

    def _format_tech_stack(self, tech_stack: Any) -> str:
        """Format tech stack data into a readable string."""
        if not tech_stack:
            return "modern technologies"
        if isinstance(tech_stack, dict):
            techs = tech_stack.get("detected_technologies", [])
            if techs:
                return ", ".join(techs[:5])
        return "modern technologies"

    def _get_primary_tech(self, tech_stack: Any) -> str:
        """Get the primary/notable technology from the tech stack."""
        if not tech_stack:
            return "tech"
        if isinstance(tech_stack, dict):
            techs = tech_stack.get("detected_technologies", [])
            if techs:
                return techs[0]
        return "tech"


# Singleton
personalizer = PersonalizationEngine()