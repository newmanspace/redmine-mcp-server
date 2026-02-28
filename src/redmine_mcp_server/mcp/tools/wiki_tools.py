import os
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redmine MCP - Wiki Management Tools
"""

from ..server import mcp, redmine, logger
from ...redmine_handler import _handle_redmine_error


@mcp.tool()
async def create_redmine_issue(
    project_id: int,
    subject: str,
    description: str = "",
    **fields: Any,
) -> Dict[str, Any]:
    """Create a new issue in Redmine."""
    if not redmine:
        return {"error": "Redmine client not initialized."}
    try:
        issue = redmine.issue.create(
            project_id=project_id, subject=subject, description=description, **fields
        )
        return _issue_to_dict(issue)
    except Exception as e:
        return _handle_redmine_error(e, f"creating issue in project {project_id}")


@mcp.tool()
async def update_redmine_issue(issue_id: int, fields: Dict[str, Any]) -> Dict[str, Any]:
    """Update an existing Redmine issue.

    In addition to standard Redmine fields, a ``status_name`` key may be
    provided in ``fields``. When present and ``status_id`` is not supplied, the
    function will look up the corresponding status ID and use it for the update.
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    # Convert status name to id if requested
    if "status_name" in fields and "status_id" not in fields:
        name = str(fields.pop("status_name")).lower()
        try:
            statuses = redmine.issue_status.all()
            for status in statuses:
                if getattr(status, "name", "").lower() == name:
                    fields["status_id"] = status.id
                    break
        except Exception as e:
            logger.warning(f"Error resolving status name '{name}': {e}")

    try:
        redmine.issue.update(issue_id, **fields)
        updated_issue = redmine.issue.get(issue_id)
        return _issue_to_dict(updated_issue)
    except Exception as e:
        return _handle_redmine_error(
            e,
            f"updating issue {issue_id}",
            {"resource_type": "issue", "resource_id": issue_id},
        )


@mcp.tool()
async def get_redmine_attachment_download_url(
    attachment_id: int,
) -> Dict[str, Any]:
    """Get HTTP download URL for a Redmine attachment.

    Downloads the attachment to server storage and returns a time-limited
    HTTP URL that clients can use to download the file. Expiry time and
    storage location are controlled by server configuration.

    Args:
        attachment_id: The ID of the attachment to retrieve

    Returns:
        Dict containing download_url, filename, content_type, size,
        expires_at, and attachment_id

    Raises:
        ResourceNotFoundError: If attachment ID doesn't exist
        Exception: For other download or processing errors
    """
    if not redmine:
        return {"error": "Redmine client not initialized."}

    # Ensure cleanup task is started (lazy initialization)
    await _ensure_cleanup_started()

    try:
        # Get attachment metadata from Redmine
        attachment = redmine.attachment.get(attachment_id)

        # Server-controlled configuration (secure)
        attachments_dir = Path(os.getenv("ATTACHMENTS_DIR", "./attachments"))
        expires_minutes = float(os.getenv("ATTACHMENT_EXPIRES_MINUTES", "60"))

        # Create secure storage directory
        attachments_dir.mkdir(parents=True, exist_ok=True)

        # Generate secure UUID-based filename
        file_id = str(uuid.uuid4())

        # Download using existing approach - keeps original filename
        downloaded_path = attachment.download(savepath=str(attachments_dir))

        # Get file info
        original_filename = getattr(
            attachment, "filename", f"attachment_{attachment_id}"
        )

        # Create organized storage with UUID directory
        uuid_dir = attachments_dir / file_id
        uuid_dir.mkdir(exist_ok=True)

        # Move file to UUID-based location using atomic operations
        final_path = uuid_dir / original_filename
        temp_path = uuid_dir / f"{original_filename}.tmp"

        # Atomic file move with error handling
        try:
            os.rename(downloaded_path, temp_path)
            os.rename(temp_path, final_path)
        except (OSError, IOError) as e:
            # Cleanup on failure
            try:
                if temp_path.exists():
                    temp_path.unlink()
                if Path(downloaded_path).exists():
                    Path(downloaded_path).unlink()
            except OSError:
                pass  # Best effort cleanup
            return {"error": f"Failed to store attachment: {str(e)}"}

        # Calculate expiry time (timezone-aware)
        expires_hours = expires_minutes / 60.0
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        # Store metadata atomically (following existing pattern)
        metadata = {
            "file_id": file_id,
            "attachment_id": attachment_id,
            "original_filename": original_filename,
            "file_path": str(final_path),
            "content_type": getattr(
                attachment, "content_type", "application/octet-stream"
            ),
            "size": final_path.stat().st_size,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        metadata_file = uuid_dir / "metadata.json"
        temp_metadata = uuid_dir / "metadata.json.tmp"

        # Atomic metadata write with error handling
        try:
            with open(temp_metadata, "w") as f:
                json.dump(metadata, f, indent=2)
            os.rename(temp_metadata, metadata_file)
        except (OSError, IOError, ValueError) as e:
            # Cleanup on failure
            try:
                if temp_metadata.exists():
                    temp_metadata.unlink()
                if final_path.exists():
                    final_path.unlink()
            except OSError:
                pass  # Best effort cleanup
            return {"error": f"Failed to save metadata: {str(e)}"}

        # Generate server base URL from environment configuration
        # Use public configuration for external URLs
        public_host = os.getenv("PUBLIC_HOST", os.getenv("SERVER_HOST", "localhost"))
        public_port = os.getenv("PUBLIC_PORT", os.getenv("SERVER_PORT", "8000"))

        # Handle special case of 0.0.0.0 bind address
        if public_host == "0.0.0.0":
            public_host = "localhost"

        download_url = f"http://{public_host}:{public_port}/files/{file_id}"

        return {
            "download_url": download_url,
            "filename": original_filename,
            "content_type": metadata["content_type"],
            "size": metadata["size"],
            "expires_at": metadata["expires_at"],
            "attachment_id": attachment_id,
        }

    except Exception as e:
        return _handle_redmine_error(
            e,
            f"downloading attachment {attachment_id}",
            {"resource_type": "attachment", "resource_id": attachment_id},
        )
