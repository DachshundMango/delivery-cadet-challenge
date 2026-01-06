"""
Data Pipeline Automation Script

Runs all data pipeline steps in sequence:
1. profiler - Analyze CSV files
2. relationship_discovery - Configure PK/FK (interactive)
3. load_data - Load data to PostgreSQL (may fail on first run)
4. integrity_checker - Check data integrity
5. transform_data - Fix data issues (interactive)
6. generate_schema - Generate schema with PII detection
"""

import subprocess
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.console import Console
from src.core.logger import setup_logger

logger = setup_logger('cadet.setup')


class PipelineStep:
    """Represents a single pipeline step"""

    def __init__(self, name: str, module: str, required: bool = True, description: str = ""):
        self.name = name
        self.module = module
        self.required = required
        self.description = description
        self.success = False
        self.exit_code = None


def run_step(step: PipelineStep) -> bool:
    """
    Run a single pipeline step

    Args:
        step: PipelineStep object

    Returns:
        True if step succeeded, False otherwise
    """
    Console.separator()
    Console.info(f"STEP: {step.name.upper()}", indent=0)
    if step.description:
        Console.info(f"      {step.description}", indent=0)
    Console.separator()

    # Run the script as a module
    cmd = [sys.executable, "-m", step.module]

    try:
        result = subprocess.run(
            cmd,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            check=False  # Don't raise exception on non-zero exit
        )

        step.exit_code = result.returncode
        step.success = (result.returncode == 0)

        # Handle result
        if step.success:
            Console.success(f"{step.name} completed successfully", indent=0)
            return True
        else:
            if step.required:
                Console.error(f"{step.name} failed (exit code: {result.returncode})")
                return False
            else:
                Console.warning(f"{step.name} failed (exit code: {result.returncode})",
                               "Continuing as this step is optional")
                return True  # Continue even though step failed

    except Exception as e:
        logger.error(f"Failed to run {step.name}: {e}")
        Console.error(f"Failed to run {step.name}", str(e))
        step.success = False
        return not step.required  # Continue only if not required


def print_summary(steps: list[PipelineStep]):
    """Print pipeline execution summary"""
    Console.separator()
    Console.info("PIPELINE EXECUTION SUMMARY", indent=0)
    Console.separator()

    for step in steps:
        if step.exit_code is None:
            status = f"{Console.YELLOW}[SKIPPED]{Console.RESET}"
        elif step.success:
            status = f"{Console.GREEN}[SUCCESS]{Console.RESET}"
        else:
            status = f"{Console.RED}[FAILED]{Console.RESET}"

        print(f"{status} {step.name}")

    Console.separator()

    # Overall result
    all_required_passed = all(step.success for step in steps if step.required)

    if all_required_passed:
        Console.footer("Pipeline completed successfully")
        Console.info("\nYour database is ready! You can now run the SQL Agent:", indent=0)
        Console.info("  python src/main.py", indent=0)
    else:
        Console.footer("Pipeline completed with errors", success=False)
        Console.info("\nSome required steps failed. Please review the errors above.", indent=0)


def main():
    """Run the complete data pipeline"""
    Console.header("Data Pipeline Setup")

    Console.info("This will run all pipeline steps in sequence:", indent=0)
    Console.info("  1. Profiler - Analyze CSV files", indent=0)
    Console.info("  2. Relationship Discovery - Configure PK/FK (interactive)", indent=0)
    Console.info("  3. Load Data - Load to PostgreSQL (may fail initially)", indent=0)
    Console.info("  4. Integrity Checker - Validate data integrity", indent=0)
    Console.info("  5. Transform Data - Fix issues (interactive)", indent=0)
    Console.info("  6. Generate Schema - Create schema with PII detection", indent=0)
    Console.info("", indent=0)

    # Ask for confirmation
    response = input("Continue? [Y/n]: ").strip().lower()
    if response and response not in ['y', 'yes']:
        Console.warning("Pipeline setup cancelled by user")
        return

    # Define pipeline steps
    steps = [
        PipelineStep(
            name="Profiler",
            module="src.data_pipeline.profiler",
            required=True,
            description="Analyzing CSV files and creating data profile"
        ),
        PipelineStep(
            name="Relationship Discovery",
            module="src.data_pipeline.relationship_discovery",
            required=True,
            description="Configuring primary and foreign keys (interactive)"
        ),
        PipelineStep(
            name="Load Data",
            module="src.data_pipeline.load_data",
            required=False,  # Expected to fail on first run
            description="Loading CSV data to PostgreSQL (expected to fail initially)"
        ),
        PipelineStep(
            name="Integrity Checker",
            module="src.data_pipeline.integrity_checker",
            required=True,
            description="Checking data integrity and FK violations"
        ),
        PipelineStep(
            name="Transform Data",
            module="src.data_pipeline.transform_data",
            required=True,
            description="Fixing data issues with SQL transformations (interactive)"
        ),
        PipelineStep(
            name="Generate Schema",
            module="src.data_pipeline.generate_schema",
            required=True,
            description="Generating schema files with PII detection"
        ),
    ]

    # Run each step
    for step in steps:
        success = run_step(step)

        if not success:
            logger.error(f"Pipeline halted at step: {step.name}")
            break

    # Print summary
    print("\n")
    print_summary(steps)


if __name__ == '__main__':
    main()
