#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Internationalization (i18n) Module

Provides translations for multiple languages
"""

import os
from typing import Dict, Any

# Default language
DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "zh_CN")

# Supported languages
SUPPORTED_LANGUAGES = ["zh_CN", "en_US"]

# Language names
LANGUAGE_NAMES = {"zh_CN": "简体中文", "en_US": "English"}

# Cache for translations
_translations_cache: Dict[str, Dict[str, Any]] = {}


def get_translations(language: str = None) -> Dict[str, Any]:
    """
    Get translations for specified language

    Args:
        language: Language code (zh_CN/en_US), defaults to DEFAULT_LANGUAGE

    Returns:
        Dictionary containing all translations
    """
    if language is None:
        language = DEFAULT_LANGUAGE

    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE

    # Return from cache if available
    if language in _translations_cache:
        return _translations_cache[language]

    # Import translations
    if language == "zh_CN":
        from .zh_CN import (
            REPORT_TYPES,
            REPORT_LEVELS,
            STATUS_NAMES,
            PRIORITY_NAMES,
            EMAIL_SUBJECTS,
            EMAIL_CONTENT,
            SUBSCRIPTION_MESSAGES,
            DAYS_OF_WEEK,
            MONTHS,
        )
    else:  # en_US
        from .en_US import (
            REPORT_TYPES,
            REPORT_LEVELS,
            STATUS_NAMES,
            PRIORITY_NAMES,
            EMAIL_SUBJECTS,
            EMAIL_CONTENT,
            SUBSCRIPTION_MESSAGES,
            DAYS_OF_WEEK,
            MONTHS,
        )

    translations = {
        "REPORT_TYPES": REPORT_TYPES,
        "REPORT_LEVELS": REPORT_LEVELS,
        "STATUS_NAMES": STATUS_NAMES,
        "PRIORITY_NAMES": PRIORITY_NAMES,
        "EMAIL_SUBJECTS": EMAIL_SUBJECTS,
        "EMAIL_CONTENT": EMAIL_CONTENT,
        "SUBSCRIPTION_MESSAGES": SUBSCRIPTION_MESSAGES,
        "DAYS_OF_WEEK": DAYS_OF_WEEK,
        "MONTHS": MONTHS,
    }

    # Cache translations
    _translations_cache[language] = translations

    return translations


def get_report_type_name(report_type: str, language: str = None) -> str:
    """Get localized report type name"""
    translations = get_translations(language)
    return translations["REPORT_TYPES"].get(report_type, report_type)


def get_status_name(status: str, language: str = None) -> str:
    """Get localized status name"""
    translations = get_translations(language)
    return translations["STATUS_NAMES"].get(status, status)


def get_priority_name(priority: str, language: str = None) -> str:
    """Get localized priority name"""
    translations = get_translations(language)
    return translations["PRIORITY_NAMES"].get(priority, priority)


def format_email_subject(
    report_type: str, project_name: str, date_info: str, language: str = None
) -> str:
    """
    Format email subject line

    Args:
        report_type: daily/weekly/monthly
        project_name: Project name
        date_info: Date/month/week range string
        language: Language code

    Returns:
        Formatted subject line
    """
    translations = get_translations(language)
    subjects = translations["EMAIL_SUBJECTS"]

    if report_type == "daily":
        return subjects["daily"].format(project_name=project_name, date=date_info)
    elif report_type == "weekly":
        return subjects["weekly"].format(
            project_name=project_name, date_range=date_info
        )
    else:  # monthly
        return subjects["monthly"].format(project_name=project_name, month=date_info)


def get_metric_name(metric: str, language: str = None) -> str:
    """Get localized metric name"""
    translations = get_translations(language)
    metrics = translations["EMAIL_CONTENT"]["metrics"]
    return metrics.get(metric, metric)


def get_trend_name(trend: str, language: str = None) -> str:
    """Get localized trend name"""
    translations = get_translations(language)
    trend_dict = translations["EMAIL_CONTENT"]["trend"]
    return trend_dict.get(trend, trend)


def get_section_name(section: str, language: str = None) -> str:
    """Get localized section name"""
    translations = get_translations(language)
    content = translations["EMAIL_CONTENT"]
    return content.get(section, section)


# Initialize default translations
get_translations(DEFAULT_LANGUAGE)
