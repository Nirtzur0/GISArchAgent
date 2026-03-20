#!/usr/bin/env python3
"""Vector database builder CLI."""

import importlib
import os
import sys
from dataclasses import dataclass
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click
import logging

from src.config import settings


@dataclass(frozen=True)
class PrerequisiteCheck:
    name: str
    ok: bool
    detail: str
    required: bool = True


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


@click.group()
def cli():
    """Vector database builder CLI."""
    pass


def check_python_module(
    module_name: str,
    *,
    label: str | None = None,
    required: bool = True,
) -> PrerequisiteCheck:
    """Verify an importable Python module."""
    try:
        importlib.import_module(module_name)
    except Exception as exc:
        status = "required" if required else "optional"
        return PrerequisiteCheck(
            name=label or module_name,
            ok=False,
            detail=f"{status} module unavailable ({exc})",
            required=required,
        )

    return PrerequisiteCheck(
        name=label or module_name,
        ok=True,
        detail="module import OK",
        required=required,
    )


def check_provider_configuration(base_url: str | None = None) -> PrerequisiteCheck:
    """Report whether the optional OpenAI-compatible provider is configured."""
    resolved_base_url = settings.openai_base_url.strip()
    if base_url is not None:
        resolved_base_url = base_url.strip()

    if not resolved_base_url:
        return PrerequisiteCheck(
            name="OpenAI-compatible provider",
            ok=False,
            detail=(
                "not configured; vision extraction will be skipped unless "
                "OPENAI_BASE_URL is set or you run with --no-vision"
            ),
            required=False,
        )

    api_key_present = bool(settings.openai_api_key or os.getenv("OPENAI_API_KEY"))
    key_note = "API key present" if api_key_present else "API key optional/absent"
    return PrerequisiteCheck(
        name="OpenAI-compatible provider",
        ok=True,
        detail=f"configured at {resolved_base_url} ({key_note})",
        required=False,
    )


def check_pydoll_runtime() -> PrerequisiteCheck:
    """Launch a bounded browser session to validate the scraper runtime."""
    try:
        import asyncio
        from pydoll.browser.chromium import Chrome

        async def _run():
            browser = Chrome()
            tab = await browser.start(headless=True)
            await tab.go_to("https://www.google.com", timeout=60)
            await browser.stop()

        asyncio.run(_run())
    except Exception as exc:
        return PrerequisiteCheck(
            name="Pydoll browser runtime",
            ok=False,
            detail=str(exc),
            required=True,
        )

    return PrerequisiteCheck(
        name="Pydoll browser runtime",
        ok=True,
        detail="Chrome launched successfully",
        required=True,
    )


def collect_prerequisite_checks() -> list[PrerequisiteCheck]:
    """Collect required and optional runtime checks for the unified pipeline."""
    return [
        check_pydoll_runtime(),
        check_python_module("chromadb", label="ChromaDB"),
        check_python_module("fitz", label="PyMuPDF", required=False),
        check_python_module("pypdf", label="pypdf", required=False),
        check_python_module("PIL", label="Pillow", required=False),
        check_provider_configuration(),
    ]


def summarize_prerequisite_checks(
    checks: list[PrerequisiteCheck],
) -> tuple[bool, list[str]]:
    """Render human-readable prerequisite results and overall status."""
    lines: list[str] = []
    required_failures = [check for check in checks if check.required and not check.ok]

    for check in checks:
        icon = "✅" if check.ok else ("❌" if check.required else "⚠️")
        requirement = "required" if check.required else "optional"
        lines.append(f"  {icon} {check.name} ({requirement}): {check.detail}")

    return (not required_failures, lines)


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed status')
def status(verbose):
    """Show vector database status and health."""
    setup_logging(verbose)
    
    # Use simple check to avoid circular imports
    import subprocess
    script_path = Path(__file__).parent / 'quick_status.py'
    subprocess.call([sys.executable, str(script_path)])


@cli.command()
@click.option('--max-plans', type=int, default=None, help='Maximum plans to process')
@click.option('--rebuild', is_flag=True, help='Clear and rebuild database')
@click.option('--headless', is_flag=True, help='Run browser headless (may reduce MAVAT reliability)')
@click.option('--no-documents', is_flag=True, help='Skip document fetching')
@click.option('--no-vision', is_flag=True, help='Skip vision processing')
@click.option('--verbose', '-v', is_flag=True, help='Verbose logging')
def build(max_plans, rebuild, headless, no_documents, no_vision, verbose):
    """Build or update the vector database."""
    setup_logging(verbose)
    
    # Lazy imports
    from src.vectorstore.unified_pipeline import UnifiedDataPipeline, PipelineConfig
    
    print("="*70)
    print("🏗️  Vector Database Builder")
    print("="*70)
    print()
    
    # Configuration
    config = PipelineConfig(
        max_plans=max_plans,
        rebuild_vectordb=rebuild,
        fetch_documents=not no_documents,
        process_documents=not no_vision,
        headless=headless,
    )
    
    print("📋 Configuration:")
    print(f"  Max plans: {max_plans or 'all'}")
    print(f"  Rebuild: {rebuild}")
    print(f"  Fetch documents: {not no_documents}")
    print(f"  Vision processing: {not no_vision}")
    print(f"  Headless: {headless}")
    print()
    
    # Confirm if rebuild
    if rebuild:
        print("⚠️  WARNING: This will clear the existing vector database!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("Cancelled.")
            return
        print()
    
    # Run pipeline
    try:
        print("🚀 Starting pipeline...\n")
        pipeline = UnifiedDataPipeline(config=config)
        stats = pipeline.run()
        
        print("\n" + "="*70)
        print("✅ Vector database build complete!")
        print("="*70)
        print()
        print(f"📊 Results:")
        print(f"  Plans processed: {stats.plans_processed}")
        print(f"  Documents found: {stats.documents_found}")
        print(f"  Regulations indexed: {stats.regulations_indexed}")
        print()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
def check():
    """Check prerequisites and setup."""
    print("="*70)
    print("🔍 Checking Prerequisites")
    print("="*70)
    print()

    all_ok, lines = summarize_prerequisite_checks(collect_prerequisite_checks())
    for line in lines:
        print(line)

    print()
    if all_ok:
        print("✅ Required checks passed.")
    else:
        print("❌ Required checks failed. Fix the items above before running a full build.")

    return 0 if all_ok else 1


if __name__ == '__main__':
    cli()
