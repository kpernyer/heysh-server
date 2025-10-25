"""Multi-queue Temporal worker setup.
Supports running workers for different queues with specific resource requirements.
"""

import asyncio
import os
from enum import Enum

import structlog
import uvicorn
from fastapi import FastAPI
from temporalio.client import Client
from temporalio.contrib.pydantic import pydantic_data_converter
from temporalio.worker import Worker

logger = structlog.get_logger()


class WorkerType(Enum):
    """Different worker types with specific capabilities."""

    AI_PROCESSING = "ai-processing"
    STORAGE = "storage"
    GENERAL = "general"


class WorkerConfig:
    """Configuration for different worker types."""

    WORKER_CONFIGS = {
        WorkerType.AI_PROCESSING: {
            "task_queue": "ai-processing-queue",
            "max_concurrent_activities": 5,
            "max_concurrent_workflow_tasks": 10,
            "resource_requirements": {
                "requires_gpu": True,
                "min_memory_gb": 16,
                "cpu_cores": 4,
            },
            "description": "Handles AI model inference, document analysis, and NLP tasks",
        },
        WorkerType.STORAGE: {
            "task_queue": "storage-queue",
            "max_concurrent_activities": 20,
            "max_concurrent_workflow_tasks": 20,
            "resource_requirements": {
                "requires_gpu": False,
                "min_memory_gb": 8,
                "cpu_cores": 2,
                "requires_fast_storage": True,
            },
            "description": "Handles database operations, file storage, and indexing",
        },
        WorkerType.GENERAL: {
            "task_queue": "general-queue",
            "max_concurrent_activities": 50,
            "max_concurrent_workflow_tasks": 50,
            "resource_requirements": {
                "requires_gpu": False,
                "min_memory_gb": 4,
                "cpu_cores": 2,
            },
            "description": "Handles notifications, coordination, and lightweight tasks",
        },
    }


class MultiQueueWorkerManager:
    """Manages multiple Temporal workers for different queues."""

    def __init__(self):
        self.workers: list[Worker] = []
        self.client = None
        self.app = FastAPI()
        self._setup_health_check()

    def _setup_health_check(self):
        """Setup health check endpoints for Kubernetes probes."""
        from datetime import datetime

        @self.app.get("/health")
        async def health():
            """Basic health check."""
            return {"status": "healthy"}

        @self.app.get("/health/startup")
        async def startup_probe():
            """Startup probe - check worker initialization."""
            workers_ready = len(self.workers) > 0 and all(
                w.is_running() for w in self.workers
            )
            return {
                "started": workers_ready,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "workers": {
                    "count": len(self.workers),
                    "running": sum(1 for w in self.workers if w.is_running()),
                },
            }

        @self.app.get("/health/ready")
        async def readiness_probe():
            """Readiness probe - can process tasks."""
            if not self.client:
                return {
                    "ready": False,
                    "message": "Temporal client not connected",
                }, 503

            try:
                # Check if workers are running and connected
                workers_ready = all(w.is_running() for w in self.workers)

                if not workers_ready:
                    return {
                        "ready": False,
                        "message": f"Not all workers running: {len([w for w in self.workers if w.is_running()])}/{len(self.workers)}",
                    }, 503

                return {
                    "ready": True,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "workers": [
                        {
                            "task_queue": w.task_queue,
                            "running": w.is_running(),
                        }
                        for w in self.workers
                    ],
                }
            except Exception as e:
                return {
                    "ready": False,
                    "message": str(e),
                }, 503

        @self.app.get("/health/live")
        async def liveness_probe():
            """Liveness probe - check if worker should be restarted."""
            if not self.client:
                return {
                    "alive": False,
                    "message": "Temporal client not connected",
                }, 503

            try:
                # Simple check - just verify we have running workers
                workers_alive = len(self.workers) > 0

                return {
                    "alive": workers_alive,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "worker_count": len(self.workers),
                }
            except Exception as e:
                return {
                    "alive": False,
                    "error": str(e),
                }, 503

    async def connect_temporal(self) -> Client:
        """Connect to Temporal server."""
        temporal_address = os.getenv("TEMPORAL_ADDRESS", "localhost:7233")
        temporal_namespace = os.getenv("TEMPORAL_NAMESPACE", "default")
        temporal_api_key = os.getenv("TEMPORAL_API_KEY")

        logger.info(
            "Connecting to Temporal",
            address=temporal_address,
            namespace=temporal_namespace,
        )

        connect_config = {
            "namespace": temporal_namespace,
        }

        if temporal_api_key:
            from temporalio.client import TLSConfig

            connect_config["tls"] = TLSConfig()
            connect_config["api_key"] = temporal_api_key
            logger.info("Using Temporal Cloud with TLS")
        else:
            logger.info("Using local Temporal server")

        self.client = await Client.connect(
            temporal_address,
            data_converter=pydantic_data_converter,
            **connect_config
        )
        return self.client

    async def create_ai_processing_worker(self) -> Worker:
        """Create worker for AI processing tasks."""
        from activity.ai_agent_activities import (
            execute_ai_agent_activity,
            extract_document_content,
        )
        from activity.document_contribution_activities import (
            assess_document_relevance,
            extract_document_topics,
            generate_summary_for_notification,
        )

        config = WorkerConfig.WORKER_CONFIGS[WorkerType.AI_PROCESSING]

        worker = Worker(
            self.client,
            task_queue=config["task_queue"],
            workflows=[],  # AI workers typically don't run workflows
            activities=[
                execute_ai_agent_activity,
                extract_document_content,
                assess_document_relevance,
                extract_document_topics,
                generate_summary_for_notification,
            ],
            max_concurrent_activities=config["max_concurrent_activities"],
            max_concurrent_workflow_tasks=config["max_concurrent_workflow_tasks"],
        )

        logger.info(
            "Created AI processing worker",
            task_queue=config["task_queue"],
            requirements=config["resource_requirements"],
        )

        return worker

    async def create_storage_worker(self) -> Worker:
        """Create worker for storage and database operations."""
        from activity.document import (
            download_document_activity,
            extract_text_activity,
            generate_embeddings_activity,
        )
        from activity.document_contribution_activities import (
            archive_rejected_document,
            index_to_weaviate,
            store_document_metadata,
            update_neo4j_graph,
        )
        from activity.search import (
            find_related_documents_activity,
            search_documents_activity,
        )

        config = WorkerConfig.WORKER_CONFIGS[WorkerType.STORAGE]

        worker = Worker(
            self.client,
            task_queue=config["task_queue"],
            workflows=[],
            activities=[
                download_document_activity,
                extract_text_activity,
                generate_embeddings_activity,
                index_to_weaviate,
                update_neo4j_graph,
                store_document_metadata,
                archive_rejected_document,
                search_documents_activity,
                find_related_documents_activity,
            ],
            max_concurrent_activities=config["max_concurrent_activities"],
            max_concurrent_workflow_tasks=config["max_concurrent_workflow_tasks"],
        )

        logger.info(
            "Created storage worker",
            task_queue=config["task_queue"],
            requirements=config["resource_requirements"],
        )

        return worker

    async def create_general_worker(self) -> Worker:
        """Create worker for general tasks and workflow orchestration."""
        from activity.document_contribution_activities import (
            build_graph_relations,
            get_next_controller,
            notify_stakeholders,
        )
        from activity.supabase import (
            apply_review_decision_activity,
            assign_review_activity,
            create_review_task_activity,
            notify_contributor_activity,
            update_quality_score_activity,
        )
        from workflow.document_contribution_workflow import (
            DocumentContributionWorkflow,
        )
        from workflow.document_processing import DocumentProcessingWorkflow
        from workflow.quality_review import QualityReviewWorkflow
        from workflow.question_answering import QuestionAnsweringWorkflow

        config = WorkerConfig.WORKER_CONFIGS[WorkerType.GENERAL]

        worker = Worker(
            self.client,
            task_queue=config["task_queue"],
            workflows=[
                DocumentContributionWorkflow,
                DocumentProcessingWorkflow,
                QualityReviewWorkflow,
                QuestionAnsweringWorkflow,
            ],
            activities=[
                notify_stakeholders,
                get_next_controller,
                build_graph_relations,
                create_review_task_activity,
                assign_review_activity,
                apply_review_decision_activity,
                update_quality_score_activity,
                notify_contributor_activity,
            ],
            max_concurrent_activities=config["max_concurrent_activities"],
            max_concurrent_workflow_tasks=config["max_concurrent_workflow_tasks"],
        )

        logger.info(
            "Created general worker",
            task_queue=config["task_queue"],
            requirements=config["resource_requirements"],
        )

        return worker

    async def start_workers(self, worker_types: list[WorkerType]):
        """Start specified worker types."""
        if not self.client:
            await self.connect_temporal()

        # Create workers based on requested types
        for worker_type in worker_types:
            if worker_type == WorkerType.AI_PROCESSING:
                worker = await self.create_ai_processing_worker()
            elif worker_type == WorkerType.STORAGE:
                worker = await self.create_storage_worker()
            elif worker_type == WorkerType.GENERAL:
                worker = await self.create_general_worker()
            else:
                logger.warning(f"Unknown worker type: {worker_type}")
                continue

            self.workers.append(worker)

        # Run all workers concurrently
        logger.info(f"Starting {len(self.workers)} workers")
        await asyncio.gather(*[w.run() for w in self.workers])

    async def run_with_health_check(self, worker_types: list[WorkerType]):
        """Run workers with health check server."""
        port = int(os.getenv("PORT", 8080))

        async def run_health_server():
            config = uvicorn.Config(
                self.app,
                host="0.0.0.0",
                port=port,
                log_level="info",
            )
            server = uvicorn.Server(config)
            await server.serve()

        # Start workers and health server concurrently
        await asyncio.gather(
            self.start_workers(worker_types),
            run_health_server(),
        )


def get_worker_types_from_env() -> list[WorkerType]:
    """Get worker types to run from environment variable."""
    worker_types_str = os.getenv("WORKER_TYPES", "general")
    worker_type_names = [t.strip() for t in worker_types_str.split(",")]

    worker_types = []
    for name in worker_type_names:
        try:
            if name == "ai-processing":
                worker_types.append(WorkerType.AI_PROCESSING)
            elif name == "storage":
                worker_types.append(WorkerType.STORAGE)
            elif name == "general":
                worker_types.append(WorkerType.GENERAL)
            else:
                logger.warning(f"Unknown worker type in env: {name}")
        except ValueError:
            logger.warning(f"Invalid worker type: {name}")

    return worker_types or [WorkerType.GENERAL]


async def main():
    """Main entry point for multi-queue worker."""
    manager = MultiQueueWorkerManager()
    worker_types = get_worker_types_from_env()

    logger.info(
        "Starting multi-queue worker",
        worker_types=[wt.value for wt in worker_types],
    )

    # Check if running in cloud environment
    if "PORT" in os.environ:
        await manager.run_with_health_check(worker_types)
    else:
        await manager.start_workers(worker_types)


if __name__ == "__main__":
    asyncio.run(main())
