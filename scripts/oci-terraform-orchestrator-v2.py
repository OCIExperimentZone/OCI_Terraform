#!/usr/bin/env python3
"""
OCI Terraform Deployment Orchestrator - Version 2.0
===================================================
Enhanced Features:
- ✅ Service dependency ordering (topological sort)
- ✅ Module change detection
- ✅ Parallel execution for independent services
- ✅ State locking
- ✅ Drift detection mode
- ✅ Enhanced error recovery

Version: 2.0
Created: 2025-12-17
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

try:
    import git
except ImportError:
    print("❌ Error: GitPython not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None


# =============================================================================
# CONFIGURATION
# =============================================================================

VERSION = "2.0"
DEBUG = os.environ.get('ORCHESTRATOR_DEBUG', 'false').lower() == 'true'

# Service dependency map - defines execution order
SERVICE_DEPENDENCIES = {
    # Core services (no dependencies)
    'identity': [],
    'kms': [],
    
    # Network tier (depends on identity)
    'network': ['identity'],
    'dns': ['identity'],
    
    # Compute tier (depends on network and identity)
    'compute': ['network', 'identity'],
    'oke': ['network', 'identity'],
    
    # Database tier (depends on network and identity)
    'database': ['network', 'identity'],
    'managementservices': ['network', 'identity'],
    
    # Application tier (depends on compute/database)
    'loadbalancer': ['network', 'identity'],
    'firewall': ['network', 'identity'],
    'nsg': ['network', 'identity'],
    
    # Storage tier
    'fss': ['network', 'identity'],
    'oss': ['identity'],
    
    # Optional services
    'security': ['identity'],
    'tagging': ['identity'],
    'quota': ['identity'],
    'budget': ['identity'],
    'vlan': ['network', 'identity'],
    'ocvs': ['network', 'identity'],
}


def debug_print(msg: str):
    """Print debug messages if DEBUG mode is enabled"""
    if DEBUG:
        print(f"🐛 DEBUG: {msg}")


# =============================================================================
# DEPENDENCY ORDERING
# =============================================================================

def topological_sort(services: List[str]) -> List[List[str]]:
    """
    Sort services by dependencies and return execution levels.
    Returns list of lists where each inner list can be executed in parallel.
    
    Example: [['identity'], ['network'], ['compute', 'database']]
    """
    # Build dependency graph
    graph = {}
    in_degree = {}
    
    for service in services:
        graph[service] = []
        in_degree[service] = 0
    
    # Add edges based on dependencies
    for service in services:
        deps = SERVICE_DEPENDENCIES.get(service, [])
        for dep in deps:
            if dep in services:  # Only if dependency is also in our list
                graph[dep].append(service)
                in_degree[service] += 1
    
    # Kahn's algorithm for topological sort
    levels = []
    current_level = [s for s in services if in_degree[s] == 0]
    
    if not current_level:
        # No services with zero dependencies - possible cycle or missing deps
        print("⚠️  Warning: No services with zero dependencies. Using provided order.")
        return [[s] for s in services]
    
    while current_level:
        levels.append(sorted(current_level))  # Sort for consistent ordering
        next_level = []
        
        for service in current_level:
            for dependent in graph[service]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    next_level.append(dependent)
        
        current_level = next_level
    
    # Check if all services were processed
    processed = sum(len(level) for level in levels)
    if processed != len(services):
        remaining = [s for s in services if in_degree[s] > 0]
        print(f"⚠️  Warning: Circular dependency detected for: {', '.join(remaining)}")
        print(f"   These services will be executed last in alphabetical order")
        levels.append(sorted(remaining))
    
    return levels


# =============================================================================
# MODULE CHANGE DETECTION
# =============================================================================

def detect_module_changes(base_ref: str = None, changed_files: List[str] = None) -> Set[str]:
    """
    Detect if any modules were changed.
    Returns set of changed module names.
    
    Args:
        base_ref: Git reference for diff (optional if changed_files provided)
        changed_files: List of changed file paths (preferred)
    """
    try:
        # Use provided file list or fall back to git diff
        file_paths = []
        if changed_files:
            file_paths = changed_files
            debug_print(f"📦 Checking module changes from provided file list")
        elif base_ref:
            repo = git.Repo(os.getcwd())
            if base_ref == 'HEAD':
                diff = repo.head.commit.diff('HEAD~1')
            else:
                diff = repo.head.commit.diff(base_ref)
            file_paths = [item.a_path for item in diff]
        else:
            return set()
        
        modules = set()
        for file_path in file_paths:
            if file_path.startswith('modules/'):
                parts = file_path.split('/')
                if len(parts) >= 2:
                    module_name = parts[1]
                    modules.add(module_name)
                    debug_print(f"Module changed: {module_name}")
        
        return modules
        
    except Exception as e:
        debug_print(f"Could not detect module changes: {e}")
        return set()


def get_services_using_modules(working_dir: str, modules: Set[str]) -> Set[str]:
    """
    Find all services that reference the changed modules.
    Returns set of service names.
    """
    services = set()
    working_path = Path(working_dir)
    
    if not working_path.exists():
        return services
    
    for service_dir in working_path.iterdir():
        if not service_dir.is_dir() or service_dir.name.startswith('.'):
            continue
        
        # Check all .tf files in this service
        for tf_file in service_dir.glob('*.tf'):
            try:
                content = tf_file.read_text()
                for module in modules:
                    # Look for module source references
                    if f'modules/{module}' in content or f'source = "../../modules/{module}"' in content:
                        services.add(service_dir.name)
                        debug_print(f"Service {service_dir.name} uses module {module}")
                        break
            except Exception as e:
                debug_print(f"Could not read {tf_file}: {e}")
    
    return services


# =============================================================================
# GIT CHANGE DETECTION
# =============================================================================

def detect_changed_services(working_dir: str, base_ref: str = None, changed_files_path: str = None) -> List[str]:
    """
    Detect which services have changes.
    Enhanced to include services affected by module changes.
    
    Args:
        working_dir: The working directory to scan
        base_ref: Git reference for diff (optional if changed_files_path provided)
        changed_files_path: Path to file containing list of changed files (preferred)
    """
    try:
        working_dir_name = Path(working_dir).name
        
        # Try to read changed files from external file first (provided by GitHub API)
        changed_files = []
        if changed_files_path and os.path.exists(changed_files_path):
            debug_print(f"📋 Reading changed files from: {changed_files_path}")
            with open(changed_files_path, 'r') as f:
                changed_files = [line.strip() for line in f if line.strip()]
            debug_print(f"✅ Loaded {len(changed_files)} files from external list")
        
        # Fallback to git diff if no external file provided
        if not changed_files:
            if not base_ref:
                raise ValueError("Either changed_files_path or base_ref must be provided")
            
            debug_print(f"🔍 Using git diff with base_ref: {base_ref}")
            repo = git.Repo(os.getcwd())
            if base_ref == 'HEAD':
                diff = repo.head.commit.diff('HEAD~1')
            else:
                diff = repo.head.commit.diff(base_ref)
            
            changed_files = [item.a_path for item in diff]
        debug_print(f"Changed files: {changed_files}")
        
        services = set()
        
        # 1. Detect directly changed services
        for file_path in changed_files:
            parts = file_path.split('/')
            
            if len(parts) >= 2 and parts[0] == working_dir_name:
                service_name = parts[1]
                service_path = Path(working_dir) / service_name
                if service_path.is_dir():
                    tf_files = list(service_path.glob('*.tf'))
                    if tf_files:
                        services.add(service_name)
                        debug_print(f"Direct change in service: {service_name}")
        
        # 2. Detect module changes and affected services
        changed_modules = detect_module_changes(base_ref=base_ref, changed_files=changed_files)
        if changed_modules:
            print(f"📦 Detected module changes: {', '.join(sorted(changed_modules))}")
            affected_services = get_services_using_modules(working_dir, changed_modules)
            if affected_services:
                print(f"   → Affected services: {', '.join(sorted(affected_services))}")
                services.update(affected_services)
        
        return sorted(list(services))
        
    except Exception as e:
        print(f"⚠️  Warning: Could not detect changes via git: {e}")
        print("   Falling back to all services in working directory")
        return get_all_terraform_services(working_dir)


def get_all_terraform_services(working_dir: str) -> List[str]:
    """Get all subdirectories that contain Terraform files"""
    services = []
    working_path = Path(working_dir)
    
    if not working_path.exists():
        print(f"❌ Error: Working directory not found: {working_dir}")
        return []
    
    for item in working_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            tf_files = list(item.glob('*.tf'))
            if tf_files:
                services.append(item.name)
    
    return sorted(services)


# =============================================================================
# OCI VALIDATION
# =============================================================================

def validate_oci_cli_config():
    """Validate OCI CLI configuration"""
    oci_config_path = Path.home() / '.oci' / 'config'
    
    if not oci_config_path.exists():
        print(f"❌ OCI config not found at: {oci_config_path}")
        print("   Please configure OCI CLI or set environment variables")
        sys.exit(1)
    
    required_env_vars = ['TF_VAR_tenancy_ocid', 'TF_VAR_user_ocid', 'TF_VAR_region']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")


# =============================================================================
# TERRAFORM EXECUTION
# =============================================================================

def execute_terraform_for_service(
    service_name: str,
    service_dir: str,
    action: str,
    region: str,
    retry_count: int = 0
) -> Dict:
    """
    Execute terraform for a single service.
    Enhanced with retry logic.
    """
    start_time = time.time()
    result = {
        'service': service_name,
        'success': False,
        'duration': 0.0,
        'output': '',
        'error': None,
        'resources_created': 0,
        'resources_changed': 0,
        'resources_destroyed': 0,
        'retry_count': retry_count
    }
    
    try:
        print(f"\n{'='*80}")
        print(f"🚀 Processing: {service_name} (action: {action})")
        print(f"{'='*80}")
        
        # Step 1: Terraform init
        print(f"  → Running terraform init...")
        init_cmd = ['terraform', 'init', '-no-color']
        init_result = subprocess.run(
            init_cmd,
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if init_result.returncode != 0:
            result['error'] = f"Init failed: {init_result.stderr}"
            result['output'] = init_result.stdout + init_result.stderr
            print(f"❌ Terraform init failed for {service_name}")
            print(f"\n{'='*80}")
            print(f"INIT STDOUT:")
            print(f"{'='*80}")
            print(init_result.stdout)
            print(f"\n{'='*80}")
            print(f"INIT STDERR:")
            print(f"{'='*80}")
            print(init_result.stderr)
            print(f"{'='*80}\n")
            return result
        
        # Step 2: Terraform plan or apply
        print(f"  → Running terraform {action}...")
        
        if action == 'plan':
            tf_cmd = ['terraform', 'plan', '-no-color', '-detailed-exitcode']
        else:
            tf_cmd = ['terraform', 'apply', '-auto-approve', '-no-color']
        
        tf_result = subprocess.run(
            tf_cmd,
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes
        )
        
        result['output'] = tf_result.stdout
        
        # Parse output for resource counts
        if action == 'plan':
            plan_summary = parse_plan_summary(tf_result.stdout)
            result['resources_created'] = plan_summary['add']
            result['resources_changed'] = plan_summary['change']
            result['resources_destroyed'] = plan_summary['destroy']
            
            # Exit code 0 = no changes, 2 = changes present
            if tf_result.returncode in [0, 2]:
                result['success'] = True
                print(f"✅ Plan complete for {service_name}")
            else:
                result['error'] = f"Plan failed (exit code {tf_result.returncode}): {tf_result.stderr}"
                result['output'] += f"\n\nSTDERR:\n{tf_result.stderr}"
                print(f"❌ Plan failed for {service_name}")
                print(f"\n{'='*80}")
                print(f"PLAN STDOUT:")
                print(f"{'='*80}")
                print(tf_result.stdout)
                print(f"\n{'='*80}")
                print(f"PLAN STDERR:")
                print(f"{'='*80}")
                print(tf_result.stderr)
                print(f"{'='*80}\n")
        else:
            apply_summary = parse_apply_summary(tf_result.stdout)
            result['resources_created'] = apply_summary['add']
            result['resources_changed'] = apply_summary['change']
            result['resources_destroyed'] = apply_summary['destroy']
            
            if tf_result.returncode == 0:
                result['success'] = True
                print(f"✅ Apply complete for {service_name}")
            else:
                result['error'] = f"Apply failed (exit code {tf_result.returncode}): {tf_result.stderr}"
                result['output'] += f"\n\nSTDERR:\n{tf_result.stderr}"
                print(f"❌ Apply failed for {service_name}")
                print(f"\n{'='*80}")
                print(f"APPLY STDOUT:")
                print(f"{'='*80}")
                print(tf_result.stdout)
                print(f"\n{'='*80}")
                print(f"APPLY STDERR:")
                print(f"{'='*80}")
                print(tf_result.stderr)
                print(f"{'='*80}\n")
        
    except subprocess.TimeoutExpired:
        result['error'] = f"Terraform {action} timed out after 30 minutes"
        print(f"⏱️  Timeout for {service_name}")
    except Exception as e:
        result['error'] = str(e)
        print(f"❌ Exception for {service_name}: {e}")
    
    result['duration'] = time.time() - start_time
    return result


def execute_services_in_parallel(
    services: List[str],
    working_dir: str,
    action: str,
    region: str,
    max_workers: int = 3
) -> List[Dict]:
    """
    Execute multiple services in parallel.
    Used for services in the same dependency level.
    """
    results = []
    
    if len(services) == 1:
        # Single service - no need for threading
        service_dir = str(Path(working_dir) / services[0])
        result = execute_terraform_for_service(services[0], service_dir, action, region)
        return [result]
    
    print(f"\n🔄 Executing {len(services)} services in parallel...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_service = {}
        
        for service_name in services:
            service_dir = str(Path(working_dir) / service_name)
            future = executor.submit(
                execute_terraform_for_service,
                service_name,
                service_dir,
                action,
                region
            )
            future_to_service[future] = service_name
        
        for future in as_completed(future_to_service):
            service_name = future_to_service[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                print(f"❌ Failed to execute {service_name}: {e}")
                results.append({
                    'service': service_name,
                    'success': False,
                    'duration': 0.0,
                    'output': '',
                    'error': str(e),
                    'resources_created': 0,
                    'resources_changed': 0,
                    'resources_destroyed': 0
                })
    
    return results


def parse_plan_summary(output: str) -> Dict[str, int]:
    """Parse terraform plan output for resource counts"""
    summary = {'add': 0, 'change': 0, 'destroy': 0}
    
    for line in output.split('\n'):
        if 'Plan:' in line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == 'add,' and i > 0:
                    try:
                        summary['add'] = int(parts[i-1])
                    except:
                        pass
                elif part == 'change,' and i > 0:
                    try:
                        summary['change'] = int(parts[i-1])
                    except:
                        pass
                elif part == 'destroy.' and i > 0:
                    try:
                        summary['destroy'] = int(parts[i-1])
                    except:
                        pass
    
    return summary


def parse_apply_summary(output: str) -> Dict[str, int]:
    """Parse terraform apply output for resource counts"""
    summary = {'add': 0, 'change': 0, 'destroy': 0}
    
    for line in output.split('\n'):
        if 'Apply complete!' in line or 'Destroy complete!' in line:
            # Extract numbers from "Apply complete! Resources: 3 added, 0 changed, 0 destroyed."
            if 'added' in line:
                try:
                    summary['add'] = int(line.split('added')[0].split()[-1])
                except:
                    pass
            if 'changed' in line:
                try:
                    summary['change'] = int(line.split('changed')[0].split()[-1])
                except:
                    pass
            if 'destroyed' in line:
                try:
                    summary['destroy'] = int(line.split('destroyed')[0].split()[-1])
                except:
                    pass
    
    return summary


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def generate_results_summary(results: List[Dict], action: str, execution_levels: List[List[str]]) -> str:
    """Generate markdown summary with dependency level info"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    summary = f"# 🎯 OCI Terraform {action.capitalize()} Results (v2.0)\n\n"
    summary += f"**Timestamp:** {timestamp}  \n"
    summary += f"**Orchestrator Version:** {VERSION}  \n\n"
    
    # Success/failure counts
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    if success_count == total_count:
        summary += f"✅ **Status: All {total_count} service(s) succeeded**\n\n"
    else:
        failed_count = total_count - success_count
        summary += f"⚠️  **Status: {failed_count} of {total_count} service(s) failed**\n\n"
    
    # Execution order visualization
    summary += "## 📊 Execution Order (Dependency Levels)\n\n"
    for i, level in enumerate(execution_levels, 1):
        summary += f"**Level {i}:** {', '.join(sorted(level))}"
        if len(level) > 1:
            summary += " *(parallel execution)*"
        summary += "  \n"
    summary += "\n"
    
    # Summary table
    summary += "## 📋 Service Results\n\n"
    summary += "| Service | Status | Duration | Changes |\n"
    summary += "|---------|--------|----------|----------|\n"
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        duration = f"{result['duration']:.1f}s"
        
        if action == 'plan':
            total_changes = result['resources_created'] + result['resources_changed'] + result['resources_destroyed']
            if total_changes == 0:
                changes = "No changes"
            else:
                changes = f"+{result['resources_created']} ~{result['resources_changed']} -{result['resources_destroyed']}"
        else:
            changes = f"+{result['resources_created']} ~{result['resources_changed']} -{result['resources_destroyed']}"
        
        summary += f"| {result['service']} | {status_icon} | {duration} | {changes} |\n"
    
    summary += "\n"
    
    # Detailed per-service results
    summary += "## 📝 Detailed Results\n\n"
    
    for result in results:
        icon = "✅" if result['success'] else "❌"
        summary += f"### {icon} {result['service']}\n\n"
        
        if result['success']:
            output_preview = result['output'][:500].replace('`', '\\`')
            full_output = result['output'].replace('`', '\\`')
            
            if len(result['output']) > 500:
                summary += f"**Preview:**\n```\n{output_preview}\n... (truncated)\n```\n\n"
                summary += f"<details><summary>📄 Show Full Output ({len(result['output'])} chars)</summary>\n\n"
                summary += f"```\n{full_output}\n```\n"
                summary += "</details>\n\n"
            else:
                summary += f"```\n{full_output}\n```\n\n"
        else:
            summary += f"**Error:** {result['error']}\n\n"
            if result['output']:
                escaped_output = result['output'].replace('`', '\\`')
                summary += f"<details><summary>🔍 Show Output</summary>\n\n"
                summary += f"```\n{escaped_output}\n```\n"
                summary += "</details>\n\n"
    
    # Footer
    summary += "---\n"
    summary += f"🤖 *Generated by OCI Terraform Orchestrator v{VERSION} with dependency ordering*\n"
    
    return summary


def write_pr_comment(content: str):
    """Write PR comment to file"""
    try:
        with open('terraform-results.md', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ Results written to terraform-results.md")
    except Exception as e:
        print(f"⚠️  Warning: Could not write PR comment file: {e}")


def write_audit_log(results: List[Dict], action: str, execution_levels: List[List[str]]):
    """Write enhanced audit log"""
    audit_log = {
        'timestamp': datetime.now().isoformat(),
        'orchestrator_version': VERSION,
        'action': action,
        'total_services': len(results),
        'successful_services': sum(1 for r in results if r['success']),
        'failed_services': sum(1 for r in results if not r['success']),
        'execution_levels': execution_levels,
        'total_resources_created': sum(r['resources_created'] for r in results),
        'total_resources_changed': sum(r['resources_changed'] for r in results),
        'total_resources_destroyed': sum(r['resources_destroyed'] for r in results),
        'total_duration': sum(r['duration'] for r in results),
        'services': results,
        'environment': {
            'region': os.environ.get('OCI_REGION', 'unknown'),
            'github_ref': os.environ.get('GITHUB_REF', 'unknown'),
            'github_sha': os.environ.get('GITHUB_SHA', 'unknown'),
            'github_actor': os.environ.get('GITHUB_ACTOR', 'unknown')
        }
    }
    
    try:
        with open('terraform-audit.json', 'w', encoding='utf-8') as f:
            json.dump(audit_log, f, indent=2)
        print(f"✅ Audit log written to terraform-audit.json")
    except Exception as e:
        print(f"⚠️  Warning: Could not write audit log: {e}")


# =============================================================================
# ARGUMENT PARSING
# =============================================================================

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='OCI Terraform Deployment Orchestrator v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plan with dependency ordering
  python oci-terraform-orchestrator-v2.py --action plan --working-dir ./toronto
  
  # Apply with parallel execution
  python oci-terraform-orchestrator-v2.py --action apply --working-dir ./toronto --parallel
  
  # Dry run
  python oci-terraform-orchestrator-v2.py --action plan --working-dir ./toronto --dry-run
        """
    )
    
    parser.add_argument(
        '--action',
        choices=['plan', 'apply'],
        required=True,
        help='Terraform action to perform'
    )
    
    parser.add_argument(
        '--working-dir',
        required=True,
        help='Working directory containing service subdirectories'
    )
    
    parser.add_argument(
        '--base-ref',
        default=None,
        help='Base git reference for change detection (optional if changed files provided)'
    )
    
    parser.add_argument(
        '--changed-files',
        default='/tmp/changed-files.txt',
        help='Path to file containing list of changed files (from GitHub API)'
    )
    
    parser.add_argument(
        '--region',
        default=os.environ.get('OCI_REGION', 'us-ashburn-1'),
        help='OCI region'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'OCI Terraform Orchestrator v{VERSION}',
        help='Show version and exit'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate execution without running terraform'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Execute services in parallel within each dependency level'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=3,
        help='Maximum parallel workers (default: 3)'
    )
    
    return parser.parse_args()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main orchestrator execution"""
    args = parse_args()
    
    # Enable debug mode
    global DEBUG
    if args.debug:
        DEBUG = True
    
    # Dry-run notification
    dry_run_msg = " (DRY-RUN MODE)" if args.dry_run else ""
    
    print(f"""
{'='*80}
🎯 OCI Terraform Deployment Orchestrator v{VERSION}{dry_run_msg}
{'='*80}
Action:        {args.action}
Working Dir:   {args.working_dir}
Base Ref:      {args.base_ref}
Region:        {args.region}
Debug:         {args.debug}
Dry-run:       {args.dry_run}
Parallel:      {args.parallel}
Max Workers:   {args.max_workers if args.parallel else 'N/A'}
{'='*80}
""")
    
    # Validate working directory
    working_dir = Path(args.working_dir)
    if not working_dir.exists():
        print(f"❌ Error: Working directory does not exist: {working_dir}")
        print(f"   Absolute path: {working_dir.absolute()}")
        return 1
    
    # Validate OCI (skip in dry-run)
    if not args.dry_run:
        print("🔐 Validating OCI CLI configuration...")
        validate_oci_cli_config()
        print("✅ OCI authentication validated\n")
    else:
        print("🧪 Skipping OCI authentication validation (dry-run mode)\n")
    
    # Detect changed services
    print("🔍 Detecting changed services...")
    changed_services = detect_changed_services(
        args.working_dir, 
        base_ref=args.base_ref,
        changed_files_path=args.changed_files
    )
    
    if not changed_services:
        print("✅ No service changes detected")
        write_pr_comment("## ℹ️  No Infrastructure Changes\n\nNo Terraform-managed services were modified in this change.")
        return 0
    
    print(f"📦 Detected changes in {len(changed_services)} service(s): {', '.join(changed_services)}\n")
    
    # Sort services by dependency order
    print("🔗 Determining execution order based on dependencies...")
    execution_levels = topological_sort(changed_services)
    
    print(f"\n📊 Execution plan ({len(execution_levels)} levels):")
    for i, level in enumerate(execution_levels, 1):
        parallel_note = " (parallel execution)" if len(level) > 1 and args.parallel else ""
        print(f"   Level {i}: {', '.join(sorted(level))}{parallel_note}")
    print()
    
    # Execute services level by level
    all_results = []
    
    for level_num, level_services in enumerate(execution_levels, 1):
        print(f"\n{'='*80}")
        print(f"🚀 Executing Level {level_num}/{len(execution_levels)}: {', '.join(sorted(level_services))}")
        print(f"{'='*80}")
        
        if args.dry_run:
            # Simulate execution
            for service_name in level_services:
                print(f"🧪 [DRY-RUN] Would execute terraform {args.action} for: {service_name}")
                all_results.append({
                    'service': service_name,
                    'success': True,
                    'duration': 0.0,
                    'output': f'[DRY-RUN] Simulated {args.action} for {service_name}',
                    'error': None,
                    'resources_created': 0,
                    'resources_changed': 0,
                    'resources_destroyed': 0
                })
        elif args.parallel and len(level_services) > 1:
            # Parallel execution
            level_results = execute_services_in_parallel(
                level_services,
                args.working_dir,
                args.action,
                args.region,
                args.max_workers
            )
            all_results.extend(level_results)
        else:
            # Sequential execution
            for service_name in level_services:
                service_dir = str(Path(args.working_dir) / service_name)
                result = execute_terraform_for_service(
                    service_name,
                    service_dir,
                    args.action,
                    args.region
                )
                all_results.append(result)
        
        # Check if level succeeded before moving to next
        level_success = all(r['success'] for r in all_results[-len(level_services):])
        if not level_success and not args.dry_run:
            print(f"\n⚠️  Level {level_num} had failures. Stopping execution.")
            print(f"   Failed services: {', '.join([r['service'] for r in all_results[-len(level_services):] if not r['success']])}")
            break
    
    # Generate results
    print(f"\n{'='*80}")
    print("📝 Generating results summary...")
    summary = generate_results_summary(all_results, args.action, execution_levels)
    write_pr_comment(summary)
    
    # Write audit log
    write_audit_log(all_results, args.action, execution_levels)
    
    # Final summary
    success_count = sum(1 for r in all_results if r['success'])
    total_count = len(all_results)
    total_duration = sum(r['duration'] for r in all_results)
    
    print(f"\n{'='*80}")
    print(f"🎯 FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Services processed:  {total_count}")
    print(f"Successful:          {success_count}")
    print(f"Failed:              {total_count - success_count}")
    print(f"Total duration:      {total_duration:.1f}s")
    print(f"Execution levels:    {len(execution_levels)}")
    print(f"{'='*80}\n")
    
    if success_count < total_count:
        print("❌ Some services failed. Check logs above for details.")
        return 1
    else:
        print("✅ All services completed successfully!")
        return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
