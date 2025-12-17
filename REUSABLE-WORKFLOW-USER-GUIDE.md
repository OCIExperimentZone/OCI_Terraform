# 🚀 OCI Terraform Reusable Workflow - Complete User Guide

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Initial Setup](#initial-setup)
4. [Configuration Guide](#configuration-guide)
5. [Daily Usage](#daily-usage)
6. [Advanced Configuration](#advanced-configuration)
7. [Multi-Environment Setup](#multi-environment-setup)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## Overview

### What is This?
A centralized, reusable GitHub Actions workflow for managing OCI Terraform deployments with:
- ✅ **Zero hardcoded paths** - Works with any directory structure
- ✅ **Auto PR creation** - Feature branches automatically create PRs
- ✅ **Dependency ordering** - Services deployed in correct sequence
- ✅ **Parallel execution** - Fast deployments
- ✅ **Centralized management** - Update once, apply everywhere

### Architecture
```
┌──────────────────────────────────────────────────────┐
│  Main Branch (Single Source of Truth)                │
│                                                       │
│  ├── .github/workflows/                              │
│  │   ├── oci-terraform-reusable.yml  ← Logic here   │
│  │   └── oci-terraform-caller.yml    ← Just config  │
│  └── scripts/                                        │
│      └── oci-terraform-orchestrator-v2.py           │
└──────────────────────────────────────────────────────┘
                       ▲
                       │ All branches use this
                       │
         ┌─────────────┴─────────────┐
         │                           │
    Feature Branches          Environment Branches
    (Auto PR)                 (Auto Deploy)
```

---

## Quick Start

### For First-Time Users

**Step 1: Set Repository Variables** (5 minutes)
```
GitHub Repo → Settings → Secrets and variables → Actions → Variables
```

Add these variables:
- `WORKING_DIR` = `toronto`
- `BASE_BRANCH` = `Dev`

**Step 2: Set Repository Secrets** (Already done if you're using this repo)
All OCI and AWS credentials should already be configured.

**Step 3: Test It**
```bash
# Create feature branch
git checkout -b feature/test-workflow

# Edit a tfvars file
vim toronto/identity/test.tfvars
# Add a comment: # Test workflow

# Commit and push
git add toronto/identity/test.tfvars
git commit -m "Test workflow"
git push origin feature/test-workflow
```

**Expected Result:**
- ✅ Workflow runs automatically
- ✅ PR created to Dev branch
- ✅ Terraform plan posted as PR comment

---

## Initial Setup

### 1. Configure Repository Variables

Go to: **GitHub Repo → Settings → Secrets and variables → Actions → Variables tab**

Click **"New repository variable"** and add:

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `WORKING_DIR` | `toronto` | Directory containing your service folders |
| `BASE_BRANCH` | `Dev` | Target branch for PRs (Dev, Staging, or Production) |
| `TERRAFORM_VERSION` | `1.5.6` | Terraform version (optional, defaults to 1.5.6) |
| `PYTHON_VERSION` | `3.11` | Python version (optional, defaults to 3.11) |
| `MAX_WORKERS` | `3` | Parallel execution workers (optional, defaults to 3) |

**Screenshot Guide:**
```
Settings → Secrets and variables → Actions
    ↓
Click "Variables" tab
    ↓
Click "New repository variable"
    ↓
Name: WORKING_DIR
Value: toronto
    ↓
Click "Add variable"
```

### 2. Verify Repository Secrets

Go to: **GitHub Repo → Settings → Secrets and variables → Actions → Secrets tab**

Verify these secrets exist:

**GitHub App Secrets:**
- `GT_APP_ID`
- `GT_APP_PRIVATE_KEY`

**OCI Secrets:**
- `OCI_USER`
- `OCI_FINGERPRINT`
- `OCI_TENANCY`
- `OCI_REGION`
- `OCI_PRIVATE_KEY`

**AWS Secrets (for Terraform state):**
- `AWS_ROLE_ARN`
- `AWS_REGION`

### 3. Configure AWS IAM Role Trust Policy

Update your AWS IAM role trust policy to allow GitHub Actions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": [
                        "repo:OCIExperimentZone/OCI_Terraform:pull_request",
                        "repo:OCIExperimentZone/OCI_Terraform:ref:refs/heads/*"
                    ]
                }
            }
        }
    ]
}
```

**Replace:**
- `YOUR_ACCOUNT_ID` with your AWS account ID
- `OCIExperimentZone/OCI_Terraform` with your org/repo

---

## Configuration Guide

### Understanding Configuration Priority

The workflow uses this priority order:

```
1. Manual Input (workflow_dispatch)     ← Highest priority
   ↓
2. Repository Variables (vars.*)
   ↓
3. Default Values                       ← Lowest priority
```

**Example:** If you set `WORKING_DIR=toronto` in repo variables but manually trigger with `working_dir=staging`, it will use `staging`.

### Configuration Options

#### Option 1: Repository Variables (Recommended)
**When to use:** Standard setup for consistent behavior across all workflows

**Setup:**
1. Go to Settings → Secrets and variables → Actions → Variables
2. Add variables (see Initial Setup section)

**Pros:**
- ✅ Configure once, use everywhere
- ✅ Easy to change (no code edits)
- ✅ Visible in GitHub UI
- ✅ Can be different per environment (via branch variables)

**Cons:**
- ❌ Requires repository settings access

#### Option 2: Manual Workflow Trigger
**When to use:** One-time override or testing

**Usage:**
1. Go to Actions tab
2. Select "🎯 OCI Terraform" workflow
3. Click "Run workflow"
4. Fill in parameters
5. Click "Run workflow"

**Pros:**
- ✅ Override any setting per run
- ✅ Test different configurations
- ✅ No permanent changes

**Cons:**
- ❌ Manual process
- ❌ Not automatic on push/PR

#### Option 3: Edit Caller Workflow (Not Recommended)
**When to use:** Never, unless testing workflow changes

**Why not:**
- ❌ Creates workflow drift
- ❌ Hard to maintain
- ❌ Defeats purpose of reusable workflows

---

## Daily Usage

### Scenario 1: Making Infrastructure Changes

**Goal:** Update OCI infrastructure by modifying tfvars files

**Steps:**

1. **Create Feature Branch**
   ```bash
   git checkout Dev
   git pull
   git checkout -b feature/update-identity-policies
   ```

2. **Make Changes**
   ```bash
   # Edit tfvars file
   vim toronto/identity/cd3-demo-tenancy_policies.auto.tfvars
   
   # Make your changes
   # Example: Add new policy statement
   ```

3. **Commit and Push**
   ```bash
   git add toronto/identity/cd3-demo-tenancy_policies.auto.tfvars
   git commit -m "Add new identity policy for developers"
   git push origin feature/update-identity-policies
   ```

4. **Automatic Workflow Execution**
   ```
   ✅ Workflow detects tfvars change
   ✅ Auto-creates PR to Dev branch
   ✅ Posts initial status comment
   ✅ Runs terraform plan
   ✅ Posts plan results to PR
   ```

5. **Review PR**
   - Go to Pull Requests tab
   - Review the auto-created PR
   - Check terraform plan results
   - Look for:
     - ✅ Correct services detected
     - ✅ Expected changes shown
     - ✅ No unexpected deletions
     - ✅ Dependency order correct

6. **Approve and Merge**
   ```
   If plan looks good:
     → Approve PR
     → Merge to Dev branch
   
   Automatic apply:
     → Workflow runs terraform apply
     → Infrastructure updated
     → Results uploaded as artifacts
   ```

### Scenario 2: Multi-Service Update

**Goal:** Update multiple services in one PR

**Steps:**

1. **Create Branch**
   ```bash
   git checkout -b feature/network-and-security-update
   ```

2. **Edit Multiple Services**
   ```bash
   # Update network configuration
   vim toronto/network/cd3-demo-tenancy_major-objects.auto.tfvars
   
   # Update security settings
   vim toronto/security/security-zones.auto.tfvars
   
   # Update identity policies
   vim toronto/identity/cd3-demo-tenancy_policies.auto.tfvars
   ```

3. **Commit All Changes**
   ```bash
   git add toronto/network/*.tfvars toronto/security/*.tfvars toronto/identity/*.tfvars
   git commit -m "Update network, security, and identity configuration"
   git push origin feature/network-and-security-update
   ```

4. **Automatic PR Shows All Services**
   ```
   PR Title: "OCI Terraform: network,security,identity [Dev]"
   
   PR Body:
   - Services: network, security, identity
   - Changed Files: 3
   - Execution order shown in plan
   ```

5. **Review Plan for All Services**
   - Check execution order respects dependencies
   - Network changes applied first
   - Security and identity follow
   - No conflicts between services

### Scenario 3: Emergency Hotfix

**Goal:** Quick fix that needs immediate deployment

**Steps:**

1. **Create Hotfix Branch**
   ```bash
   git checkout Dev
   git pull
   git checkout -b hotfix/fix-security-rule
   ```

2. **Make Minimal Change**
   ```bash
   vim toronto/security/security-lists.auto.tfvars
   # Fix the security rule
   ```

3. **Fast-track Process**
   ```bash
   git add toronto/security/security-lists.auto.tfvars
   git commit -m "HOTFIX: Fix security rule blocking production traffic"
   git push origin hotfix/fix-security-rule
   ```

4. **Expedited Review**
   - Auto-PR created immediately
   - Review plan quickly
   - Get approval
   - Merge immediately
   - Apply runs automatically

### Scenario 4: Manual Workflow Trigger

**Goal:** Run plan manually without creating PR

**Steps:**

1. **Go to Actions Tab**
   ```
   GitHub → Actions → "🎯 OCI Terraform" → "Run workflow"
   ```

2. **Select Branch**
   ```
   Use workflow from: main (or any branch)
   ```

3. **Configure Parameters**
   ```
   Working directory: toronto
   Parallel execution: ✓ (checked)
   Base branch: Dev
   ```

4. **Click "Run workflow"**
   - Plan runs immediately
   - Results appear in workflow logs
   - No PR created
   - Useful for testing

---

## Advanced Configuration

### Multi-Environment Setup

#### Option A: Using Branch Variables (Recommended)

GitHub supports environment-specific variables:

**Setup for Dev Environment:**
```
Settings → Environments → Dev → Variables
- WORKING_DIR = toronto
- BASE_BRANCH = Dev
- MAX_WORKERS = 3
```

**Setup for Staging Environment:**
```
Settings → Environments → Staging → Variables
- WORKING_DIR = staging
- BASE_BRANCH = Staging
- MAX_WORKERS = 2
```

**Setup for Production Environment:**
```
Settings → Environments → Production → Variables
- WORKING_DIR = production
- BASE_BRANCH = Production
- MAX_WORKERS = 1  (safer, sequential)
```

#### Option B: Multiple Caller Workflows

Create separate caller workflows for each environment:

**File: `.github/workflows/oci-terraform-dev.yml`**
```yaml
name: 🎯 OCI Terraform (Dev)

on:
  push:
    branches: [Dev]
    paths: ['toronto/**/*.tfvars']
  pull_request:
    branches: [Dev]

jobs:
  call-reusable-workflow:
    uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@main
    with:
      working_dir: 'toronto'
      base_branch: 'Dev'
      max_workers: 3
    secrets: inherit
```

**File: `.github/workflows/oci-terraform-staging.yml`**
```yaml
name: 🎯 OCI Terraform (Staging)

on:
  push:
    branches: [Staging]
    paths: ['staging/**/*.tfvars']
  pull_request:
    branches: [Staging]

jobs:
  call-reusable-workflow:
    uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@main
    with:
      working_dir: 'staging'
      base_branch: 'Staging'
      max_workers: 2
    secrets: inherit
```

**File: `.github/workflows/oci-terraform-production.yml`**
```yaml
name: 🎯 OCI Terraform (Production)

on:
  push:
    branches: [Production]
    paths: ['production/**/*.tfvars']
  pull_request:
    branches: [Production]

jobs:
  call-reusable-workflow:
    uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@main
    with:
      working_dir: 'production'
      base_branch: 'Production'
      max_workers: 1  # Sequential for safety
      parallel: false
    secrets: inherit
```

### Custom Terraform Versions per Branch

**Option 1: Branch-specific Variables**
```
Environments → Dev → Variables
- TERRAFORM_VERSION = 1.5.6

Environments → Production → Variables
- TERRAFORM_VERSION = 1.4.6  (more stable)
```

**Option 2: Workflow Override**
```yaml
with:
  terraform_version: ${{ github.ref == 'refs/heads/Production' && '1.4.6' || '1.5.6' }}
```

### Parallel Execution Control

**Development:** Fast, parallel execution
```yaml
parallel: true
max_workers: 5
```

**Staging:** Moderate parallelism
```yaml
parallel: true
max_workers: 3
```

**Production:** Safe, sequential execution
```yaml
parallel: false
max_workers: 1
```

---

## Multi-Environment Setup

### Recommended Directory Structure

```
repository-root/
├── .github/
│   └── workflows/
│       ├── oci-terraform-reusable.yml     (main branch)
│       ├── oci-terraform-caller.yml       (all branches)
│       └── README.md
├── scripts/
│   ├── oci-terraform-orchestrator-v2.py
│   └── requirements.txt
├── toronto/                                (Dev environment)
│   ├── identity/
│   │   └── *.tfvars
│   ├── network/
│   │   └── *.tfvars
│   └── database/
│       └── *.tfvars
├── staging/                                (Staging environment)
│   ├── identity/
│   ├── network/
│   └── database/
└── production/                             (Production environment)
    ├── identity/
    ├── network/
    └── database/
```

### Branch Strategy

```
feature/xxx → Dev → Staging → Production
     ↓         ↓        ↓          ↓
   Auto PR   Apply    Apply      Apply
            (toronto) (staging) (production)
```

### Configuration per Environment

| Environment | Branch | Working Dir | Parallel | Workers | Approval |
|------------|--------|-------------|----------|---------|----------|
| Dev | Dev | toronto | ✅ Yes | 3 | None |
| Staging | Staging | staging | ✅ Yes | 2 | Manual |
| Production | Production | production | ❌ No | 1 | Required |

### Setting Up Environments in GitHub

1. **Create Environments**
   ```
   Settings → Environments → New environment
   ```

2. **Configure Dev Environment**
   ```
   Name: development
   
   Variables:
   - WORKING_DIR = toronto
   - BASE_BRANCH = Dev
   - MAX_WORKERS = 3
   
   Protection rules: None
   ```

3. **Configure Staging Environment**
   ```
   Name: staging
   
   Variables:
   - WORKING_DIR = staging
   - BASE_BRANCH = Staging
   - MAX_WORKERS = 2
   
   Protection rules:
   - ✓ Required reviewers (1 person)
   - ✓ Wait timer: 5 minutes
   ```

4. **Configure Production Environment**
   ```
   Name: production
   
   Variables:
   - WORKING_DIR = production
   - BASE_BRANCH = Production
   - MAX_WORKERS = 1
   
   Protection rules:
   - ✓ Required reviewers (2 people)
   - ✓ Wait timer: 30 minutes
   - ✓ Prevent self-review
   ```

---

## Troubleshooting

### Workflow Not Triggering

**Problem:** Pushed changes but workflow didn't run

**Checks:**
1. ✅ Is it a `.tfvars` file?
   ```bash
   git diff --name-only HEAD^ | grep "\.tfvars$"
   ```

2. ✅ Is the workflow file present?
   ```bash
   ls .github/workflows/oci-terraform-caller.yml
   ```

3. ✅ Check workflow file syntax
   ```bash
   # In GitHub: Actions tab → Look for syntax errors
   ```

4. ✅ Check path filters
   ```yaml
   # Workflow should have:
   paths:
     - '**/*.tfvars'  # Matches ANY tfvars file
   ```

**Solution:**
```bash
# View GitHub Actions logs
GitHub → Actions → Latest run → View logs
```

### PR Not Created

**Problem:** Feature branch pushed but no PR appeared

**Checks:**
1. ✅ Branch name correct?
   ```bash
   # Must start with: feature/, fix/, update/, or hotfix/
   git branch --show-current
   ```

2. ✅ GitHub App token working?
   ```bash
   # Check workflow logs for:
   # "Error: RequestError [HttpError]: GitHub Actions is not permitted"
   ```

3. ✅ PR already exists?
   ```bash
   gh pr list --head $(git branch --show-current) --base Dev
   ```

**Solution:**
```bash
# If GitHub App issues, check secrets:
# Settings → Secrets → Verify GT_APP_ID and GT_APP_PRIVATE_KEY

# If PR exists, workflow logs will show:
# "✅ Pull Request already exists"
```

### Terraform Plan Failed

**Problem:** Plan job failed with errors

**Checks:**
1. ✅ Check AWS credentials
   ```
   Logs → "🔐 Configure AWS Credentials" step
   Look for: "AssumeRoleWithWebIdentity failed"
   ```

2. ✅ Check OCI credentials
   ```
   Logs → "🔐 Configure OCI CLI" step
   Look for: "Authentication failed"
   ```

3. ✅ Check Terraform state access
   ```
   Logs → "📋 Run Terraform Plan" step
   Look for: "Error acquiring state lock"
   ```

4. ✅ Check orchestrator script
   ```
   Logs → "📋 Run Terraform Plan" step
   Look for: Python errors or missing dependencies
   ```

**Common Solutions:**

**AWS Trust Policy Issue:**
```json
// Add to IAM role trust policy:
{
    "StringLike": {
        "token.actions.githubusercontent.com:sub": [
            "repo:YOUR_ORG/YOUR_REPO:pull_request",
            "repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/*"
        ]
    }
}
```

**OCI Credentials:**
```bash
# Verify secrets are correct:
# Settings → Secrets → Check OCI_* secrets
# - OCI_USER
# - OCI_FINGERPRINT
# - OCI_TENANCY
# - OCI_REGION
# - OCI_PRIVATE_KEY (must be valid PEM format)
```

**Python Dependencies:**
```bash
# Check scripts/requirements.txt exists and is committed
# Workflow installs from: pip install -r scripts/requirements.txt
```

### Wrong Working Directory

**Problem:** Workflow looking in wrong directory

**Checks:**
1. ✅ Check repository variables
   ```
   Settings → Secrets and variables → Actions → Variables
   Look for: WORKING_DIR
   ```

2. ✅ Check workflow inputs
   ```
   Actions → Workflow run → "call-reusable-workflow" → Input parameters
   ```

3. ✅ Check logs
   ```
   Logs → "🔍 Detect Changes" step
   Look for: "Comparing against: HEAD^"
   Should show: working_dir = your-expected-directory
   ```

**Solution:**
```bash
# Update repository variable:
Settings → Secrets and variables → Actions → Variables
Edit WORKING_DIR → Set to correct path (e.g., "toronto")

# Or override via manual trigger:
Actions → Run workflow → Working directory: "staging"
```

### Reusable Workflow Not Found

**Problem:** Error: "workflow 'oci-terraform-reusable.yml' not found"

**Checks:**
1. ✅ File exists on main branch
   ```bash
   git checkout main
   ls .github/workflows/oci-terraform-reusable.yml
   ```

2. ✅ Caller workflow references correct branch
   ```yaml
   uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@main
   #                                                                                   ^^^^
   # Must be: @main (or your reusable workflow branch)
   ```

3. ✅ Repository and path are correct
   ```yaml
   uses: YOUR_ORG/YOUR_REPO/.github/workflows/oci-terraform-reusable.yml@main
   #     ^^^^^^^^ ^^^^^^^^                                                   
   # Must match your organization and repository name
   ```

**Solution:**
```bash
# Push reusable workflow to main:
git checkout main
git add .github/workflows/oci-terraform-reusable.yml
git commit -m "Add reusable workflow"
git push origin main

# Update caller workflow reference:
vim .github/workflows/oci-terraform-caller.yml
# Fix the 'uses:' line to point to correct org/repo@main
```

### Permission Denied Errors

**Problem:** "Error: Resource not accessible by integration"

**Checks:**
1. ✅ Workflow permissions
   ```yaml
   # In caller workflow:
   permissions:
     contents: write
     pull-requests: write
     issues: write
     id-token: write
     actions: write
   ```

2. ✅ GitHub App permissions
   ```
   GitHub → Settings → GitHub Apps → Your App
   Check permissions:
   - Contents: Read & write
   - Pull requests: Read & write
   - Issues: Read & write
   ```

3. ✅ Repository settings
   ```
   Settings → Actions → General
   Workflow permissions: "Read and write permissions"
   ✓ Allow GitHub Actions to create and approve pull requests
   ```

**Solution:**
```bash
# Update repository settings:
Settings → Actions → General → Workflow permissions
→ Select "Read and write permissions"
→ Check "Allow GitHub Actions to create and approve pull requests"

# Or update GitHub App permissions
```

---

## FAQ

### Q: Can I use this workflow in multiple repositories?

**A:** Yes! That's the whole point. Just copy the caller workflow to any repository:

```bash
# In new repository:
mkdir -p .github/workflows
cp oci-terraform-caller.yml your-new-repo/.github/workflows/

# Update the 'uses:' line to point to your main repo:
uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@main
```

### Q: How do I test workflow changes without affecting production?

**A:** Use a feature branch for the reusable workflow:

```bash
# Create workflow testing branch
git checkout -b feature/test-workflow-changes

# Edit reusable workflow
vim .github/workflows/oci-terraform-reusable.yml

# Push to GitHub
git push origin feature/test-workflow-changes

# In caller workflow, temporarily change:
uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@feature/test-workflow-changes
#                                                                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
```

### Q: Can I disable automatic PR creation?

**A:** Yes, modify the reusable workflow's job condition:

```yaml
# In oci-terraform-reusable.yml:
auto-create-pr:
  if: false  # Disables auto-PR creation
```

Or only enable for specific branches:
```yaml
auto-create-pr:
  if: |
    needs.detect-changes.outputs.has_changes == 'true' &&
    startsWith(github.ref, 'refs/heads/feature/automation-')  # Only feature/automation-* branches
```

### Q: How do I run only plan without apply?

**A:** Use manual workflow trigger:

```
Actions → 🎯 OCI Terraform → Run workflow
```

This runs plan on the selected branch but doesn't trigger apply (because it's not a push to Dev/Staging/Production).

### Q: Can I use different orchestrator scripts per environment?

**A:** Yes, but not recommended. Better approach:

```yaml
# In reusable workflow, add input:
inputs:
  orchestrator_script:
    type: string
    default: 'scripts/oci-terraform-orchestrator-v2.py'

# Then use:
python3 ${{ inputs.orchestrator_script }} \
  --action plan ...
```

### Q: How do I add manual approval for Dev environment?

**A:** Configure environment protection:

```
Settings → Environments → development → Protection rules
✓ Required reviewers: Select team members
Save protection rules
```

Then update reusable workflow:
```yaml
terraform-apply:
  environment:
    name: development  # Adds to Dev environment
```

### Q: Can I run terraform apply without pushing to environment branch?

**A:** Yes, use workflow_dispatch with apply action:

```yaml
# Add to caller workflow:
workflow_dispatch:
  inputs:
    action:
      description: 'Action to perform'
      type: choice
      options:
        - plan
        - apply
      default: 'plan'

# Then manually trigger with action=apply
```

### Q: How do I see what changed in the last deployment?

**A:** Check workflow artifacts:

```
Actions → Latest workflow run → Artifacts
Download: terraform-apply-XXXX
Contains:
- terraform-results.md (summary)
- terraform-audit.json (full details)
```

### Q: Can I use different AWS accounts per environment?

**A:** Yes, use environment-specific secrets:

```
Settings → Environments → development → Secrets
Add: AWS_ROLE_ARN (dev account role)

Settings → Environments → production → Secrets
Add: AWS_ROLE_ARN (prod account role)
```

### Q: How do I rollback a failed deployment?

**A:** Two options:

**Option 1: Revert the merge commit**
```bash
git revert <merge-commit-sha>
git push origin Dev  # Triggers apply with reverted changes
```

**Option 2: Manual rollback**
```bash
git checkout <previous-good-commit>
# Manually trigger workflow with apply action
```

### Q: Can I skip certain services from deployment?

**A:** The orchestrator automatically detects changed services. To skip:

**Option 1: Don't commit changes to that service's tfvars**

**Option 2: Modify orchestrator script to exclude services:**
```python
# In orchestrator script, add exclusion:
EXCLUDED_SERVICES = ['service-to-skip']
if service in EXCLUDED_SERVICES:
    continue
```

### Q: How do I see dependency order before deployment?

**A:** Check the plan output in PR comments:

```
📊 Execution Order (Dependency Levels)
Level 1: network, identity
Level 2: security
Level 3: compute, database
Level 4: loadbalancer
```

### Q: Can I use this with other cloud providers?

**A:** Yes, but requires modifications:

1. Update reusable workflow to accept different provider credentials
2. Modify orchestrator script to support multiple providers
3. Add provider-specific configuration

---

## Best Practices

### 1. Branch Naming
```
✅ Good:
- feature/add-new-policy
- fix/security-rule-typo
- update/network-configuration
- hotfix/critical-issue

❌ Bad:
- my-changes
- test
- temp
- wip
```

### 2. Commit Messages
```
✅ Good:
- "Add security policy for developer group"
- "Update network CIDR blocks for new subnet"
- "Fix: Correct IAM policy statement"

❌ Bad:
- "update"
- "changes"
- "test"
```

### 3. PR Review Checklist
```
Before approving PR:
☐ Terraform plan shows expected changes
☐ No unexpected resource deletions
☐ Dependency order is correct
☐ No sensitive data in tfvars
☐ Service names are correct
☐ Changed files match description
```

### 4. Environment Promotion
```
Development → Staging → Production

✅ Always test in Dev first
✅ Review plan output carefully
✅ Staging should mirror Production
✅ Production requires manual approval
```

### 5. Secrets Management
```
✅ Do: Use GitHub Secrets
✅ Do: Rotate secrets regularly
✅ Do: Use different credentials per environment
✅ Do: Audit secret access

❌ Don't: Hardcode secrets in tfvars
❌ Don't: Share secrets in Slack/Email
❌ Don't: Use same secrets across environments
```

---

## Support and Resources

### Documentation
- **Reusable Workflow**: `.github/workflows/oci-terraform-reusable.yml`
- **Caller Workflow**: `.github/workflows/oci-terraform-caller.yml`
- **Orchestrator**: `scripts/oci-terraform-orchestrator-v2.py`
- **Workflow README**: `.github/workflows/README.md`

### Getting Help
1. Check this user guide
2. Review GitHub Actions logs
3. Check workflow README
4. Review orchestrator documentation
5. Create GitHub issue

### Useful Commands

**Check what workflow is running:**
```bash
gh workflow list
gh workflow view "🎯 OCI Terraform"
```

**View workflow runs:**
```bash
gh run list --workflow="oci-terraform-caller.yml"
gh run view <run-id>
```

**Check repository variables:**
```bash
gh variable list
```

**Check repository secrets:**
```bash
gh secret list
```

**Manually trigger workflow:**
```bash
gh workflow run "🎯 OCI Terraform" \
  --ref feature/your-branch \
  -f working_dir=toronto \
  -f parallel=true
```

---

**Last Updated:** December 17, 2025  
**Version:** 2.0  
**Author:** DevOps Team

