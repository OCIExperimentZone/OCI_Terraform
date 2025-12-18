# 🔄 Reusable Workflow Architecture

## Overview

This repository now uses a **centralized reusable workflow** approach for all OCI Terraform operations. This prevents workflow drift, simplifies maintenance, and ensures consistency across all environments.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Repository: OCIExperimentZone/OCI_Terraform (main branch)  │
│                                                               │
│  .github/workflows/                                          │
│  ├── oci-terraform-reusable.yml  ← REUSABLE (source of truth)│
│  └── oci-terraform-caller.yml    ← CALLER (minimal config)   │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │ calls
                            │
    ┌───────────────────────┴───────────────────────┐
    │                                               │
┌───▼────────────────┐                  ┌──────────▼──────────┐
│  This Repository   │                  │  Other Repositories │
│  Feature Branches  │                  │  (future use)       │
│                    │                  │                     │
│  Uses:             │                  │  Uses:              │
│  caller.yml        │                  │  caller.yml         │
└────────────────────┘                  └─────────────────────┘
```

## Benefits

### ✅ Centralized Management
- **Single source of truth**: All workflow logic is in `oci-terraform-reusable.yml` on main branch
- **Easy updates**: Update one file, all environments benefit
- **Version control**: Changes tracked in main branch history

### ✅ Prevents Workflow Drift
- **Protected**: Reusable workflow is on main branch (can be branch-protected)
- **Consistent**: All feature branches use the same workflow logic
- **Auditable**: Changes require PR to main branch

### ✅ Simplified Maintenance
- **Less duplication**: Feature branches only have caller workflow
- **Faster onboarding**: New repos just copy caller workflow
- **Easier testing**: Test workflow changes in one place

### ✅ Security
- **Controlled changes**: Workflow modifications require main branch access
- **Prevents tampering**: Feature branches can't modify workflow logic
- **Audit trail**: All workflow changes tracked via main branch commits

## File Structure

### 1. Reusable Workflow (`oci-terraform-reusable.yml`)
**Location**: `.github/workflows/` on **main branch**

**Purpose**: Contains all the actual workflow logic
- Change detection
- PR creation
- Terraform plan
- Terraform apply
- All orchestration logic

**Called by**: Other workflows using `uses:` syntax

**DO NOT MODIFY IN FEATURE BRANCHES**

### 2. Caller Workflow (`oci-terraform-caller.yml`)
**Location**: `.github/workflows/` in **any branch**

**Purpose**: Minimal configuration that calls the reusable workflow
- Defines triggers (push, PR, manual)
- Sets input parameters
- Passes secrets

**This is the only workflow file that runs directly**

## Usage

### For This Repository

1. **Main branch** contains:
   - `oci-terraform-reusable.yml` (the logic)
   - `oci-terraform-caller.yml` (the trigger)
   - `scripts/oci-terraform-orchestrator-v2.py`
   - `scripts/requirements.txt`

2. **Feature branches** contain:
   - `oci-terraform-caller.yml` (same as main)
   - Calls reusable workflow from main branch

3. **Environment branches** (Dev, Staging, Production):
   - `oci-terraform-caller.yml` (same as main)
   - Triggers apply when changes are merged

### For Other Repositories (Future)

Any repository can use this workflow by:

1. **Copy `oci-terraform-caller.yml`** to their `.github/workflows/` directory

2. **Update parameters** in the caller:
   ```yaml
   uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@main
   with:
     working_dir: 'your-service-dir'  # Change this
     terraform_version: '1.5.6'
     base_branch: 'Dev'                # Or Staging, Production
   ```

3. **Add secrets** to their repository

4. **Done!** No need to maintain complex workflow logic

## Configuration

### Caller Workflow Parameters

```yaml
with:
  working_dir: 'toronto'          # Your tfvars directory
  terraform_version: '1.5.6'      # Terraform version
  python_version: '3.11'          # Python version
  parallel: true                   # Enable parallel execution
  max_workers: 3                   # Parallel worker count
  base_branch: 'Dev'              # Target branch for PRs
```

### Required Secrets

All workflows need these secrets:
- `GT_APP_ID` - GitHub App ID for PR creation
- `GT_APP_PRIVATE_KEY` - GitHub App private key
- `OCI_USER` - OCI User OCID
- `OCI_FINGERPRINT` - OCI API key fingerprint
- `OCI_TENANCY` - OCI Tenancy OCID
- `OCI_REGION` - OCI Region
- `OCI_PRIVATE_KEY` - OCI Private key content
- `AWS_ROLE_ARN` - AWS role for state backend
- `AWS_REGION` - AWS region for state backend

## Workflow Logic

### 1. Feature Branch Push → Auto PR Creation
```
Feature branch push (tfvars change)
  ↓
Caller workflow triggers
  ↓
Calls reusable workflow
  ↓
Creates PR to Dev branch
  ↓
Posts initial status comment
```

### 2. Pull Request → Plan
```
PR opened/updated
  ↓
Caller workflow triggers
  ↓
Calls reusable workflow
  ↓
Runs terraform plan with orchestrator v2.0
  ↓
Posts plan results as PR comment
```

### 3. Merge to Dev/Staging/Production → Apply
```
PR merged to environment branch
  ↓
Caller workflow triggers
  ↓
Calls reusable workflow
  ↓
Runs terraform apply with orchestrator v2.0
  ↓
Uploads results as artifacts
```

## Updating the Workflow

### To modify workflow logic:

1. **Create PR to main branch**
   ```bash
   git checkout main
   git pull
   git checkout -b feature/update-workflow
   ```

2. **Edit reusable workflow**
   ```bash
   vim .github/workflows/oci-terraform-reusable.yml
   ```

3. **Test in feature branch**
   - The feature branch automatically uses the reusable workflow from main
   - OR reference your branch: `uses: ...@feature/update-workflow`

4. **Merge to main**
   - All branches immediately use the updated workflow
   - No need to update caller workflows

### To update configuration only:

1. **Edit caller workflow** in your branch
   ```bash
   vim .github/workflows/oci-terraform-caller.yml
   ```

2. **Change parameters** (working_dir, versions, etc.)

3. **Commit and push**

## Migration from Old Workflows

### Old Approach (❌ Not Recommended)
```
Each branch has full workflow definition
├── feature/branch-1
│   └── .github/workflows/oci-terraform-v2.yml (500 lines)
├── feature/branch-2
│   └── .github/workflows/oci-terraform-v2.yml (500 lines)
└── main
    └── .github/workflows/oci-terraform-v2.yml (500 lines)
```

**Problems:**
- Workflow drift between branches
- Hard to update (need to update every branch)
- Accidental modifications
- Inconsistent behavior

### New Approach (✅ Recommended)
```
Main branch has reusable workflow, branches have minimal caller
├── feature/branch-1
│   └── .github/workflows/oci-terraform-caller.yml (60 lines)
├── feature/branch-2
│   └── .github/workflows/oci-terraform-caller.yml (60 lines)
└── main
    ├── .github/workflows/oci-terraform-reusable.yml (450 lines)
    └── .github/workflows/oci-terraform-caller.yml (60 lines)
```

**Benefits:**
- Single source of truth
- Easy to update (one file)
- Prevents accidental changes
- Consistent across all branches

## Rollback

If you need to rollback to old workflow:

```bash
# Rename disabled old workflow back
mv .github/workflows/oci-terraform-v2.yml.disabled.old \
   .github/workflows/oci-terraform-v2.yml

# Disable caller workflow
mv .github/workflows/oci-terraform-caller.yml \
   .github/workflows/oci-terraform-caller.yml.disabled

git add .
git commit -m "Rollback to old workflow"
git push
```

## Best Practices

1. **Always use reusable workflow from main branch**
   - `uses: .../oci-terraform-reusable.yml@main`
   - This ensures stability

2. **Test workflow changes before merging to main**
   - Use feature branch reference during testing
   - `uses: .../oci-terraform-reusable.yml@feature/test`

3. **Keep caller workflow minimal**
   - Only configuration, no logic
   - Easy to review and maintain

4. **Protect main branch**
   - Require PR reviews for workflow changes
   - Prevents unauthorized modifications

5. **Document workflow changes**
   - Clear commit messages
   - Update this README if behavior changes

## Troubleshooting

### Workflow not triggering?
- Check caller workflow triggers match your use case
- Verify path filters: `toronto/**/*.tfvars`
- Check branch name patterns

### Wrong workflow version running?
- Verify `uses:` points to correct branch (`@main`)
- Check GitHub Actions UI for which workflow is running

### Secrets not working?
- Reusable workflows inherit secrets from caller
- Verify secret names match exactly
- Check repository secret configuration

### Need to test workflow changes?
```yaml
# Temporarily change caller to use your branch
uses: OCIExperimentZone/OCI_Terraform/.github/workflows/oci-terraform-reusable.yml@feature/your-test-branch
```

## Support

For issues or questions:
1. Check GitHub Actions logs
2. Review this README
3. Check main branch workflow file
4. Create issue in repository

---

**Last Updated**: December 17, 2025
**Version**: 2.0 (Reusable Workflow Architecture)
