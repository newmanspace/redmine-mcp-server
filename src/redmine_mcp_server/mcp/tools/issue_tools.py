#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP - Issue Management Tools

Tools for managing Redmine issues.
"""

from typing import Dict, Any, List, Optional, Union
from ..server import mcp, redmine, logger


@mcp.tool()
async def get_redmine_issue(
    issue_id: int, include_journals: bool = True, include_attachments: bool = True
) -> Dict[str, Any]:
    """Retrieve a specific Redmine issue by ID.

    Args:
        issue_id: The ID of the issue to retrieve
        include_journals: Whether to include journals (comments) in the result.
            Defaults to ``True``.
        include_attachments: Whether to include attachments metadata in the
            result. Defaults to ``True``.

    Returns:
        A dictionary containing issue details. If ``include_journals`` is ``True``
        and the issue has journals, they will be returned under the ``"journals"``
        key. If ``include_attachments`` is ``True`` and attachments exist they
        will be returned under the ``"attachments"`` key. On failure a dictionary
        with an ``"error"`` key is returned.
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    # Ensure cleanup task is started (lazy initialization)
    await _ensure_cleanup_started()
    try:
        # python-redmine is synchronous, so we don't use await here for the library call
        includes = []
        if include_journals:
            includes.append("journals")
        if include_attachments:
            includes.append("attachments")

        if includes:
            issue = redmine.issue.get(issue_id, include=",".join(includes))
        else:
            issue = redmine.issue.get(issue_id)

        result = _issue_to_dict(issue)
        if include_journals:
            result["journals"] = _journals_to_list(issue)
        if include_attachments:
            result["attachments"] = _attachments_to_list(issue)

        return result
    except Exception as e:
        return _handle_redmine_error(
            e,
            f"fetching issue {issue_id}",
            {"resource_type": "issue", "resource_id": issue_id},
        )


@mcp.tool()
async def list_redmine_projects() -> List[Dict[str, Any]]:
    """
    Lists all accessible projects in Redmine.
    Returns:
        A list of dictionaries, each representing a project.
    """
    if not redmine:
        return [{"error": "Redmine client not initialized."}]
    try:
        projects = redmine.project.all()
        return [
            {
                "id": project.id,
                "name": project.name,
                "identifier": project.identifier,
                "description": getattr(project, "description", ""),
                "created_on": (
                    project.created_on.isoformat()
                    if getattr(project, "created_on", None) is not None
                    else None
                ),
            }
            for project in projects
        ]
    except Exception as e:
        return [_handle_redmine_error(e, "listing projects")]


@mcp.tool()
async def list_my_redmine_issues(
    **filters: Any,
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """List issues assigned to the authenticated user with pagination support.

    This uses the Redmine REST API filter ``assigned_to_id='me'`` to
    retrieve issues for the current user. Supports server-side pagination
    to prevent MCP token overflow and improve performance.

    Args:
        **filters: Keyword arguments for filtering issues:
            - limit: Maximum number of issues to return (default: 25, max: 1000)
            - offset: Number of issues to skip for pagination (default: 0)
            - include_pagination_info: Return structured response with metadata
                                   (default: False)
            - sort: Sort order (e.g., "updated_on:desc")
            - status_id: Filter by status ID
            - project_id: Filter by project ID
            - [other Redmine API filters]

    Returns:
        List[Dict] (default) or Dict with 'issues' and 'pagination' keys.
        Issues are limited to prevent token overflow (25,000 token MCP limit).

    Examples:
        >>> await list_my_redmine_issues(limit=10)
        [{"id": 1, "subject": "Issue 1", ...}, ...]

        >>> await list_my_redmine_issues(
        ...     limit=25, offset=50, include_pagination_info=True
        ... )
        {
            "issues": [...],
            "pagination": {"total": 150, "has_next": True, "next_offset": 75, ...}
        }

    Performance:
        - Memory efficient: Uses server-side pagination
        - Token efficient: Default limit keeps response under 2000 tokens
        - Time efficient: Typically <500ms for limit=25
    """
    if not redmine:
        logging.error("Redmine client not initialized")
        return [{"error": "Redmine client not initialized."}]

    # Ensure cleanup task is started (lazy initialization)
    await _ensure_cleanup_started()

    try:
        # Handle MCP interface wrapping parameters in 'filters' key
        if "filters" in filters and isinstance(filters["filters"], dict):
            actual_filters = filters["filters"]
        else:
            actual_filters = filters

        # Extract pagination parameters
        limit = actual_filters.pop("limit", 25)
        offset = actual_filters.pop("offset", 0)
        include_pagination_info = actual_filters.pop("include_pagination_info", False)

        # Use actual_filters for remaining Redmine filters
        filters = actual_filters

        # Log request for monitoring
        filter_keys = list(filters.keys()) if filters else []
        logging.info(
            f"Pagination request: limit={limit}, offset={offset}, filters={filter_keys}"
        )

        # Validate and sanitize parameters
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
                            "total": 0,
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
                    f"Limit {original_limit} exceeds maximum 1000, capped to {limit}"
                )

        # Validate offset
        if not isinstance(offset, int) or offset < 0:
            logging.warning(f"Invalid offset {offset}, reset to 0")
            offset = 0

        # Use python-redmine ResourceSet native pagination
        # Server-side filtering more efficient than client-side
        redmine_filters = {
            "assigned_to_id": "me",
            "offset": offset,
            "limit": min(limit or 25, 100),  # Redmine API max per request
            **filters,
        }

        # Get paginated issues from Redmine
        logging.debug(f"Calling redmine.issue.filter with: {redmine_filters}")
        issues = redmine.issue.filter(**redmine_filters)

        # Convert ResourceSet to list (triggers server-side pagination)
        issues_list = list(issues)
        logging.debug(
            f"Retrieved {len(issues_list)} issues with offset={offset}, limit={limit}"
        )

        # Convert to dictionaries
        result_issues = [_issue_to_dict(issue) for issue in issues_list]

        # Handle metadata response format
        if include_pagination_info:
            # Get total count from a separate query without offset/limit
            try:
                # Create clean query for total count (no pagination parameters)
                count_filters = {"assigned_to_id": "me", **filters}
                count_query = redmine.issue.filter(**count_filters)
                # Must evaluate the query first to get accurate total_count
                list(count_query)  # Trigger evaluation
                total_count = count_query.total_count
                logging.debug(f"Got total count from separate query: {total_count}")
            except Exception as e:
                logging.warning(
                    f"Could not get total count: {e}, using estimated value"
                )
                # For unknown total, use a conservative estimate
                if len(result_issues) == limit:
                    # If we got a full page, there might be more
                    total_count = offset + len(result_issues) + 1
                else:
                    # If we got less than requested, this is likely the end
                    total_count = offset + len(result_issues)

            pagination_info = {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "count": len(result_issues),
                "has_next": len(result_issues) == limit,
                "has_previous": offset > 0,
                "next_offset": offset + limit if len(result_issues) == limit else None,
                "previous_offset": max(0, offset - limit) if offset > 0 else None,
            }

            result = {"issues": result_issues, "pagination": pagination_info}

            logging.info(
                f"Returning paginated response: {len(result_issues)} issues, "
                f"total={total_count}"
            )
            return result

        # Log success and return simple list
        logging.info(f"Successfully retrieved {len(result_issues)} issues")
        return result_issues

    except Exception as e:
        return [_handle_redmine_error(e, "listing assigned issues")]
