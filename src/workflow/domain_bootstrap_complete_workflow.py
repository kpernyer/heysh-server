"""Complete Domain Bootstrap Workflow with OpenAI research, vector storage, and owner feedback."""

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from temporalio import workflow
from temporalio.common import RetryPolicy

# Allow imports from src.app for activities
with workflow.unsafe.imports_passed_through():
    from activity.domain_research import research_domain_activity, analyze_research_results_activity
    from activity.ai import generate_knowledge_questions_activity
    from activity.search import index_weaviate_activity, update_neo4j_graph_activity
    from activity.notification import notify_user_activity
    from activity.supabase import create_domain_activity, update_domain_activity
    from src.app.models.domain import BootstrapInput, BootstrapResult, DomainStatus

logger = structlog.get_logger()


class BootstrapStatus(Enum):
    """Bootstrap workflow status."""
    STARTED = "started"
    RESEARCHING = "researching"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    GENERATING_QUESTIONS = "generating_questions"
    PENDING_OWNER_FEEDBACK = "pending_owner_feedback"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DomainBootstrapInput:
    """Input for complete domain bootstrap workflow."""
    domain_id: str
    owner_id: str
    title: str
    description: str
    slug: Optional[str] = None
    initial_topics: List[str] = None
    target_audience: List[str] = None
    research_focus: Optional[str] = None
    quality_requirements: Dict[str, Any] = None
    research_depth: str = "comprehensive"
    include_historical: bool = True
    include_technical: bool = True
    include_practical: bool = True


@workflow.defn(name="DomainBootstrapCompleteWorkflow")
class DomainBootstrapCompleteWorkflow:
    """
    Complete domain bootstrap workflow with OpenAI research, vector storage, and owner feedback.
    
    This workflow:
    1. Creates domain record
    2. Researches domain using OpenAI
    3. Analyzes research results
    4. Indexes knowledge in Weaviate
    5. Updates Neo4j knowledge graph
    6. Generates example questions
    7. Waits for owner feedback
    8. Completes domain setup
    """

    def __init__(self):
        """Initialize the bootstrap workflow."""
        self.status: BootstrapStatus = BootstrapStatus.STARTED
        self.research_results: Optional[Dict[str, Any]] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.domain_config: Optional[Dict[str, Any]] = None
        self.example_questions: List[Dict[str, Any]] = []
        self.owner_feedback: Optional[Dict[str, Any]] = None
        self.owner_approved: bool = False
        self.error_message: Optional[str] = None

    @workflow.run
    async def run(self, input: DomainBootstrapInput) -> BootstrapResult:
        """Execute the complete domain bootstrap workflow."""
        workflow.logger.info(
            "Starting DomainBootstrapCompleteWorkflow",
            domain_id=input.domain_id,
            title=input.title,
            owner_id=input.owner_id,
        )
        
        self.status = BootstrapStatus.STARTED

        try:
            # Step 1: Create initial domain record
            await workflow.execute_activity(
                create_domain_activity,
                args=[input.domain_id, input.owner_id, input.title, input.description],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Step 2: Research domain using OpenAI
            self.status = BootstrapStatus.RESEARCHING
            workflow.logger.info("Starting OpenAI domain research", domain_id=input.domain_id)
            
            research_input = {
                "domain_name": input.title,
                "domain_description": input.description,
                "initial_topics": input.initial_topics or [],
                "target_audience": input.target_audience or [],
                "research_focus": input.research_focus,
                "research_depth": input.research_depth,
                "include_historical": input.include_historical,
                "include_technical": input.include_technical,
                "include_practical": input.include_practical,
            }
            
            self.research_results = await workflow.execute_activity(
                research_domain_activity,
                args=[research_input],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=20),
            )

            # Step 3: Analyze research results
            self.status = BootstrapStatus.ANALYZING
            workflow.logger.info("Analyzing research results", domain_id=input.domain_id)
            
            self.analysis_results = await workflow.execute_activity(
                analyze_research_results_activity,
                args=[self.research_results, input.title],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=15),
            )

            # Step 4: Generate domain configuration
            self.domain_config = self._generate_domain_config(input, self.analysis_results)
            
            # Step 5: Index knowledge in Weaviate
            self.status = BootstrapStatus.INDEXING
            workflow.logger.info("Indexing knowledge in Weaviate", domain_id=input.domain_id)
            
            weaviate_data = {
                "domain_id": input.domain_id,
                "domain_name": input.title,
                "domain_description": input.description,
                "topics": self.analysis_results.get("topics", []),
                "research_summary": self.research_results.get("summary", ""),
                "quality_criteria": self.domain_config.get("quality_criteria", {}),
                "search_attributes": self.domain_config.get("search_attributes", {}),
                "owner_id": input.owner_id,
            }
            
            weaviate_result = await workflow.execute_activity(
                index_weaviate_activity,
                args=[weaviate_data],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=10),
            )

            # Step 6: Update Neo4j knowledge graph
            workflow.logger.info("Updating Neo4j knowledge graph", domain_id=input.domain_id)
            
            neo4j_data = {
                "domain_id": input.domain_id,
                "domain_name": input.title,
                "domain_description": input.description,
                "topics": self.analysis_results.get("topics", []),
                "research_sources": self.research_results.get("sources", []),
                "knowledge_gaps": self.research_results.get("knowledge_gaps", []),
                "owner_id": input.owner_id,
            }
            
            neo4j_result = await workflow.execute_activity(
                update_neo4j_graph_activity,
                args=[neo4j_data],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=8),
            )

            # Step 7: Generate example questions
            self.status = BootstrapStatus.GENERATING_QUESTIONS
            workflow.logger.info("Generating example questions", domain_id=input.domain_id)
            
            questions_input = {
                "domain_name": input.title,
                "domain_description": input.description,
                "topics": self.analysis_results.get("topics", []),
                "research_summary": self.research_results.get("summary", ""),
                "target_audience": input.target_audience or [],
            }
            
            self.example_questions = await workflow.execute_activity(
                generate_knowledge_questions_activity,
                args=[questions_input],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=10),
            )

            # Step 8: Update domain with research results
            await workflow.execute_activity(
                update_domain_activity,
                args=[input.domain_id, self.domain_config],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Step 9: Notify owner for feedback
            self.status = BootstrapStatus.PENDING_OWNER_FEEDBACK
            workflow.logger.info("Requesting owner feedback", domain_id=input.domain_id)
            
            feedback_message = self._create_owner_feedback_message(input, self.example_questions)
            
            await workflow.execute_activity(
                notify_user_activity,
                args=[
                    input.owner_id,
                    f"Domain '{input.title}' Research Complete - Feedback Required",
                    feedback_message,
                ],
                task_queue="general-queue",
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Upsert Search Attributes for HITL inbox
            await workflow.upsert_search_attributes(
                assignee=[input.owner_id],
                queue=["domain-bootstrap"],
                status=[BootstrapStatus.PENDING_OWNER_FEEDBACK.value],
                priority=["high"],
                domain_id=[input.domain_id],
                domain_name=[input.title],
                owner_id=[input.owner_id],
                due_at=[(workflow.now() + timedelta(days=3)).isoformat()],
            )

            # Step 10: Wait for owner feedback (with timeout)
            try:
                await workflow.wait_condition(
                    lambda: self.owner_approved, 
                    timeout=timedelta(days=7)
                )
                
                if self.owner_approved:
                    self.status = BootstrapStatus.COMPLETED
                    workflow.logger.info("Domain bootstrap completed", domain_id=input.domain_id)
                    
                    # Final domain update
                    await workflow.execute_activity(
                        update_domain_activity,
                        args=[input.domain_id, {"status": DomainStatus.ACTIVE.value}],
                        task_queue="storage-queue",
                        start_to_close_timeout=timedelta(minutes=1),
                    )
                    
                    # Notify owner of completion
                    await workflow.execute_activity(
                        notify_user_activity,
                        args=[
                            input.owner_id,
                            f"Domain '{input.title}' is Now Active",
                            f"Your domain '{input.title}' is now active and ready for contributions. The knowledge base has been populated with research and is ready to answer questions.",
                        ],
                        task_queue="general-queue",
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                else:
                    self.status = BootstrapStatus.FAILED
                    self.error_message = "Owner did not approve the domain configuration"
                    
            except asyncio.TimeoutError:
                self.status = BootstrapStatus.FAILED
                self.error_message = "Owner feedback timed out"
                workflow.logger.warning("Owner feedback timed out", domain_id=input.domain_id)

        except Exception as e:
            self.status = BootstrapStatus.FAILED
            self.error_message = str(e)
            workflow.logger.error(
                f"Domain bootstrap workflow failed: domain_id={input.domain_id}, error={e!s}"
            )
            raise

        # Final Search Attributes update
        await workflow.upsert_search_attributes(
            status=[self.status.value],
            error_message=[self.error_message or ""],
            owner_approved=[self.owner_approved],
        )

        return BootstrapResult(
            domain_id=input.domain_id,
            status=self.status.value,
            research_summary=self.research_results.get("summary", "") if self.research_results else "",
            discovered_topics=self.analysis_results.get("topics", []) if self.analysis_results else [],
            quality_criteria=self.domain_config.get("quality_criteria", {}) if self.domain_config else {},
            search_attributes=self.domain_config.get("search_attributes", {}) if self.domain_config else {},
            research_sources=self.research_results.get("sources", []) if self.research_results else [],
            recommendations=self.analysis_results.get("recommendations", []) if self.analysis_results else [],
        )

    @workflow.signal
    async def submit_owner_feedback(self, feedback: Dict[str, Any]):
        """Signal for owner to submit feedback on domain configuration."""
        workflow.logger.info("Owner submitted feedback", feedback=feedback)
        self.owner_feedback = feedback
        self.owner_approved = feedback.get("approved", False)

    @workflow.query
    def get_bootstrap_status(self) -> Dict[str, Any]:
        """Query current bootstrap status."""
        return {
            "status": self.status.value,
            "research_results": self.research_results,
            "analysis_results": self.analysis_results,
            "domain_config": self.domain_config,
            "example_questions": self.example_questions,
            "owner_feedback": self.owner_feedback,
            "owner_approved": self.owner_approved,
            "error_message": self.error_message,
        }

    def _generate_domain_config(
        self, 
        input: DomainBootstrapInput, 
        analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate domain configuration from analysis results."""
        return {
            "topics": analysis_results.get("topics", input.initial_topics or []),
            "quality_criteria": {
                "min_length": 1000,
                "quality_threshold": 7.0,
                "required_sections": ["abstract", "introduction", "conclusion", "references"],
                "technical_depth_required": True,
                "safety_considerations_required": True,
                "practical_applications_required": True,
            },
            "search_attributes": {
                "domain_id": input.domain_id,
                "domain_name": input.title,
                "owner_id": input.owner_id,
                "topics": analysis_results.get("topics", []),
                "target_audience": input.target_audience or [],
            },
            "bootstrap_prompt": analysis_results.get("bootstrap_prompt", ""),
            "research_steps": analysis_results.get("research_steps", []),
            "target_audience": input.target_audience or [],
        }

    def _create_owner_feedback_message(
        self, 
        input: DomainBootstrapInput, 
        example_questions: List[Dict[str, Any]]
    ) -> str:
        """Create owner feedback message with example questions."""
        message = f"""
🎉 Domain Research Complete!

Your domain "{input.title}" has been thoroughly researched and analyzed. Here's what we've discovered:

📊 Research Summary:
{self.research_results.get('summary', 'Research completed successfully') if self.research_results else 'Research in progress'}

🏷️ Discovered Topics:
{', '.join(self.analysis_results.get('topics', [])[:10]) if self.analysis_results else 'Topics being analyzed'}

❓ Example Questions the Knowledge Base Can Answer:

"""
        
        for i, question in enumerate(example_questions[:5], 1):
            message += f"{i}. {question.get('question', 'Question being generated')}\n"
        
        message += f"""
Please review these questions and provide feedback:
1. Which questions are most relevant for your domain?
2. What additional topics should be covered?
3. What should be removed or modified?
4. Any specific requirements for contributions?

Your feedback will help us fine-tune the knowledge base for your specific needs.
"""
        
        return message
