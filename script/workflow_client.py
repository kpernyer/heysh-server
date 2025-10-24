#!/usr/bin/env python3
"""Workflow client for testing hey.sh backend.

Usage:
    python script/workflow_client.py upload-doc --domain-id my-domain --file-path test.pdf
    python script/workflow_client.py ask --domain-id my-domain --question "What is X?"
    python script/workflow_client.py status --workflow-id doc-123456
"""

import asyncio
import os
from datetime import datetime
from typing import Any

import httpx
import structlog
import typer

logger = structlog.get_logger()
app = typer.Typer()

API_URL = os.getenv("API_URL", "http://localhost:8001")


async def call_api(
    method: str, endpoint: str, json: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Call the backend API."""
    url = f"{API_URL}{endpoint}"

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json=json)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()


@app.command()
def upload_doc(
    domain_id: str = typer.Option(..., help="Domain ID"),
    file_path: str = typer.Option(..., help="File path in storage"),
    document_id: str | None = typer.Option(
        None, help="Document ID (auto-generated if not provided)"
    ),
) -> None:
    """Upload document and trigger processing workflow."""
    doc_id = document_id or f"doc-{int(datetime.now().timestamp())}"

    typer.echo("🚀 Starting document processing workflow...")
    typer.echo(f"   Domain: {domain_id}")
    typer.echo(f"   Document: {doc_id}")
    typer.echo(f"   File: {file_path}")

    result = asyncio.run(
        call_api(
            "POST",
            "/api/v1/documents",
            json={
                "document_id": doc_id,
                "domain_id": domain_id,
                "file_path": file_path,
            },
        )
    )

    typer.echo(f"✅ {result['message']}")
    typer.echo(f"   Workflow ID: {result['workflow_id']}")
    typer.echo(f"   Status: {result['status']}")
    typer.echo(
        f"\n💡 Check status: python script/workflow_client.py status --workflow-id {result['workflow_id']}"
    )


@app.command()
def ask(
    domain_id: str = typer.Option(..., help="Domain ID"),
    question: str = typer.Option(..., help="Question to ask"),
    user_id: str = typer.Option("test-user", help="User ID"),
    question_id: str | None = typer.Option(
        None, help="Question ID (auto-generated if not provided)"
    ),
) -> None:
    """Ask a question and trigger Q&A workflow."""
    q_id = question_id or f"q-{int(datetime.now().timestamp())}"

    typer.echo("💬 Starting question answering workflow...")
    typer.echo(f"   Domain: {domain_id}")
    typer.echo(f"   Question: {question}")

    result = asyncio.run(
        call_api(
            "POST",
            "/api/v1/questions",
            json={
                "question_id": q_id,
                "question": question,
                "domain_id": domain_id,
                "user_id": user_id,
            },
        )
    )

    typer.echo(f"✅ {result['message']}")
    typer.echo(f"   Workflow ID: {result['workflow_id']}")
    typer.echo(f"   Status: {result['status']}")
    typer.echo(
        f"\n💡 Check status: python script/workflow_client.py status --workflow-id {result['workflow_id']}"
    )


@app.command()
def review(
    reviewable_type: str = typer.Option(..., help="Type: document, answer, etc."),
    reviewable_id: str = typer.Option(..., help="ID of item to review"),
    domain_id: str = typer.Option(..., help="Domain ID"),
    review_id: str | None = typer.Option(
        None, help="Review ID (auto-generated if not provided)"
    ),
) -> None:
    """Create a review task and trigger quality review workflow."""
    r_id = review_id or f"review-{int(datetime.now().timestamp())}"

    typer.echo("📋 Starting quality review workflow...")
    typer.echo(f"   Domain: {domain_id}")
    typer.echo(f"   Type: {reviewable_type}")
    typer.echo(f"   Reviewable ID: {reviewable_id}")

    result = asyncio.run(
        call_api(
            "POST",
            "/api/v1/reviews",
            json={
                "review_id": r_id,
                "reviewable_type": reviewable_type,
                "reviewable_id": reviewable_id,
                "domain_id": domain_id,
            },
        )
    )

    typer.echo(f"✅ {result['message']}")
    typer.echo(f"   Workflow ID: {result['workflow_id']}")
    typer.echo(f"   Status: {result['status']}")


@app.command()
def status(workflow_id: str = typer.Option(..., help="Workflow ID")) -> None:
    """Get status of a workflow."""
    typer.echo("🔍 Checking workflow status...")
    typer.echo(f"   Workflow ID: {workflow_id}")

    result = asyncio.run(call_api("GET", f"/api/v1/workflows/{workflow_id}"))

    typer.echo("\n📊 Status:")
    typer.echo(f"   ID: {result['workflow_id']}")
    typer.echo(f"   Type: {result['type']}")
    typer.echo(f"   Status: {result['status']}")


@app.command()
def health() -> None:
    """Check API health."""
    typer.echo("🏥 Checking API health...")
    typer.echo(f"   URL: {API_URL}")

    result = asyncio.run(call_api("GET", "/health"))

    typer.echo(f"✅ {result['status']}")


if __name__ == "__main__":
    app()
