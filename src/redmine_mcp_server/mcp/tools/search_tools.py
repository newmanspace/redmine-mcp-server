import os
from typing import Dict, Any, List, Optional, Union

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP - Search Management Tools
"""

from ..server import mcp, redmine, logger
from ...redmine_handler import _handle_redmine_error


@mcp.tool()
async def search_entire_redmine(
    query: str,
    resources: Optional[List[str]] = None,
    limit: int = 100,
    offset: int = 0,
) -> Dict[str, Any]:
    """
    Search for issues and wiki pages across the Redmine instance.

    Args:
        query: Text to search for. Case sensitivity controlled by server DB config.
        resources: Filter by resource types. Allowed: ['issues', 'wiki_pages']
                   Default: None (searches both issues and wiki_pages)
        limit: Maximum number of results to return (max 100)
        offset: Pagination offset for server-side pagination

    Returns:
        Dictionary containing search results, counts, and metadata.
        On error, returns {"error": "message"}.

    Note:
        v1.4 Scope Limitation: Only 'issues' and 'wiki_pages' are supported.
        Requires Redmine 3.3.0 or higher for search API support.
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    try:
        await _ensure_cleanup_started()

        # Validate and enforce scope limitation (v1.4)
        allowed_types = ["issues", "wiki_pages"]
        if resources:
            resources = [r for r in resources if r in allowed_types]
            if not resources:
                resources = allowed_types  # Fall back to default if all filtered
        else:
            resources = allowed_types

        # Cap limit at 100 (Redmine API maximum)
        limit = min(limit, 100)
        if limit <= 0:
            limit = 100

        # Build search options
        search_options = {
            "resources": resources,
            "limit": limit,
            "offset": offset,
        }

        # Execute search
        categorized_results = redmine.search(query, **search_options)

        # Handle empty results (python-redmine returns None)
        if not categorized_results:
            return {
                "results": [],
                "results_by_type": {},
                "total_count": 0,
                "query": query,
            }

        # Process categorized results
        all_results = []
        results_by_type: Dict[str, int] = {}

        for resource_type, resource_set in categorized_results.items():
            # Skip 'unknown' category (plugin resources)
            if resource_type == "unknown":
                continue

            # Skip if not in allowed types
            if resource_type not in allowed_types:
                continue

            # Handle both ResourceSet and dict (for 'unknown')
            if hasattr(resource_set, "__iter__"):
                count = 0
                for resource in resource_set:
                    result_dict = _resource_to_dict(resource, resource_type)
                    all_results.append(result_dict)
                    count += 1
                if count > 0:
                    results_by_type[resource_type] = count

        return {
            "results": all_results,
            "results_by_type": results_by_type,
            "total_count": len(all_results),
            "query": query,
        }

    except VersionMismatchError:
        return {"error": "Search requires Redmine 3.3.0 or higher."}
    except Exception as e:
        return _handle_redmine_error(e, f"searching Redmine for '{query}'")


def _wiki_page_to_dict(
    wiki_page: Any, include_attachments: bool = True
) -> Dict[str, Any]:
    """Convert a wiki page object to a dictionary.

    Args:
        wiki_page: Redmine wiki page object
        include_attachments: Whether to include attachment metadata

    Returns:
        Dictionary with wiki page data
    """
    result: Dict[str, Any] = {
        "title": wiki_page.title,
        "text": wiki_page.text,
        "version": wiki_page.version,
    }

    # Add optional timestamp fields
    if hasattr(wiki_page, "created_on"):
        result["created_on"] = (
            str(wiki_page.created_on) if wiki_page.created_on else None
        )
    else:
        result["created_on"] = None

    if hasattr(wiki_page, "updated_on"):
        result["updated_on"] = (
            str(wiki_page.updated_on) if wiki_page.updated_on else None
        )
    else:
        result["updated_on"] = None

    # Add author info
    if hasattr(wiki_page, "author"):
        result["author"] = {
            "id": wiki_page.author.id,
            "name": wiki_page.author.name,
        }

    # Add project info
    if hasattr(wiki_page, "project"):
        result["project"] = {
            "id": wiki_page.project.id,
            "name": wiki_page.project.name,
        }

    # Process attachments if requested
    if include_attachments and hasattr(wiki_page, "attachments"):
        result["attachments"] = []
        for attachment in wiki_page.attachments:
            att_dict = {
                "id": attachment.id,
                "filename": attachment.filename,
                "filesize": attachment.filesize,
                "content_type": attachment.content_type,
                "description": getattr(attachment, "description", ""),
                "created_on": (
                    str(attachment.created_on)
                    if hasattr(attachment, "created_on") and attachment.created_on
                    else None
                ),
            }
            result["attachments"].append(att_dict)

    return result


@mcp.tool()
async def get_redmine_wiki_page(
    project_id: Union[str, int],
    wiki_page_title: str,
    version: Optional[int] = None,
    include_attachments: bool = True,
) -> Dict[str, Any]:
    """
    Retrieve full wiki page content from Redmine.

    Args:
        project_id: Project identifier (ID number or string identifier)
        wiki_page_title: Wiki page title (e.g., "Installation_Guide")
        version: Specific version number (None = latest version)
        include_attachments: Include attachment metadata in response

    Returns:
        Dictionary containing full wiki page content and metadata

    Note:
        Use get_redmine_attachment_download_url() to download attachments.
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    try:
        await _ensure_cleanup_started()

        # Retrieve wiki page
        if version:
            wiki_page = redmine.wiki_page.get(
                wiki_page_title, project_id=project_id, version=version
            )
        else:
            wiki_page = redmine.wiki_page.get(wiki_page_title, project_id=project_id)

        return _wiki_page_to_dict(wiki_page, include_attachments)

    except Exception as e:
        return _handle_redmine_error(
            e,
            f"fetching wiki page '{wiki_page_title}' in project {project_id}",
            {"resource_type": "wiki page", "resource_id": wiki_page_title},
        )
