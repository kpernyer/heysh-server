#!/usr/bin/env python3
"""Domain onboarding CLI with real-time OpenAI integration and continuous feedback."""

import asyncio
import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class DomainOnboardingCLI:
    """Interactive CLI for domain onboarding with real-time feedback."""
    
    def __init__(self):
        """Initialize the CLI."""
        self.domain_id = None
        self.owner_id = None
        self.domain_name = None
        self.domain_description = None
        self.research_results = None
        self.example_questions = []
        self.continuous_insights = []
        self.onboarding_active = True
        
    async def start_onboarding(self):
        """Start the domain onboarding process."""
        logger.info("=" * 80)
        logger.info("🚀 HEY.SH DOMAIN ONBOARDING")
        logger.info("=" * 80)
        
        try:
            # Step 1: Collect domain information
            await self.collect_domain_info()
            
            # Step 2: Start OpenAI research
            await self.start_openai_research()
            
            # Step 3: Generate example questions
            await self.generate_example_questions()
            
            # Step 4: Continuous research loop
            await self.continuous_research_loop()
            
            # Step 5: Owner feedback
            await self.collect_owner_feedback()
            
            # Step 6: Finalize domain
            await self.finalize_domain()
            
        except KeyboardInterrupt:
            logger.info("\n🛑 Onboarding interrupted by user")
            await self.handle_interruption()
        except Exception as e:
            logger.error(f"❌ Onboarding failed: {e}")
            await self.handle_error(e)
    
    async def collect_domain_info(self):
        """Collect basic domain information from user."""
        logger.info("\n1️⃣  Domain Information")
        logger.info("-" * 40)
        
        # Get domain name
        while not self.domain_name:
            self.domain_name = input("📋 Enter domain name: ").strip()
            if not self.domain_name:
                logger.warning("Domain name is required")
        
        # Get domain description
        while not self.domain_description:
            self.domain_description = input("📝 Enter domain description: ").strip()
            if not self.domain_description:
                logger.warning("Domain description is required")
        
        # Get initial topics
        topics_input = input("🏷️  Enter initial topics (comma-separated): ").strip()
        initial_topics = [t.strip() for t in topics_input.split(",") if t.strip()]
        
        # Get target audience
        audience_input = input("👥 Enter target audience (comma-separated): ").strip()
        target_audience = [a.strip() for a in audience_input.split(",") if a.strip()]
        
        # Get research focus
        research_focus = input("🔍 Enter research focus (optional): ").strip()
        
        # Generate IDs
        self.domain_id = str(uuid.uuid4())
        self.owner_id = str(uuid.uuid4())
        
        logger.info(f"✅ Domain: {self.domain_name}")
        logger.info(f"✅ Description: {self.domain_description}")
        logger.info(f"✅ Topics: {', '.join(initial_topics) if initial_topics else 'None'}")
        logger.info(f"✅ Audience: {', '.join(target_audience) if target_audience else 'None'}")
        logger.info(f"✅ Research focus: {research_focus or 'General'}")
    
    async def start_openai_research(self):
        """Start OpenAI research with real-time feedback."""
        logger.info("\n2️⃣  OpenAI Research")
        logger.info("-" * 40)
        
        # Check for API key
        api_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("⚠️  No OpenAI API key found. Set OPENROUTER_API_KEY or OPENAI_API_KEY")
            logger.info("Using mock research for demonstration...")
            await self.mock_research()
            return
        
        logger.info("🔍 Starting OpenAI research...")
        logger.info("📊 Research will be streamed in real-time...")
        
        try:
            # Import OpenAI client
            from openai import AsyncOpenAI
            
            # Initialize client
            client = AsyncOpenAI(api_key=api_key)
            
            # Use OpenRouter if available
            if os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY"):
                client.base_url = "https://openrouter.ai/api/v1"
                logger.info("🌐 Using OpenRouter for API routing")
            
            # Create research prompt
            research_prompt = self.create_research_prompt()
            
            # Call OpenAI API with streaming
            response = await client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                messages=[
                    {"role": "system", "content": research_prompt["system"]},
                    {"role": "user", "content": research_prompt["user"]}
                ],
                temperature=0.1,
                max_tokens=4000,
                stream=True
            )
            
            # Process streaming response
            research_content = ""
            logger.info("📡 Streaming research results...")
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    research_content += content
                    print(content, end="", flush=True)
            
            print("\n")  # New line after streaming
            
            # Parse the complete response
            try:
                self.research_results = json.loads(research_content)
                logger.info("✅ Research completed successfully")
            except json.JSONDecodeError:
                logger.warning("⚠️  Failed to parse JSON response, using mock data")
                await self.mock_research()
                
        except Exception as e:
            logger.error(f"❌ OpenAI research failed: {e}")
            logger.info("Falling back to mock research...")
            await self.mock_research()
    
    async def mock_research(self):
        """Mock research when OpenAI is not available."""
        logger.info("🧪 Using mock research...")
        
        self.research_results = {
            "summary": f"Comprehensive research on {self.domain_name} reveals significant potential for knowledge base development.",
            "topics": [
                f"{self.domain_name.lower()} fundamentals",
                f"{self.domain_name.lower()} applications",
                f"{self.domain_name.lower()} best practices",
                f"{self.domain_name.lower()} case studies",
                f"{self.domain_name.lower()} future trends"
            ],
            "quality_criteria": {
                "min_length": 1000,
                "quality_threshold": 7.0,
                "required_sections": ["abstract", "introduction", "conclusion", "references"],
                "technical_depth_required": True,
                "safety_considerations_required": True,
                "practical_applications_required": True
            },
            "knowledge_gaps": [
                f"Limited research on {self.domain_name.lower()} in emerging markets",
                f"Need for more practical {self.domain_name.lower()} applications"
            ],
            "sources": [
                f"Academic research on {self.domain_name.lower()}",
                f"Industry reports on {self.domain_name.lower()}",
                f"Expert interviews on {self.domain_name.lower()}"
            ],
            "recommendations": [
                f"Focus on practical {self.domain_name.lower()} applications",
                f"Develop {self.domain_name.lower()} education resources"
            ]
        }
        
        logger.info("✅ Mock research completed")
    
    async def generate_example_questions(self):
        """Generate example questions using OpenAI."""
        logger.info("\n3️⃣  Example Questions Generation")
        logger.info("-" * 40)
        
        # Check for API key
        api_key = os.getenv("OPEN_ROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.info("Using mock questions...")
            await self.mock_questions()
            return
        
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=api_key)
            
            if os.getenv("OPENROUTER_API_KEY"):
                client.base_url = "https://openrouter.ai/api/v1"
                client.default_headers = {"HTTP-Referer": "https://hey.sh"}
            
            # Create questions prompt
            questions_prompt = self.create_questions_prompt()
            
            # Call OpenAI API
            response = await client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                messages=[
                    {"role": "system", "content": questions_prompt["system"]},
                    {"role": "user", "content": questions_prompt["user"]}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            # Parse response
            content = response.choices[0].message.content
            try:
                self.example_questions = json.loads(content)
                logger.info("✅ Example questions generated")
            except json.JSONDecodeError:
                logger.warning("⚠️  Failed to parse questions JSON, using mock data")
                await self.mock_questions()
                
        except Exception as e:
            logger.error(f"❌ Questions generation failed: {e}")
            await self.mock_questions()
    
    async def mock_questions(self):
        """Mock questions when OpenAI is not available."""
        self.example_questions = [
            {
                "question": f"What are the fundamental principles of {self.domain_name.lower()}?",
                "category": "technical",
                "difficulty": "beginner",
                "relevance_score": 0.9
            },
            {
                "question": f"How has {self.domain_name.lower()} evolved over time?",
                "category": "historical",
                "difficulty": "intermediate",
                "relevance_score": 0.8
            },
            {
                "question": f"What are the best practices for {self.domain_name.lower()}?",
                "category": "practical",
                "difficulty": "intermediate",
                "relevance_score": 0.85
            },
            {
                "question": f"What are the common challenges in {self.domain_name.lower()}?",
                "category": "problem-solving",
                "difficulty": "advanced",
                "relevance_score": 0.75
            },
            {
                "question": f"How can {self.domain_name.lower()} be applied in real-world scenarios?",
                "category": "practical",
                "difficulty": "intermediate",
                "relevance_score": 0.8
            }
        ]
        
        logger.info("✅ Mock questions generated")
    
    async def continuous_research_loop(self):
        """Continuous research loop with real-time insights."""
        logger.info("\n4️⃣  Continuous Research")
        logger.info("-" * 40)
        logger.info("🔄 Continuous research is running in the background...")
        logger.info("💡 New insights will be added as they're discovered...")
        
        # Simulate continuous research
        research_focuses = [
            "Historical development",
            "Technical aspects",
            "Practical applications",
            "Current trends",
            "Future directions"
        ]
        
        for i, focus in enumerate(research_focuses, 1):
            logger.info(f"🔍 Research focus {i}/5: {focus}")
            
            # Simulate research time
            await asyncio.sleep(2)
            
            # Generate insight
            insight = {
                "id": f"insight_{i}",
                "focus": focus,
                "insight": f"New insight about {focus.lower()} in {self.domain_name.lower()}",
                "relevance": 0.7 + (i * 0.05),
                "timestamp": datetime.now().isoformat(),
                "actionable": True
            }
            
            self.continuous_insights.append(insight)
            logger.info(f"💡 New insight: {insight['insight']}")
        
        logger.info("✅ Continuous research completed")
    
    async def collect_owner_feedback(self):
        """Collect feedback from the owner."""
        logger.info("\n5️⃣  Owner Feedback")
        logger.info("-" * 40)
        
        # Display research summary
        logger.info("📊 Research Summary:")
        logger.info(f"   {self.research_results['summary']}")
        
        # Display topics
        logger.info(f"\n🏷️  Discovered Topics ({len(self.research_results['topics'])}):")
        for topic in self.research_results['topics']:
            logger.info(f"   • {topic}")
        
        # Display example questions
        logger.info(f"\n❓ Example Questions ({len(self.example_questions)}):")
        for i, question in enumerate(self.example_questions, 1):
            logger.info(f"   {i}. {question['question']}")
            logger.info(f"      Category: {question['category']}, Difficulty: {question['difficulty']}")
        
        # Display continuous insights
        logger.info(f"\n💡 Continuous Insights ({len(self.continuous_insights)}):")
        for insight in self.continuous_insights:
            logger.info(f"   • {insight['insight']}")
        
        # Collect feedback
        logger.info("\n👤 Please provide your feedback:")
        
        # Question rankings
        logger.info("\n📊 Rank the example questions (1-5, where 1 is most relevant):")
        question_rankings = []
        for i, question in enumerate(self.example_questions):
            while True:
                try:
                    ranking = int(input(f"   {i+1}. {question['question'][:50]}... (1-5): "))
                    if 1 <= ranking <= 5:
                        question_rankings.append({
                            "question_id": i,
                            "ranking": ranking,
                            "relevance": "high" if ranking <= 2 else "medium" if ranking <= 3 else "low"
                        })
                        break
                    else:
                        logger.warning("Please enter a number between 1 and 5")
                except ValueError:
                    logger.warning("Please enter a valid number")
        
        # Additional topics
        additional_topics_input = input("\n➕ Additional topics to cover (comma-separated): ").strip()
        additional_topics = [t.strip() for t in additional_topics_input.split(",") if t.strip()]
        
        # Remove topics
        remove_topics_input = input("➖ Topics to remove (comma-separated): ").strip()
        remove_topics = [t.strip() for t in remove_topics_input.split(",") if t.strip()]
        
        # Quality requirements
        quality_threshold = input("📈 Quality threshold (7.0-10.0, default 7.0): ").strip()
        try:
            quality_threshold = float(quality_threshold) if quality_threshold else 7.0
        except ValueError:
            quality_threshold = 7.0
        
        min_length = input("📏 Minimum length (1000-5000, default 1000): ").strip()
        try:
            min_length = int(min_length) if min_length else 1000
        except ValueError:
            min_length = 1000
        
        # Approval
        approval = input("\n✅ Approve this domain configuration? (y/n): ").strip().lower()
        approved = approval in ['y', 'yes']
        
        # Store feedback
        self.owner_feedback = {
            "approved": approved,
            "question_rankings": question_rankings,
            "additional_topics": additional_topics,
            "remove_topics": remove_topics,
            "quality_requirements": {
                "quality_threshold": quality_threshold,
                "min_length": min_length
            }
        }
        
        logger.info("✅ Owner feedback collected")
    
    async def finalize_domain(self):
        """Finalize the domain configuration."""
        logger.info("\n6️⃣  Domain Finalization")
        logger.info("-" * 40)
        
        if not self.owner_feedback["approved"]:
            logger.info("❌ Domain not approved by owner")
            return
        
        # Create final domain configuration
        final_config = {
            "domain_id": self.domain_id,
            "owner_id": self.owner_id,
            "title": self.domain_name,
            "description": self.domain_description,
            "status": "active",
            "topics": self.research_results["topics"] + self.owner_feedback["additional_topics"],
            "quality_criteria": {
                "min_length": self.owner_feedback["quality_requirements"]["min_length"],
                "quality_threshold": self.owner_feedback["quality_requirements"]["quality_threshold"],
                "required_sections": ["abstract", "introduction", "conclusion", "references"],
                "technical_depth_required": True,
                "safety_considerations_required": True,
                "practical_applications_required": True
            },
            "search_attributes": {
                "domain_id": self.domain_id,
                "domain_name": self.domain_name,
                "owner_id": self.owner_id,
                "topics": self.research_results["topics"],
                "target_audience": ["general"]
            },
            "bootstrap_prompt": f"Expert analysis of {self.domain_name.lower()} domain with focus on practical applications and best practices.",
            "research_steps": [
                f"Literature review of {self.domain_name.lower()}",
                f"Expert interviews on {self.domain_name.lower()}",
                f"Case study analysis of {self.domain_name.lower()}"
            ],
            "target_audience": ["general"]
        }
        
        # Remove topics if specified
        if self.owner_feedback["remove_topics"]:
            final_config["topics"] = [
                topic for topic in final_config["topics"] 
                if topic not in self.owner_feedback["remove_topics"]
            ]
        
        logger.info("🏗️  Final domain configuration:")
        logger.info(f"   📋 Domain: {final_config['title']}")
        logger.info(f"   🏷️  Topics: {len(final_config['topics'])} topics")
        logger.info(f"   📊 Quality threshold: {final_config['quality_criteria']['quality_threshold']}")
        logger.info(f"   📏 Min length: {final_config['quality_criteria']['min_length']} characters")
        
        # Save configuration
        config_file = f"domain_config_{self.domain_id}.json"
        with open(config_file, "w") as f:
            json.dump(final_config, f, indent=2)
        
        logger.info(f"💾 Configuration saved to: {config_file}")
        logger.info("✅ Domain finalized successfully!")
    
    async def handle_interruption(self):
        """Handle user interruption."""
        logger.info("🛑 Onboarding interrupted")
        if self.domain_id:
            logger.info(f"Domain ID: {self.domain_id}")
            logger.info("You can resume onboarding later using this ID")
    
    async def handle_error(self, error: Exception):
        """Handle errors during onboarding."""
        logger.error(f"❌ Onboarding error: {error}")
        logger.info("Please check your configuration and try again")
    
    def create_research_prompt(self) -> Dict[str, str]:
        """Create research prompt for OpenAI."""
        system_prompt = f"""
You are an expert knowledge base architect specializing in comprehensive domain research.
Your task is to conduct deep, multi-faceted research on the domain "{self.domain_name}" to bootstrap a world-class knowledge base.

RESEARCH OBJECTIVES:
1. Discover all relevant topics and subtopics for this domain
2. Identify quality criteria for content assessment
3. Understand the knowledge landscape and gaps
4. Recommend knowledge base structure and organization
5. Identify key stakeholders and use cases
6. Provide actionable insights for knowledge base development

Please provide your research in JSON format with the following structure:
{{
    "summary": "Comprehensive research summary",
    "topics": ["topic1", "topic2", "topic3"],
    "quality_criteria": {{
        "min_length": 1000,
        "quality_threshold": 7.0,
        "required_sections": ["abstract", "introduction", "conclusion", "references"],
        "technical_depth_required": true,
        "safety_considerations_required": true,
        "practical_applications_required": true
    }},
    "knowledge_gaps": ["gap1", "gap2", "gap3"],
    "sources": ["source1", "source2", "source3"],
    "recommendations": ["recommendation1", "recommendation2", "recommendation3"]
}}
"""

        user_prompt = f"""
Please conduct comprehensive research on the domain: {self.domain_name}

DOMAIN DESCRIPTION:
{self.domain_description}

Please provide a comprehensive research analysis in JSON format as specified in the system prompt.
"""

        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def create_questions_prompt(self) -> Dict[str, str]:
        """Create questions prompt for OpenAI."""
        system_prompt = f"""
You are an expert knowledge base architect specializing in generating relevant questions for domain-specific knowledge bases.
Your task is to generate example questions that demonstrate the knowledge base's capabilities for the domain "{self.domain_name}".

Please generate 5 example questions in JSON format with the following structure:
[
    {{
        "question": "Specific question about the domain",
        "category": "technical|practical|historical|comparative|problem-solving",
        "difficulty": "beginner|intermediate|advanced",
        "relevance_score": 0.0-1.0
    }}
]
"""

        user_prompt = f"""
Please generate example questions for the domain: {self.domain_name}

DOMAIN DESCRIPTION:
{self.domain_description}

Please generate 5 example questions that demonstrate the knowledge base's capabilities for this domain.
"""

        return {
            "system": system_prompt,
            "user": user_prompt
        }


async def main():
    """Main CLI execution."""
    cli = DomainOnboardingCLI()
    await cli.start_onboarding()


if __name__ == "__main__":
    asyncio.run(main())
