"""Load testing for Document Contribution Workflow.
Tests system performance under various load conditions.
"""

import asyncio
import statistics
import time
import uuid
from dataclasses import dataclass
from typing import Any

from temporalio.client import Client

from workflow.document_contribution_workflow import (
    DocumentContributionInput,
    DocumentContributionWorkflow,
)


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""

    temporal_address: str = "localhost:7233"
    namespace: str = "default"

    # Test parameters
    num_workflows: int = 100
    concurrent_workflows: int = 10
    workflow_delay: float = 0.1  # Delay between workflow starts

    # Document score distribution
    high_score_percentage: float = 0.3  # 30% auto-approve
    low_score_percentage: float = 0.2  # 20% auto-reject
    review_percentage: float = 0.5  # 50% need review

    # Monitoring
    print_interval: int = 10  # Print status every N workflows


@dataclass
class LoadTestResult:
    """Results from load test."""

    total_workflows: int
    successful_workflows: int
    failed_workflows: int

    total_duration: float
    average_duration: float
    min_duration: float
    max_duration: float
    p95_duration: float
    p99_duration: float

    throughput: float  # workflows per second

    status_distribution: dict[str, int]
    error_types: dict[str, int]


class LoadTester:
    """Load tester for Document Contribution Workflow."""

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.client = None
        self.results = []
        self.errors = []
        self.status_counts = {}

    async def setup(self):
        """Setup Temporal client."""
        self.client = await Client.connect(
            self.config.temporal_address,
            namespace=self.config.namespace,
        )

    async def generate_workflow_input(self, index: int) -> DocumentContributionInput:
        """Generate test workflow input with varied scores."""
        # Determine score based on distribution
        if index % 100 < self.config.high_score_percentage * 100:
            # High score - will auto-approve
            import os

            os.environ["DEFAULT_RELEVANCE_SCORE"] = "9.0"
            use_ai = False
        elif (
            index % 100
            < (self.config.high_score_percentage + self.config.low_score_percentage)
            * 100
        ):
            # Low score - will auto-reject
            import os

            os.environ["DEFAULT_RELEVANCE_SCORE"] = "3.0"
            use_ai = False
        else:
            # Medium score - needs review
            import os

            os.environ["DEFAULT_RELEVANCE_SCORE"] = "6.0"
            # Alternate between AI and human review
            use_ai = index % 2 == 0

        return DocumentContributionInput(
            document_id=str(uuid.uuid4()),
            document_path=f"/load-test/document-{index}.pdf",
            contributor_id=f"contributor-{index % 10}",  # 10 different contributors
            domain_id=f"domain-{index % 5}",  # 5 different domains
            domain_criteria={
                "topic": "load-testing",
                "quality": "variable",
                "index": index,
            },
            use_ai_controller=use_ai,
            controller_pool=(
                [f"controller-{i}" for i in range(5)] if not use_ai else None
            ),
        )

    async def run_workflow(self, index: int) -> dict[str, Any]:
        """Run a single workflow and measure performance."""
        start_time = time.time()
        workflow_id = f"load-test-{uuid.uuid4()}"

        try:
            # Generate input
            workflow_input = await self.generate_workflow_input(index)

            # Start workflow
            handle = await self.client.start_workflow(
                DocumentContributionWorkflow.run,
                workflow_input,
                id=workflow_id,
                task_queue="general-queue",
            )

            # For review workflows, auto-approve after short delay
            if (
                workflow_input.relevance_threshold
                > workflow_input.relevance_score
                > workflow_input.auto_reject_threshold
            ):
                if not workflow_input.use_ai_controller:
                    # Wait a bit then send review signal
                    await asyncio.sleep(1)
                    await handle.signal(
                        DocumentContributionWorkflow.submit_review,
                        {"approved": True, "feedback": "Load test auto-approve"},
                    )

            # Wait for result
            result = await handle.result()

            duration = time.time() - start_time

            return {
                "success": result.success,
                "duration": duration,
                "status": result.status.value if result.status else "unknown",
                "workflow_id": workflow_id,
                "error": result.error,
            }

        except Exception as e:
            duration = time.time() - start_time
            return {
                "success": False,
                "duration": duration,
                "status": "error",
                "workflow_id": workflow_id,
                "error": str(e),
            }

    async def run_concurrent_batch(
        self, start_index: int, batch_size: int
    ) -> list[dict[str, Any]]:
        """Run a batch of workflows concurrently."""
        tasks = []
        for i in range(batch_size):
            task = self.run_workflow(start_index + i)
            tasks.append(task)

            # Small delay between starts to avoid overwhelming system
            await asyncio.sleep(self.config.workflow_delay)

        results = await asyncio.gather(*tasks)
        return results

    async def run_load_test(self) -> LoadTestResult:
        """Run the complete load test."""
        print(f"🚀 Starting load test with {self.config.num_workflows} workflows")
        print(f"   Concurrency: {self.config.concurrent_workflows}")
        print(
            f"   Score distribution: {self.config.high_score_percentage * 100:.0f}% high, "
            f"{self.config.low_score_percentage * 100:.0f}% low, "
            f"{self.config.review_percentage * 100:.0f}% review"
        )

        await self.setup()

        start_time = time.time()
        all_results = []

        # Run workflows in batches
        num_batches = (
            self.config.num_workflows + self.config.concurrent_workflows - 1
        ) // self.config.concurrent_workflows

        for batch_idx in range(num_batches):
            start_index = batch_idx * self.config.concurrent_workflows
            batch_size = min(
                self.config.concurrent_workflows,
                self.config.num_workflows - start_index,
            )

            batch_results = await self.run_concurrent_batch(start_index, batch_size)
            all_results.extend(batch_results)

            # Print progress
            if (batch_idx + 1) % (
                self.config.print_interval // self.config.concurrent_workflows
            ) == 0:
                completed = len(all_results)
                elapsed = time.time() - start_time
                rate = completed / elapsed
                print(
                    f"   Progress: {completed}/{self.config.num_workflows} "
                    f"({completed * 100 / self.config.num_workflows:.1f}%) "
                    f"- {rate:.1f} workflows/sec"
                )

        total_duration = time.time() - start_time

        # Analyze results
        return self.analyze_results(all_results, total_duration)

    def analyze_results(
        self, results: list[dict[str, Any]], total_duration: float
    ) -> LoadTestResult:
        """Analyze test results and generate report."""
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        durations = [r["duration"] for r in successful]
        durations.sort()

        # Calculate statistics
        if durations:
            avg_duration = statistics.mean(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            p95_duration = (
                durations[int(len(durations) * 0.95)]
                if len(durations) > 20
                else max_duration
            )
            p99_duration = (
                durations[int(len(durations) * 0.99)]
                if len(durations) > 100
                else max_duration
            )
        else:
            avg_duration = min_duration = max_duration = p95_duration = p99_duration = 0

        # Status distribution
        status_dist = {}
        for r in results:
            status = r.get("status", "unknown")
            status_dist[status] = status_dist.get(status, 0) + 1

        # Error types
        error_types = {}
        for r in failed:
            error = r.get("error", "unknown")[:50]  # Truncate long errors
            error_types[error] = error_types.get(error, 0) + 1

        return LoadTestResult(
            total_workflows=len(results),
            successful_workflows=len(successful),
            failed_workflows=len(failed),
            total_duration=total_duration,
            average_duration=avg_duration,
            min_duration=min_duration,
            max_duration=max_duration,
            p95_duration=p95_duration,
            p99_duration=p99_duration,
            throughput=len(results) / total_duration,
            status_distribution=status_dist,
            error_types=error_types,
        )

    def print_report(self, result: LoadTestResult):
        """Print load test report."""
        print("\n" + "=" * 60)
        print("📊 LOAD TEST REPORT")
        print("=" * 60)

        print("\n📈 Summary:")
        print(f"   Total workflows:     {result.total_workflows}")
        print(
            f"   Successful:          {result.successful_workflows} ({result.successful_workflows * 100 / result.total_workflows:.1f}%)"
        )
        print(
            f"   Failed:              {result.failed_workflows} ({result.failed_workflows * 100 / result.total_workflows:.1f}%)"
        )
        print(f"   Total duration:      {result.total_duration:.2f} seconds")
        print(f"   Throughput:          {result.throughput:.2f} workflows/second")

        print("\n⏱️ Performance:")
        print(f"   Average duration:    {result.average_duration:.2f} seconds")
        print(f"   Min duration:        {result.min_duration:.2f} seconds")
        print(f"   Max duration:        {result.max_duration:.2f} seconds")
        print(f"   P95 duration:        {result.p95_duration:.2f} seconds")
        print(f"   P99 duration:        {result.p99_duration:.2f} seconds")

        print("\n📊 Status Distribution:")
        for status, count in result.status_distribution.items():
            print(
                f"   {status:20s} {count:5d} ({count * 100 / result.total_workflows:.1f}%)"
            )

        if result.error_types:
            print("\n❌ Error Types:")
            for error, count in result.error_types.items():
                print(f"   {error[:40]:40s} {count:5d}")

        print("\n" + "=" * 60)


async def main():
    """Main entry point for load testing."""
    import sys

    # Parse command line arguments
    num_workflows = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    concurrency = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    config = LoadTestConfig(
        num_workflows=num_workflows,
        concurrent_workflows=concurrency,
    )

    tester = LoadTester(config)
    result = await tester.run_load_test()
    tester.print_report(result)

    # Exit with error code if too many failures
    failure_rate = result.failed_workflows / result.total_workflows
    if failure_rate > 0.1:  # More than 10% failures
        print(f"\n❌ Load test failed: {failure_rate * 100:.1f}% failure rate")
        sys.exit(1)
    else:
        print("\n✅ Load test passed!")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
