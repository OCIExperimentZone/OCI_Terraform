# OCI Terraform Controller - Migration Plan
## Centralized Orchestration for Oracle Cloud Infrastructure

**Date:** December 17, 2025  
**Status:** Planning Phase  
**Purpose:** Migrate OCI CD3 workflow from basic matrix approach to centralized controller pattern

---

## 📊 Current State Analysis

### **Current OCI Workflow Issues**
The existing [dev.yml](.github/workflows/dev.yml) workflow has several limitations:

1. **❌ Mixed Matrix Flow**
   - Uses basic matrix strategy with limited control
   - Deploys to apply job but plan and apply are separate
   - No dependency management between resources
   - Sequential deployment is enforced but not intelligent

2. **❌ No Orchestration Logic**
   - Simple path-based change detection only
   - No dynamic deployment ordering
   - No intelligent error handling

3. **❌ Hardcoded Service Detection**
   - Manual path filters for each service
   - Cannot scale to new services without workflow changes
   - Fixed directory structure required

4. **❌ Limited Error Handling & Reporting**
   - Basic error output only
   - No resource dependency checks
   - No detailed PR comments with results
   - No audit logging

5. **❌ Duplicate Terraform Execution**
   - Separate plan and apply jobs
   - Redundant `terraform init` in both jobs
   - No state continuity between jobs

---

## 🎯 Target State - Centralized Controller Approach

### **Why Centralized Controller?**
The AWS centralized controller ([centralized-controller.yml](../../../../OPA-test/centerlized-pipline-/.github/workflows/centralized-controller.yml)) provides:

✅ **Intelligent Orchestration**
- Python-based deployment orchestrator
- Dynamic service detection
- Resource dependency management
- Parallel/sequential execution control

✅ **Unified Execution Flow**
- Single job handling plan and apply
- No redundant terraform init
- State continuity between plan/apply
- Efficient resource usage

✅ **Enhanced Reporting**
- Detailed PR comments with results
- Structured output formatting
- Error aggregation and reporting
- Audit logging

✅ **Scalability**
- Auto-detect new services without workflow changes
- Dynamic matrix generation from filesystem
- Service-agnostic orchestration logic

---

## 🔄 Architecture Comparison

### Current OCI Approach
```
GitHub Event (Push)
  ↓
detect_changes (job)
  → Uses dorny/paths-filter
  → Creates matrix JSON
  ↓
deploy (job) - Matrix Strategy
  → terraform init
  → terraform plan
  ↓
apply (job) - Matrix Strategy (separate)
  → terraform init (again)
  → terraform apply
```

**Problems:**
- No Python orchestration
- Separate plan/apply jobs (redundant init)
- No validation layer
- No intelligent state management

---

### Target Centralized Controller Approach
```
GitHub Event (Push/PR)
  ↓
OCI Controller (single job)
  ↓
Python Orchestrator Script
  ├─ 1. Change Detection (dynamic)
  ├─ 2. Dynamic Change Detection
  │    └─ Scan filesystem for changed services (auto-discover)
  ├─ 2. Terraform Execution (unified)
  │    ├─ terraform init (once per service)
  │    ├─ terraform plan (capture output)
  │    └─ terraform apply (if approved/merged)
  ├─ 3. Result Collection & Reporting
  │    ├─ Aggregate plan/apply outputs
  │    ├─ Format for PR comments
  │    ├─ Generate audit logs
  │    └─ Track resource changes
  └─ 4. Error Handling & Recovery
       ├─ Capture detailed errors
       ├─ Continue on error (parallel mode)
       └─ Report all failures together
```

**Benefits:**
- Single orchestrated execution (no duplicate init)
- Dynamic service detection (scalable)
- Comprehensive error reporting
- Efficient CI/CD runtime
---

## 📋 Migration Strategy

### Phase 1: Script Adaptation (Week 1)
**Objective:** Adapt AWS Python scripts for OCI
Core Orchestrator Script (Week 1)
**Objective:** Create simplified Python orchestrator for OCI

#### 1.1 Create OCI Orchestrator (Simplified)
**Source:** `centerlized-pipline-/scripts/terraform-deployment-orchestrator-enhanced.py`

**Simplifications for OCI:**
- ❌ **Removed:** Backend key generation (OCI already configured)
- ❌ **Removed:** Pre-deployment validation (not needed)
- ❌ **Removed:** OPA policy integration (not required)
- ✅ **Keep:** Dynamic service detection
- ✅ **Keep:** Terraform execution orchestration
- ✅ **Keep:** Result formatting and PR comments
- ✅ **Keep:** Error handling and reporting

**Adaptations Required:**
```python
# AWS → OCI Changes (Authentication Only)

# Authentication
AWS: AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_SESSION_TOKEN
OCI: OCI_CLI_USER, OCI_CLI_TENANCY, OCI_CLI_REGION, 
     OCI_CLI_KEY_FILE, OCI_CLI_FINGERPRINT

# Note: Backend configuration already exists in OCI terraform files
# No need for dynamic backend key generation
```

**New File:** `scripts/oci-terraform-orchestrator.py`

**Core Functions (Simplified):**
1. `detect_changed_services()` - Scan toronto/ for changed directories
2. `validate_oci_authentication()` - Check OCI CLI config
3. `run_terraform_for_service()` - Execute init/plan/apply
4. `aggregate_results()` - Collect outputs from all services
5. `create_pr_comment()` - Format and post results to GitHub

### Phase 2: Workflow Creation (Week 2)
**Objective:** Build new centralized OCI controller workflow

#### 2.1 Create New Workflow File
**Location:** `.github/workflows/oci-centralized-controller.yml`

**Structure:**
```yaml
name: 🎯 OCI Centralized Controller

on:
  push:
    branches: [Dev, Staging, Production]
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:

jobs:
  oci-controller:
    name: 🚀 OCI Deployment Orchestrator
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
      
      - name: Configure OCI CLI
        # Setup OCI authentication
        
      - name: Install Dependencies
        # Python, Terraform, OPA, conftest
        
      - name: Run OCI Orchestrator
        run: |
          python scripts/oci-terraform-orchestrator.py \
            --action ${{ github.event_name == 'pull_request' && 'validate' || 'apply' }} \
            --working-dir ${{ github.workspace }}/toronto \
            --compartment-id ${{ secrets.OCI_COMPARTMENT_ID }} \
            --region ${{ secrets.OCI_REGION }}
            
      - name: Post PR Comment
        if: github.event_name == 'pull_request'
        # Use GitHub API to post results
```

#### 2.2 Backend Configuration
**Create:** `toronto/backend-config/oci-backend.tf`

```hcl1-2)
**Objective:** Build simplified centralized OCI controller workflow

#### 2.1 Create New Workflow File
**Location:** `.github/workflows/oci-centralized-controller.yml`

**Structure:**
```yaml
name: 🎯 OCI Centralized Controller

on:
  push:
    branches: [Dev, Staging, Production]
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:

jobs:
  oci-controller:
    name: 🚀 OCI Deployment Orchestrator
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@v4
      
      - name: Configure OCI CLI
        run: |
          mkdir -p ~/.oci
          echo "${{ secrets.OCI_CLI_CONFIG }}" > ~/.oci/config
          echo "${{ secrets.OCI_PRIVATE_KEY }}" > ~/.oci/oci_api_key.pem
          chmod 600 ~/.oci/oci_api_key.pem
        
      - name: Install Dependencies
        run: |
          pip install -r scripts/requirements.txt
        
      - name: Run OCI Orchestrator
        run: |
          python scripts/oci-terraform-orchestrator.py \
            --action ${{ github.event_name == 'pull_request' && 'plan' || 'apply' }} \
            --working-dir ${{ github.workspace }}/toronto \
            --region ${{ secrets.OCI_REGION }}
            
      - name: Post PR Comment
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const comment = fs.readFileSync('terraform-results.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

**Note:** Backend configuration already exists in OCI terraform files - no changes neededre-Deployment Checks:**
1. ✅ Compartment exists and accessible
2. ✅ Region is valid and enabled
3. ✅ Resource limits not exceeded
4. ✅ Required tags present
5. ✅ Network security rules compliant
6. ✅ Encryption enabled where required

#### 4.2 OPA Policy Enforcement
**Policy Categories:**
1. **Compute Policies**
   - Instance shapes approved
   - Boot volumes encrypted
   - SSH keys properly managed
   - Public IP restrictions

2. **Network Policies**
   - SecurityTesting & Rollout (Week 2-3)
**Objective:** Validate and deploy simplified

#### `scripts/requirements.txt`
```txt
PyYAML>=6.0
requests>=2.31.0
oci>=2.118.0
boto3>=1.28.0  # For S3-compatible backend
```

#### `scripts/oci-config.yaml`
```yaml
# OCI Controller Configuration
orchestrator_version: "1.0"
debug: true

# OCI Authentication
oci:
  config_file: "~/.oci/config"
  profile: "DEFAULT"
  
# State Backend
state_backend:
  type: "oci-object-storage"  # or "s3-compatible"
  bucket: "terraform-state-bucket"
  namespace: "your-namespace"
  region: "us-ashburn-1"
  
# Backend Key Pattern
backend_key_pattern: "{service}/{compartment}/{region}/{project}/{resource}/terraform.tfstate"

# Validation
validation:
  pre_deployment: true
  opa_enabled: true
  opa_policies_dir: "../opa-policies/oci"
  
# Execution
execution:
  max_parallel: 3
  timeout_seconds: 3600
  
# Audit
audit:
  enabled: true
  log_bucket: "audit-logs-bucket"
```

---

## 📝 Script Pseudo-Code

### **oci-terraform-orchestrator.py**
```python
#!/usr/bin/env python3
"""
OCI Terraform Deployment Orchestrator
Adapted from AWS Centralized Controller
"""

def main():
    # 1. Parse arguments
    args = parse_args()
    
    # 2. Load configuration
    config = load_config("scripts/oci-config.yaml")
    
    # 3. Authenticate with OCI
    oci_config = setup_oci_authentication()
    
    # 4. Detect changed services
    changed_services = detect_changed_services(
        working_dir=args.working_dir,
        base_ref=get_base_ref()
    )
    
    if not changed_services:
        print("No changes detected")
        return
    
    #3.1 Testing Strategy
**Test Phases:**
1. **Unit Tests** - Test Python functions individually
2. **Integration Tests** - Test with OCI sandbox compartment
3. **Dry-Run Tests** - Test plan without apply
4. **Pilot Deployment** - Single service (e.g., identity)
5. **Full Migration** - All services

**Test Cases:**
```bash
# Test 1: Single service change (compute only)
# Test 2: Multi-service change (network + compute)
# Test 3: No changes detected (verify skip logic)
# Test 4: Terraform error handling
# Test 5: Parallel execution (if enabled)
```

#### 3.2 Migration Checklist
- [ ] Python orchestrator script created
- [ ] New workflow file created and tested
- [ ] OCI secrets configured in GitHub
  - OCI_CLI_CONFIG
  - OCI_PRIVATE_KEY
  - OCI_REGION
  - OCI_TENANCY
- [ ] Test in sandbox compartment
- [ ] Documentation updated
- [ ] Old workflow deprecafor each deployment
    results = []
    for deployment in deployment_plan:
        # Generate backend key
        backend_key = generate_backend_key(
            service=deployment.service,
            compartment=deployment.compartment_name,
            region=deployment.region,
            project=deployment.project_name,
            resource=deployment.resource_name
        )
        
        # Execute Terraform
        result = execute_terraform( (simplified)
    requirements.txt                   # Python dependencies
  toronto/
    identity/
    network/
    compute/
    storage/
    # ... other services auto-discoveredit with appropriate code
    if any(r.failed for r in results):
        sys.exit(1)

def detect_changed_services(working_dir, base_ref):
    """Detect which OCI services have changed"""
    # Use git diff to find changed files
    # Dynamically detect service directories
    # Return list of changed service deployments
    
def generate_backend_key(service, compartment, region, project, resource):
    """Generate OCI state backend key"""
    # Pattern: {service}/{compartment}/{region}/{project}/{resource}/terraform.tfstate
    # Example: compute/arj-prod/us-ashburn-1/web-app/web-instance/terraform.tfstate
    
GitPython>=3.1.0
git add .
git commit -m "Add new compute instance"
git push origin feature/new-instance

# 3. Create PR - Orchestrator runs automatically
# - Validates OCI config
# - Runs OPA policies
# - Generates Terraform plan
# - Posts detailed PR comment

# 4. Merge PR - Orchestrator applies changes
# - Runs apply with approved plan
# - Updates state in Object Storage
# - Posts apply results
```

### **For Administrators:**
```bash
# Test orchestrator locally
cd scripts
python oci-terraform-orchestrator.py \
  --action validate \
  --working-dir ../toronto \
  --debug

# Dry-run mode
python oci-terraform-orchestrator.py \
  --action plan \
  --working-dir ../toronto \
  --dry-run
```

---

## 📚 Additional Resources

### **Reference Documentation:**
1. AWS Controller: `centerlized-pipline-/.github/workflows/centralized-controller.yml`
2. AWS Orchestrator: `centerlized-pipline-/scripts/terraform-deployment-orchestrator-enhanced.py`
3. OPA Policies: `OPA-Poclies/terraform/`

### **OCI-Specific Resources:**
- OCI Terraform Provider: https://registry.terraform.io/providers/oracle/oci/latest/docs
- OCI CLI Reference: https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/
- OCI Object Storage API: https://docs.oracle.com/en-us/iaas/api/#/en/objectstorage/
 (Simplified)
```python
#!/usr/bin/env python3
"""
OCI Terraform Deployment Orchestrator - Simplified
Focus: Dynamic service detection + unified execution + enhanced reporting
"""

def main():
    # 1. Parse arguments
    args = parse_args()  # --action [plan|apply], --working-dir, --region
    
    # 2. Validate OCI authentication
    validate_oci_cli_config()
    
    # 3. Detect changed services dynamically
    changed_services = detect_changed_services(
        working_dir=args.working_dir,
        base_ref=os.getenv('GITHUB_BASE_REF', 'main')
    )
    
    if not changed_services:
        print("✅ No changes detected")
        write_pr_comment("No infrastructure changes detected.")
        return
    
    print(f"📦 Detected changes in: {', '.join(changed_services)}")
    
    # 4. Execute Terraform for each changed service
    results = []
    for service in changed_services:
        service_dir = os.path.join(args.working_dir, service)
        
        print(f"\n🔄 Processing: {service}")
        result = execute_terraform_for_service(
            service_name=service,
            service_dir=service_dir,
            action=args.action,  # 'plan' or 'apply'
            region=args.region
        )
        
        results.append(result)
    
    # 5. Generate formatted results
    summary = generate_results_summary(results, args.action)
    
    # 6. Write PR comment file
    write_pr_comment(summary)
    
    # 7. Write audit log (optional)
    write_audit_log(results)
    
    # 8. Exit with appropriate code
    if any(r['success'] == False for r in results):
        sys.exit(1)


def detect_changed_services(working_dir, base_ref):
    """
    Dynamically detect which service directories have changes.
    Uses git diff to find modified files, extracts service names.
    """
    import git
    
    repo = git.Repo(search_parent_directories=True)
    
    # Get diff between base and HEAD
    diff = repo.git.diff(f'{base_ref}...HEAD', '--name-only')
    
    changed_files = diff.split('\n')
    
    # Extract unique service names from paths
    # Pattern: toronto/{service}/...
    services = set()
    for file in changed_files:
        if file.startswith('toronto/'):
            parts = file.split('/')
            if len(parts) >= 2:
                services.add(parts[1])  # Extract service name
    
    return sorted(list(services))


def execute_terraform_for_service(service_name, service_dir, action, region):
    """
    Execute terraform init + plan/apply for a single service.
    Backend configuration already exists in terraform files.
    """
    result = {
        'service': service_name,
        'action': action,
        'success': False,
        'output': '',
        'error': ''
    }
    
    try:
        # 1. Terraform init
        print(f"  🔧 terraform init")
        init_cmd = ['terraform', 'init']
        init_result = subprocess.run(
            init_cmd, 
            cwd=service_dir,
            capture_output=True,
            text=True
        )
        
        if init_result.returncode != 0:
            result['error'] = init_result.stderr
            return result
         (hardcoded paths)
- ❌ Limited error visibility
- ❌ Duplicate init in plan/apply jobs
- ❌ Separate matrix jobs (inefficient)
- ❌ Basic output formatting

### **After Migration (Target State)**
- ✅ Dynamic service detection (auto-discover new services)
- ✅ Comprehensive error reporting
- ✅ Single orchestrated execution flow (no duplicate init)
- ✅ Unified plan/apply in single job
- ✅ Enhanced PR comments with collapsible sections
- ✅ Audit logging
- ✅ Scalable architecture  # 30 min timeout
        )
        
        result['output'] = tf_result.stdout
        result['success'] = (tf_result.returncode == 0)
        
        if not result['success']:
            result['error'] = tf_result.stderr
        
        return result
        
    except Exception as e:
        result['error'] = str(e)
        return result


def generate_results_summary(results, action):
    """Generate formatted markdown summary for PR comment"""
    
    summary = f"# 🎯 OCI Terraform {action.capitalize()} Results\n\n"
    
    # Success/failure counts
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)
    
    if success_count == total_count:
        summary += f"✅ **All {total_count} service(s) succeeded**\n\n"
    else:
        summary += f"⚠️ **{success_count}/{total_count} service(s) succeeded**\n\n"
    
    # Per-service results
    for result in results:
        icon = "✅" if result['success'] else "❌"
        summary += f"## {icon} {result['service']}\n\n"
        
        if result['success']:
            summary += "<details><summary>📋 Show Output</summary>\n\n"
            summary += f"```\n{result['output'][:2000]}\n```\n"
            summary += "</details>\n\n"
        else:
            summary += f"**Error:**\n```\n{result['error']}\n```\n\n"
    
    return summary


def write_pr_comment(content):
    """Write PR comment to file for GitHub Action to post"""
    with open('terraform-results.md', 'w') as f:
        f.write(content)Core Orchestrator | Week 1 | Simplified OCI orchestrator script |
| Phase 2: Workflow Creation | Week 1-2 | New workflow file |
| Phase 3: Testing & Rollout | Week 2-3 | Testing, documentation, migration |

**Total Duration:** 2-3Create Python Orchestrator** - Write simplified script
4. **Create New Workflow** - Build centralized controller workflow
5. **Configure GitHub Secrets** - Add OCI credentials
6. **Test in Sandbox** - Validate with test resources
7. **Pilot with Single Service** - Test with identity or network
8. **Full Migration** - Roll out to all services
9. **Deprecate Old Workflow** - Archive or remo