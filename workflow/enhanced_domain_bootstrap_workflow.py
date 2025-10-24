"""Enhanced Domain Bootstrap Workflow with real-time OpenAI integration and continuous feedback."""

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
    from activity.openai_enhanced import (
        enhanced_domain_research_activity,
        continuous_research_activity,
        deep_question_analysis_activity
    )
    from activity.knowledge_questions import generate_knowledge_questions_activity
    from activity.search import index_weaviate_activity, update_neo4j_graph_activity
    from activity.notification import notify_user_activity
    from activity.supabase import create_domain_activity, update_domain_activity
    from src.app.models.domain import BootstrapInput, BootstrapResult, DomainStatus

logger = structlog.get_logger()


class EnhancedBootstrapStatus(Enum):
    """Enhanced bootstrap workflow status."""
    STARTED = "started"
    RESEARCHING = "researching"
    CONTINUOUS_RESEARCH = "continuous_research"
    ANALYZING = "analyzing"
    INDEXING = "indexing"
    GENERATING_QUESTIONS = "generating_questions"
    DEEP_ANALYSIS = "deep_analysis"
    PENDING_OWNER_FEEDBACK = "pending_owner_feedback"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class EnhancedDomainBootstrapInput:
    """Input for enhanced domain bootstrap workflow."""
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
    enable_continuous_research: bool = True
    enable_deep_analysis: bool = True


@workflow.defn(name="EnhancedDomainBootstrapWorkflow")
class EnhancedDomainBootstrapWorkflow:
    """
    Enhanced domain bootstrap workflow with real-time OpenAI integration and continuous feedback.
    
    This workflow:
    1. Creates domain record
    2. Researches domain using OpenAI with streaming
    3. Runs continuous research in background
    4. Analyzes research results
    5. Indexes knowledge in Weaviate
    6. Updates Neo4j knowledge graph
    7. Generates example questions
    8. Performs deep analysis on top questions
    9. Waits for owner feedback
    10. Completes domain setup
    """

    def __init__(self):
        """Initialize the enhanced bootstrap workflow."""
        self.status: EnhancedBootstrapStatus = EnhancedBootstrapStatus.STARTED
        self.research_results: Optional[Dict[str, Any]] = None
        self.analysis_results: Optional[Dict[str, Any]] = None
        self.domain_config: Optional[Dict[str, Any]] = None
        self.example_questions: List[Dict[str, Any]] = []
        self.continuous_insights: List[Dict[str, Any]] = []
        self.deep_analyses: List[Dict[str, Any]] = []
        self.owner_feedback: Optional[Dict[str, Any]] = None
        self.owner_approved: bool = False
        self.error_message: Optional[str] = None

    @workflow.run
    async def run(self, input: EnhancedDomainBootstrapInput) -> BootstrapResult:
        """Execute the enhanced domain bootstrap workflow."""
        workflow.logger.info(
            "Starting EnhancedDomainBootstrapWorkflow",
            domain_id=input.domain_id,
            title=input.title,
            owner_id=input.owner_id,
        )
        
        self.status = EnhancedBootstrapStatus.STARTED

        try:
            # Step 1: Create initial domain record
            await workflow.execute_activity(
                create_domain_activity,
                args=[input.domain_id, input.owner_id, input.title, input.description],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Step 2: Enhanced OpenAI research with streaming
            self.status = EnhancedBootstrapStatus.RESEARCHING
            workflow.logger.info("Starting enhanced OpenAI research", domain_id=input.domain_id)
            
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
                enhanced_domain_research_activity,
                args=[research_input],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=25),
            )

            # Step 3: Continuous research (runs in background)
            if input.enable_continuous_research:
                self.status = EnhancedBootstrapStatus.CONTINUOUS_RESEARCH
                workflow.logger.info("Starting continuous research", domain_id=input.domain_id)
                
                # Start continuous research tasks
                continuous_tasks = []
                research_focuses = [
                    "Historical development",
                    "Technical aspects", 
                    "Practical applications",
                    "Current trends",
                    "Future directions"
                ]
                
                for focus in research_focuses:
                    task = workflow.execute_activity(
                        continuous_research_activity,
                        args=[input.title, focus, self.continuous_insights],
                        task_queue="ai-processing-queue",
                        start_to_close_timeout=timedelta(minutes=10),
                    )
                    continuous_tasks.append(task)
                
                # Wait for continuous research to complete
                continuous_results = await asyncio.gather(*continuous_tasks, return_exceptions=True)
                
                # Process continuous research results
                for result in continuous_results:
                    if isinstance(result, dict) and "new_insights" in result:
                        self.continuous_insights.extend(result["new_insights"])

            # Step 4: Analyze research results
            self.status = EnhancedBootstrapStatus.ANALYZING
            workflow.logger.info("Analyzing research results", domain_id=input.domain_id)
            
            # Combine research results with continuous insights
            combined_research = {
                **self.research_results,
                "continuous_insights": self.continuous_insights
            }
            
            self.analysis_results = await workflow.execute_activity(
                analyze_research_results_activity,
                args=[combined_research, input.title],
                task_queue="ai-processing-queue",
                start_to_close_timeout=timedelta(minutes=15),
            )

            # Step 5: Generate domain configuration
            self.domain_config = self._generate_domain_config(input, self.analysis_results)
            
            # Step 6: Index knowledge in Weaviate
            self.status = EnhancedBootstrapStatus.INDEXING
            workflow.logger.info("Indexing knowledge in Weaviate", domain_id=input.domain_id)
            
            weaviate_data = {
                "domain_id": input.domain_id,
                "domain_name": input.title,
                "domain_description": input.description,
                "topics": self.analysis_results.get("topics", []),
                "research_summary": self.research_results.get("summary", ""),
                "continuous_insights": self.continuous_insights,
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

            # Step 7: Update Neo4j knowledge graph
            workflow.logger.info("Updating Neo4j knowledge graph", domain_id=input.domain_id)
            
            neo4j_data = {
                "domain_id": input.domain_id,
                "domain_name": input.title,
                "domain_description": input.description,
                "topics": self.analysis_results.get("topics", []),
                "research_sources": self.research_results.get("sources", []),
                "knowledge_gaps": self.research_results.get("knowledge_gaps", []),
                "continuous_insights": self.continuous_insights,
                "owner_id": input.owner_id,
            }
            
            neo4j_result = await workflow.execute_activity(
                update_neo4j_graph_activity,
                args=[neo4j_data],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=8),
            )

            # Step 8: Generate example questions
            self.status = EnhancedBootstrapStatus.GENERATING_QUESTIONS
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

            # Step 9: Deep analysis on top questions
            if input.enable_deep_analysis and self.example_questions:
                self.status = EnhancedBootstrapStatus.DEEP_ANALYSIS
                workflow.logger.info("Performing deep analysis on top questions", domain_id=input.domain_id)
                
                # Get top 3 questions for deep analysis
                top_questions = sorted(
                    self.example_questions, 
                    key=lambda x: x.get("relevance_score", 0), 
                    reverse=True
                )[:3]
                
                deep_analysis_tasks = []
                for question in top_questions:
                    domain_context = {
                        "domain_name": input.title,
                        "domain_description": input.description,
                        "research_summary": self.research_results.get("summary", ""),
                        "topics": self.analysis_results.get("topics", []),
                        "continuous_insights": self.continuous_insights
                    }
                    
                    task = workflow.execute_activity(
                        deep_question_analysis_activity,
                        args=[question["question"], domain_context, input.research_depth],
                        task_queue="ai-processing-queue",
                        start_to_close_timeout=timedelta(minutes=15),
                    )
                    deep_analysis_tasks.append(task)
                
                # Wait for deep analysis to complete
                deep_results = await asyncio.gather(*deep_analysis_tasks, return_exceptions=True)
                
                # Process deep analysis results
                for i, result in enumerate(deep_results):
                    if isinstance(result, dict):
                        self.deep_analyses.append({
                            "question": top_questions[i]["question"],
                            "analysis": result
                        })

            # Step 10: Update domain with research results
            await workflow.execute_activity(
                update_domain_activity,
                args=[input.domain_id, self.domain_config],
                task_queue="storage-queue",
                start_to_close_timeout=timedelta(minutes=2),
            )

            # Step 11: Notify owner for feedback
            self.status = EnhancedBootstrapStatus.PENDING_OWNER_FEEDBACK
            workflow.logger.info("Requesting owner feedback", domain_id=input.domain_id)
            
            feedback_message = self._create_enhanced_owner_feedback_message(
                input, self.example_questions, self.continuous_insights, self.deep_analyses
            )
            
            await workflow.execute_activity(
                notify_user_activity,
                args=[
                    input.owner_id,
                    f"Domain '{input.title}' Research Complete - Enhanced Feedback Required",
                    feedback_message,
                ],
                task_queue="general-queue",
                start_to_close_timeout=timedelta(seconds=30),
            )

            # Upsert Search Attributes for HITL inbox
            await workflow.upsert_search_attributes(
                assignee=[input.owner_id],
                queue=["enhanced-domain-bootstrap"],
                status=[EnhancedBootstrapStatus.PENDING_OWNER_FEEDBACK.value],
                priority=["high"],
                domain_id=[input.domain_id],
                domain_name=[input.title],
                owner_id=[input.owner_id],
                due_at=[(workflow.now() + timedelta(days=3)).isoformat()],
            )

            # Step 12: Wait for owner feedback (with timeout)
            try:
                await workflow.wait_condition(
                    lambda: self.owner_approved, 
                    timeout=timedelta(days=7)
                )
                
                if self.owner_approved:
                    self.status = EnhancedBootstrapStatus.COMPLETED
                    workflow.logger.info("Enhanced domain bootstrap completed", domain_id=input.domain_id)
                    
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
                            f"Your domain '{input.title}' is now active and ready for contributions. The knowledge base has been populated with comprehensive research and is ready to answer questions.",
                        ],
                        task_queue="general-queue",
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                else:
                    self.status = EnhancedBootstrapStatus.FAILED
                    self.error_message = "Owner did not approve the domain configuration"
                    
            except asyncio.TimeoutError:
                self.status = EnhancedBootstrapStatus.FAILED
                self.error_message = "Owner feedback timed out"
                workflow.logger.warning("Owner feedback timed out", domain_id=input.domain_id)

        except Exception as e:
            self.status = EnhancedBootstrapStatus.FAILED
            self.error_message = str(e)
            workflow.logger.error(
                f"Enhanced domain bootstrap workflow failed: domain_id={input.domain_id}, error={e!s}"
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
    async def submit_enhanced_owner_feedback(self, feedback: Dict[str, Any]):
        """Signal for owner to submit enhanced feedback on domain configuration."""
        workflow.logger.info("Owner submitted enhanced feedback", feedback=feedback)
        self.owner_feedback = feedback
        self.owner_approved = feedback.get("approved", False)

    @workflow.query
    def get_enhanced_bootstrap_status(self) -> Dict[str, Any]:
        """Query current enhanced bootstrap status."""
        return {
            "status": self.status.value,
            "research_results": self.research_results,
            "analysis_results": self.analysis_results,
            "domain_config": self.domain_config,
            "example_questions": self.example_questions,
            "continuous_insights": self.continuous_insights,
            "deep_analyses": self.deep_analyses,
            "owner_feedback": self.owner_feedback,
            "owner_approved": self.owner_approved,
            "error_message": self.error_message,
        }

    def _generate_domain_config(
        self, 
        input: EnhancedDomainBootstrapInput, 
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

    def _create_enhanced_owner_feedback_message(
        self, 
        input: EnhancedDomainBootstrapInput, 
        example_questions: List[Dict[str, Any]],
        continuous_insights: List[Dict[str, Any]],
        deep_analyses: List[Dict[str, Any]]
    ) -> str:
        """Create enhanced owner feedback message with all insights."""
        message = f"""
🎉 Enhanced Domain Research Complete!

Your domain "{input.title}" has been thoroughly researched and analyzed with advanced AI capabilities. Here's what we've discovered:

📊 Research Summary:
{self.research_results.get('summary', 'Research completed successfully') if self.research_results else 'Research in progress'}

🏷️ Discovered Topics:
{', '.join(self.analysis_results.get('topics', [])[:10]) if self.analysis_results else 'Topics being analyzed'}

💡 Continuous Insights ({len(continuous_insights)}):
"""
        
        for insight in continuous_insights[:5]:
            message += f"• {insight.get('insight', 'Insight being processed')}\n"
        
        message += f"""
❓ Example Questions the Knowledge Base Can Answer:

"""
        
        for i, question in enumerate(example_questions[:5], 1):
            message += f"{i}. {question.get('question', 'Question being generated')}\n"
        
        if deep_analyses:
            message += f"""
🔍 Deep Analysis on Top Questions:

"""
            for analysis in deep_analyses[:3]:
                message += f"• {analysis.get('question', 'Question')}: {analysis.get('analysis', {}).get('answer', 'Analysis in progress')[:100]}...\n"
        
        message += f"""
Please review these results and provide feedback:
1. Which questions are most relevant for your domain?
2. What additional topics should be covered?
3. What should be removed or modified?
4. Any specific requirements for contributions?
5. Rate the continuous insights (1-5 scale)

Your feedback will help us fine-tune the knowledge base for your specific needs.
"""
        
        return message
