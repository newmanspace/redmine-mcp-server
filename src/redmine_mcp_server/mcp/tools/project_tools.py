import os
from typing import Dict, Any, List, Optional, Union

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP - Project Management Tools
"""

from ..server import mcp, redmine, logger


@mcp.tool()
async def search_redmine_issues(
    query: str, **options: Any
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Search Redmine issues matching a query string with pagination support.

    Performs text search across issues using the Redmine Search API.
    Supports server-side pagination to prevent MCP token overflow.

    Args:
        query: Text to search for in issues.
        **options: Search, pagination, and field selection options:
            - limit: Maximum number of issues to return (default: 25, max: 1000)
            - offset: Number of issues to skip for pagination (default: 0)
            - include_pagination_info: Return structured response with metadata
                                   (default: False)
            - fields: List of field names to include in results (default: None = all)
                     Available: id, subject, description, project, status,
                               priority, author, assigned_to, created_on, updated_on
            - scope: Search scope (default: "all")
                    Values: "all", "my_project", "subprojects"
            - open_issues: Search only open issues (default: False)
            - [other Redmine Search API parameters]

    Returns:
        List[Dict] (default) or Dict with 'issues' and 'pagination' keys.
        Issues are limited to prevent token overflow (25,000 token MCP limit).

    Examples:
        >>> await search_redmine_issues("bug fix")
        [{"id": 1, "subject": "Bug in login", ...}, ...]

        >>> await search_redmine_issues(
        ...     "performance", limit=10, offset=0, include_pagination_info=True
        ... )
        {
            "issues": [...],
            "pagination": {"limit": 10, "offset": 0, "has_next": True, ...}
        }

        >>> await search_redmine_issues("urgent", fields=["id", "subject", "status"])
        [{"id": 1, "subject": "Critical bug", "status": {...}}, ...]

        >>> await search_redmine_issues("bug", scope="my_project", open_issues=True)
        [{"id": 1, "subject": "Open bug in my project", ...}, ...]

    Note:
        The Redmine Search API does not provide total_count. Pagination
        metadata uses conservative estimation: has_next=True if result
        count equals limit.

        Search API Limitations: The Search API supports text search with
        scope and open_issues filters only. For advanced filtering by
        project_id, status_id, priority_id, etc., use list_my_redmine_issues()
        instead, which uses the Issues API with full filter support.

    Performance:
        - Memory efficient: Uses server-side pagination
        - Token efficient: Default limit keeps response under 2000 tokens
        - Further reduce tokens: Use fields parameter for minimal data transfer
    """
    if not redmine:
        logging.error("Redmine client not initialized")
        return [{"error": "Redmine client not initialized."}]

    try:
        # Handle MCP interface wrapping parameters in 'options' key
        if "options" in options and isinstance(options["options"], dict):
            actual_options = options["options"]
        else:
            actual_options = options

        # Extract pagination and field selection parameters
        limit = actual_options.pop("limit", 25)
        offset = actual_options.pop("offset", 0)
        include_pagination_info = actual_options.pop("include_pagination_info", False)
        fields = actual_options.pop("fields", None)

        # Use actual_options for remaining Redmine search options
        options = actual_options

        # Log request for monitoring
        option_keys = list(options.keys()) if options else []
        logging.info(
            f"Search request: query='{query}', limit={limit}, "
            f"offset={offset}, options={option_keys}"
        )

        # Validate and sanitize limit parameter
        if limit is not None:
            if not isinstance(limit, int):
                try:
                    limit = int(limit)
                except (ValueError, TypeError):
                    logging.warning(
                        f"Invalid limit type {type(limit)}, using default 25"
                    )
                    limit = 25

            if limit <= 0:
                logging.debug(f"Limit {limit} <= 0, returning empty result")
                empty_result = []
                if include_pagination_info:
                    empty_result = {
                        "issues": [],
                        "pagination": {
                            "limit": limit,
                            "offset": offset,
                            "count": 0,
                            "has_next": False,
                            "has_previous": False,
                            "next_offset": None,
                            "previous_offset": None,
                        },
                    }
                return empty_result

            # Cap at reasonable maximum
            original_limit = limit
            limit = min(limit, 1000)
            if original_limit > limit:
                logging.warning(
                    f"Limit {original_limit} exceeds maximum 1000, "
                    f"capped to {limit}"
                )

        # Validate offset
        if not isinstance(offset, int) or offset < 0:
            logging.warning(f"Invalid offset {offset}, reset to 0")
            offset = 0

        # Pass offset and limit to Redmine Search API
        search_params = {"offset": offset, "limit": limit, **options}

        # Perform search with pagination
        logging.debug(f"Calling redmine.issue.search with: {search_params}")
        results = redmine.issue.search(query, **search_params)

        if results is None:
            results = []

        # Convert results to list
        issues_list = list(results)
        logging.debug(
            f"Retrieved {len(issues_list)} issues with "
            f"offset={offset}, limit={limit}"
        )

        # Convert to dictionaries with optional field selection
        result_issues = [
            _issue_to_dict_selective(issue, fields) for issue in issues_list
        ]

        # Handle metadata response format
        if include_pagination_info:
            # Search API doesn't provide total_count
            # Use conservative estimation
            pagination_info = {
                "limit": limit,
                "offset": offset,
                "count": len(result_issues),
                "has_next": len(result_issues) == limit,
                "has_previous": offset > 0,
                "next_offset": (
                    offset + limit if len(result_issues) == limit else None
                ),
                "previous_offset": max(0, offset - limit) if offset > 0 else None,
            }

            result = {"issues": result_issues, "pagination": pagination_info}

            logging.info(
                f"Returning paginated search response: " f"{len(result_issues)} issues"
            )
            return result

        # Log success and return simple list
        logging.info(f"Successfully searched and retrieved {len(result_issues)} issues")
        return result_issues

    except Exception as e:
        return _handle_redmine_error(e, f"searching issues with query '{query}'")
