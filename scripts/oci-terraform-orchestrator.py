#!/usr/bin/env python3
"""
OCI Terraform Deployment Orchestrator - Simplified
===================================================
Features:
- Dynamic service detection from git changes
- Unified terraform init + plan/apply execution
- Enhanced PR comments with structured output
- Error aggregation and reporting
- Audit logging

Version: 1.0
Created: 2025-12-17
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

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

VERSION = "1.0"
DEBUG = os.environ.get('ORCHESTRATOR_DEBUG', 'false').lower() == 'true'


def debug_print(msg: str):
    """Print debug messages if DEBUG mode is enabled"""
    if DEBUG:
        print(f"🐛 DEBUG: {msg}")


# =============================================================================
# ARGUMENT PARSING
# =============================================================================

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='OCI Terraform Deployment Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Plan changes (PR context)
  python oci-terraform-orchestrator.py --action plan --working-dir ./toronto
  
  # Apply changes (merge context)
  python oci-terraform-orchestrator.py --action apply --working-dir ./toronto
  
  # Debug mode
  python oci-terraform-orchestrator.py --action plan --working-dir ./toronto --debug
        """
    )
    
    parser.add_argument(
        '--action',
        choices=['plan', 'apply'],
        required=True,
        help='Terraform action to perform (plan or apply)'
    )
    
    parser.add_argument(
        '--working-dir',
        required=True,
        help='Working directory containing service subdirectories (e.g., ./toronto)'
    )
    
    parser.add_argument(
        '--base-ref',
        default=os.environ.get('GITHUB_BASE_REF', 'main'),
        help='Base git reference for change detection (default: main)'
    )
    
    parser.add_argument(
        '--region',
        default=os.environ.get('OCI_REGION', 'us-ashburn-1'),
        help='OCI region (default: from OCI_REGION env or us-ashburn-1)'
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
        help='Simulate execution without running terraform (for testing)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )
    
    parser.add_argument(
        '--parallel',
        action='store_true',
        help='Execute services in parallel (experimental)'
    )
    
    return parser.parse_args()


# =============================================================================
# OCI AUTHENTICATION
# =============================================================================

def validate_oci_cli_config():
    """Validate OCI CLI configuration exists"""
    config_path = Path.home() / '.oci' / 'config'
    
    if not config_path.exists():
        print(f"❌ Error: OCI CLI config not found at {config_path}")
        print("   Create config file with OCI credentials")
        sys.exit(1)
    
    debug_print(f"✓ OCI config found at {config_path}")
    
    # Check for required OCI environment variables
    required_vars = ['OCI_CLI_TENANCY', 'OCI_CLI_USER', 'OCI_CLI_REGION']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing OCI environment variables: {', '.join(missing_vars)}")
        print("   These may be required depending on your OCI provider configuration")
    
    return True


# =============================================================================
# CHANGE DETECTION
# =============================================================================

def detect_changed_services(working_dir: str, base_ref: str) -> List[str]:
    """
    Dynamically detect which service directories have changes.
    Uses git diff to find modified files and extracts service names.
    
    Args:
        working_dir: Base directory containing services (e.g., "toronto")
        base_ref: Base git reference for comparison (e.g., "main")
    
    Returns:
        Sorted list of changed service names
    """
    try:
        repo = git.Repo(search_parent_directories=True)
        
        # Handle different git scenarios
        if os.environ.get('GITHUB_EVENT_NAME') == 'pull_request':
            # PR: compare base...HEAD
            base = f"origin/{base_ref}"
            head = "HEAD"
        else:
            # Push: compare previous commit with current
            base = "HEAD^"
            head = "HEAD"
        
        debug_print(f"Git diff: {base}...{head}")
        
        # Get list of changed files
        try:
            diff_output = repo.git.diff(f'{base}...{head}', '--name-only')
        except git.exc.GitCommandError:
            # Fallback for initial commit or shallow clone
            debug_print("Using fallback: listing all files")
            diff_output = repo.git.ls_files()
        
        changed_files = [f for f in diff_output.split('\n') if f.strip()]
        
        debug_print(f"Changed files: {changed_files}")
        
        # Extract service names from changed file paths
        # Pattern: {working_dir_name}/{service_name}/...
        working_dir_name = Path(working_dir).name
        services = set()
        
        for file_path in changed_files:
            parts = file_path.split('/')
            
            # Check if file is under working directory
            if len(parts) >= 2 and parts[0] == working_dir_name:
                service_name = parts[1]
                
                # Verify service directory exists
                service_path = Path(working_dir) / service_name
                if service_path.is_dir():
                    # Check if directory contains Terraform files
                    tf_files = list(service_path.glob('*.tf'))
                    if tf_files:
                        services.add(service_name)
                        debug_print(f"Found service: {service_name}")
        
        return sorted(list(services))
        
    except Exception as e:
        print(f"⚠️  Warning: Could not detect changes via git: {e}")
        print("   Falling back to all services in working directory")
        
        # Fallback: return all directories with .tf files
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
            # Check if directory contains .tf files
            tf_files = list(item.glob('*.tf'))
            if tf_files:
                services.append(item.name)
    
    return sorted(services)


# =============================================================================
# TERRAFORM EXECUTION
# =============================================================================

def execute_terraform_for_service(
    service_name: str,
    service_dir: str,
    action: str,
    region: str
) -> Dict:
    """
    Execute terraform init + plan/apply for a single service.
    
    Args:
        service_name: Name of the service (e.g., "compute")
        service_dir: Full path to service directory
        action: 'plan' or 'apply'
        region: OCI region
    
    Returns:
        Dictionary with execution results
    """
    result = {
        'service': service_name,
        'action': action,
        'success': False,
        'output': '',
        'error': '',
        'duration': 0,
        'resources_changed': 0,
        'resources_created': 0,
        'resources_destroyed': 0
    }
    
    start_time = datetime.now()
    
    try:
        print(f"\n{'='*80}")
        print(f"🔄 Processing Service: {service_name}")
        print(f"{'='*80}")
        
        # Step 1: Terraform Init
        print(f"  🔧 Step 1/2: terraform init")
        init_cmd = ['terraform', 'init', '-no-color']
        
        init_result = subprocess.run(
            init_cmd,
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=600  # 10 min timeout for init
        )
        
        if init_result.returncode != 0:
            result['error'] = f"Terraform init failed:\n{init_result.stderr}"
            print(f"  ❌ Init failed")
            return result
        
        print(f"  ✅ Init successful")
        
        # Step 2: Terraform Plan or Apply
        if action == 'plan':
            print(f"  📋 Step 2/2: terraform plan")
            tf_cmd = ['terraform', 'plan', '-no-color', '-detailed-exitcode']
        else:
            print(f"  🚀 Step 2/2: terraform apply")
            tf_cmd = ['terraform', 'apply', '-auto-approve', '-no-color']
        
        tf_result = subprocess.run(
            tf_cmd,
            cwd=service_dir,
            capture_output=True,
            text=True,
            timeout=1800  # 30 min timeout
        )
        
        result['output'] = tf_result.stdout
        
        # Parse exit codes
        # Plan: 0 = no changes, 1 = error, 2 = changes present
        if action == 'plan':
            if tf_result.returncode == 0:
                result['success'] = True
                result['resources_changed'] = 0
                print(f"  ✅ Plan completed - No changes")
            elif tf_result.returncode == 2:
                result['success'] = True
                result['resources_changed'] = parse_plan_summary(tf_result.stdout)
                print(f"  ✅ Plan completed - {result['resources_changed']} changes")
            else:
                result['error'] = tf_result.stderr
                print(f"  ❌ Plan failed")
        else:
            # Apply: 0 = success, anything else = error
            result['success'] = (tf_result.returncode == 0)
            if result['success']:
                stats = parse_apply_summary(tf_result.stdout)
                result.update(stats)
                print(f"  ✅ Apply completed - {stats['resources_changed']} changes")
            else:
                result['error'] = tf_result.stderr
                print(f"  ❌ Apply failed")
        
    except subprocess.TimeoutExpired:
        result['error'] = f"Terraform {action} timed out after 30 minutes"
        print(f"  ⏱️  Timeout")
    except Exception as e:
        result['error'] = f"Unexpected error: {str(e)}"
        print(f"  ❌ Error: {str(e)}")
    
    result['duration'] = (datetime.now() - start_time).total_seconds()
    
    return result


def parse_plan_summary(output: str) -> int:
    """Extract number of changes from terraform plan output"""
    import re
    
    # Look for: "Plan: 1 to add, 0 to change, 0 to destroy"
    match = re.search(r'Plan:\s+(\d+)\s+to\s+add,\s+(\d+)\s+to\s+change,\s+(\d+)\s+to\s+destroy', output)
    if match:
        return int(match.group(1)) + int(match.group(2)) + int(match.group(3))
    
    return 0


def parse_apply_summary(output: str) -> Dict:
    """Extract resource change statistics from terraform apply output"""
    import re
    
    stats = {
        'resources_created': 0,
        'resources_changed': 0,
        'resources_destroyed': 0
    }
    
    # Look for: "Apply complete! Resources: 1 added, 0 changed, 0 destroyed"
    match = re.search(
        r'Apply complete!\s+Resources:\s+(\d+)\s+added,\s+(\d+)\s+changed,\s+(\d+)\s+destroyed',
        output
    )
    
    if match:
        stats['resources_created'] = int(match.group(1))
        stats['resources_changed'] = int(match.group(2))
        stats['resources_destroyed'] = int(match.group(3))
    
    return stats


# =============================================================================
# RESULT FORMATTING
# =============================================================================

def generate_results_summary(results: List[Dict], action: str) -> str:
    """
    Generate formatted markdown summary for PR comment.
    
    Args:
        results: List of service execution results
        action: 'plan' or 'apply'
    
    Returns:
        Markdown formatted string
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    summary = f"# 🎯 OCI Terraform {action.capitalize()} Results\n\n"
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
    
    # Summary table
    summary += "## 📊 Summary\n\n"
    summary += "| Service | Status | Duration | Changes |\n"
    summary += "|---------|--------|----------|----------|\n"
    
    for result in results:
        status_icon = "✅" if result['success'] else "❌"
        duration = f"{result['duration']:.1f}s"
        
        if action == 'plan':
            changes = str(result['resources_changed']) if result['success'] else "N/A"
        else:
            changes = f"+{result['resources_created']} ~{result['resources_changed']} -{result['resources_destroyed']}"
        
        summary += f"| {result['service']} | {status_icon} | {duration} | {changes} |\n"
    
    summary += "\n"
    
    # Detailed per-service results
    summary += "## 📋 Detailed Results\n\n"
    
    for result in results:
        icon = "✅" if result['success'] else "❌"
        summary += f"### {icon} {result['service']}\n\n"
        
        if result['success']:
            # Successful execution - show collapsible output
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
            # Failed execution - show error prominently
            summary += f"**❌ Error:**\n```\n{result['error']}\n```\n\n"
            
            if result['output']:
                summary += f"<details><summary>📄 Show Output</summary>\n\n"
                summary += f"```\n{result['output']}\n```\n"
                summary += "</details>\n\n"
    
    # Footer
    summary += "---\n"
    summary += f"🤖 *Generated by OCI Terraform Orchestrator v{VERSION}*\n"
    
    return summary


def write_pr_comment(content: str):
    """Write PR comment to file for GitHub Action to post"""
    output_file = 'terraform-results.md'
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"\n✅ Results written to {output_file}")
    except Exception as e:
        print(f"⚠️  Warning: Could not write PR comment file: {e}")


def write_audit_log(results: List[Dict], action: str):
    """Write audit log in JSON format"""
    audit_log = {
        'timestamp': datetime.now().isoformat(),
        'orchestrator_version': VERSION,
        'action': action,
        'total_services': len(results),
        'successful_services': sum(1 for r in results if r['success']),
        'failed_services': sum(1 for r in results if not r['success']),
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
# MAIN EXECUTION
# =============================================================================

def main():
    """Main orchestrator execution"""
    args = parse_args()
    
    # Enable debug mode if requested
    global DEBUG
    if args.debug:
        DEBUG = True
    
    # Dry-run mode notification
    dry_run_msg = " (DRY-RUN MODE)" if args.dry_run else ""
    
    print(f"""
{'='*80}
🎯 OCI Terraform Deployment Orchestrator v{VERSION}{dry_run_msg}
{'='*80}
Action:       {args.action}
Working Dir:  {args.working_dir}
Base Ref:     {args.base_ref}
Region:       {args.region}
Debug:        {args.debug}
Dry-run:      {args.dry_run}
{'='*80}
""")
    
    # Step 1: Validate working directory
    working_dir = Path(args.working_dir)
    if not working_dir.exists():
        print(f"❌ Error: Working directory does not exist: {working_dir}")
        print(f"   Absolute path: {working_dir.absolute()}")
        return 1
    
    # Step 1.5: Validate OCI authentication (skip in dry-run)
    if not args.dry_run:
        print("🔐 Validating OCI CLI configuration...")
        validate_oci_cli_config()
        print("✅ OCI authentication validated\n")
    else:
        print("🧪 Skipping OCI authentication validation (dry-run mode)\n")
    
    # Step 2: Detect changed services
    print("🔍 Detecting changed services...")
    changed_services = detect_changed_services(args.working_dir, args.base_ref)
    
    if not changed_services:
        print("✅ No service changes detected")
        write_pr_comment("## ℹ️  No Infrastructure Changes\n\nNo Terraform-managed services were modified in this change.")
        return 0
    
    print(f"📦 Detected changes in {len(changed_services)} service(s): {', '.join(changed_services)}\n")
    
    # Step 3: Execute Terraform for each service
    results = []
    
    for service_name in changed_services:
        service_dir = Path(args.working_dir) / service_name
        
        if args.dry_run:
            # Simulate execution in dry-run mode
            print(f"\n🧪 [DRY-RUN] Would execute terraform {args.action} for: {service_name}")
            result = {
                'service': service_name,
                'success': True,
                'duration': 0.0,
                'output': f'[DRY-RUN] Simulated {args.action} for {service_name}',
                'error': None,
                'resources_created': 0,
                'resources_changed': 0,
                'resources_destroyed': 0
            }
        else:
            result = execute_terraform_for_service(
                service_name=service_name,
                service_dir=str(service_dir),
                action=args.action,
                region=args.region
            )
        
        results.append(result)
    
    # Step 4: Generate and write results
    print(f"\n{'='*80}")
    print("📝 Generating results summary...")
    summary = generate_results_summary(results, args.action)
    write_pr_comment(summary)
    
    # Step 5: Write audit log
    write_audit_log(results, args.action)
    
    # Step 6: Print final summary
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    print(f"\n{'='*80}")
    print(f"🎯 FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Services processed: {total_count}")
    print(f"Successful:         {success_count}")
    print(f"Failed:             {total_count - success_count}")
    print(f"{'='*80}\n")
    
    # Exit with appropriate code
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
