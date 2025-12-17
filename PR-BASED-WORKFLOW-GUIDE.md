# 🔀 OCI Terraform PR-Based Workflow Guide

**Date:** December 17, 2025  
**Workflow:** PR-Based Approval with Auto-PR Creation

---

## 🎯 Overview

This workflow implements a **complete PR-based approval process** for OCI Terraform deployments in a **single repository**.

### **Key Features:**
- ✅ Auto-creates PRs from feature branches
- ✅ Runs terraform plan on PR open/update
- ✅ Requires approval before apply
- ✅ Manual approval gates for Production
- ✅ Apply only on merge to main branches
- ✅ Single-repo approach (no cross-repo dispatch)

---

## 🔄 Workflow Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: DEVELOPER PUSHES TO FEATURE BRANCH                     │
└─────────────────────────────────────────────────────────────────┘
                           ↓
    Push to feature/*, fix/*, update/*
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: AUTO-CREATE PR                                         │
│  - Detects changed services in toronto/                        │
│  - Creates PR to Dev/Staging/Production                        │
│  - Adds labels and checklist                                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: TERRAFORM PLAN (AUTO-TRIGGERED)                        │
│  - PR opened → workflow runs                                   │
│  - Executes terraform plan for changed services                │
│  - Posts results as PR comment                                 │
│  - Shows resource changes, errors                              │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: HUMAN REVIEW & APPROVAL                                │
│  - Team reviews terraform plan output                          │
│  - Checks approval checklist                                   │
│  - Approves PR if changes look correct                         │
│  - Can request changes if issues found                         │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: MERGE PR                                               │
│  - Developer/Approver merges PR                                │
│  - Merge to Dev/Staging/Production branch                      │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: TERRAFORM APPLY (AUTO-TRIGGERED)                       │
│  - Merge → workflow runs                                       │
│  - Production: requires manual approval gate                   │
│  - Executes terraform apply                                    │
│  - Posts deployment summary                                    │
│  - Uploads audit logs                                          │
└─────────────────────────────────────────────────────────────────┘
                           ↓
                    ✅ DEPLOYED!
```

---

## 📋 Detailed Steps

### **Step 1: Developer Workflow**

```bash
# 1. Create feature branch
git checkout -b feature/add-compute-instances

# 2. Make changes (e.g., CD3 export or manual updates)
cd toronto/compute
vim instance.tf

# 3. Commit and push
git add .
git commit -m "Add new compute instances for web tier"
git push origin feature/add-compute-instances
```

**What happens:**
- Push triggers `auto-create-pr` job
- Detects changes in `toronto/compute/`
- Auto-creates PR to Dev branch

---

### **Step 2: Auto-PR Creation**

The workflow automatically:

1. **Detects changed services**
   ```bash
   git diff --name-only HEAD^ | grep "^toronto/"
   # Result: toronto/compute/instance.tf
   # Extracted service: compute
   ```

2. **Creates PR with template**
   ```markdown
   ## 🎯 Automated Terraform Infrastructure Update
   
   **Branch:** feature/add-compute-instances
   **Changed Services:** compute
   **Triggered by:** @yourname
   
   ### 📋 What This PR Does
   This PR contains OCI infrastructure changes...
   
   ### ✅ Next Steps
   1. Review terraform plan output below
   2. Approve this PR if changes look correct
   3. Merge to trigger terraform apply
   
   ### 🤖 Automation Status
   - [ ] Terraform plan completed
   - [ ] Plan reviewed
   - [ ] PR approved
   - [ ] Ready to merge
   ```

3. **Adds labels**
   - `terraform`
   - `auto-created`
   - `oci-infrastructure`

---

### **Step 3: Terraform Plan (Automatic)**

When PR is opened/updated:

1. **Checkout PR branch**
2. **Run orchestrator in plan mode**
   ```bash
   python scripts/oci-terraform-orchestrator.py \
     --action plan \
     --working-dir ./toronto \
     --base-ref origin/Dev
   ```

3. **Post plan results as comment**
   ```markdown
   # 🎯 OCI Terraform Plan Results
   
   ## 📊 Summary
   | Service | Status | Duration | Changes |
   |---------|--------|----------|---------|
   | compute | ✅     | 45.2s    | 3       |
   
   ## 📋 Detailed Results
   ### ✅ compute
   Plan: 3 to add, 0 to change, 0 to destroy.
   
   ## ✅ Approval Checklist
   - [ ] Terraform plan shows expected changes
   - [ ] No unexpected resource deletions
   - [ ] Service dependencies are correct
   
   ⚠️ Merging this PR will trigger `terraform apply`
   ```

---

### **Step 4: Human Review**

**Reviewers should:**

1. ✅ Check terraform plan output
   - Verify resource counts
   - Check for unexpected changes
   - Look for deletions (red flag!)

2. ✅ Review service dependencies
   - If compute + network changed, network should run first
   - Check for cross-service references

3. ✅ Validate against intent
   - Does this match the CD3 export?
   - Are manual changes correct?

4. ✅ Approve PR
   - Click "Approve" in GitHub UI
   - Add comments if needed

---

### **Step 5: Merge PR**

**When ready:**

```bash
# Merge via GitHub UI or CLI
gh pr merge <pr-number> --merge
```

**Merge triggers:**
- Push event to Dev/Staging/Production branch
- `terraform-apply` job starts

---

### **Step 6: Terraform Apply (Automatic)**

On merge to main branches:

1. **Environment gate (Production only)**
   - Production deployments require manual approval
   - Reviewer clicks "Approve deployment" in GitHub UI
   - Other environments (Dev/Staging) auto-deploy

2. **Run terraform apply**
   ```bash
   python scripts/oci-terraform-orchestrator.py \
     --action apply \
     --working-dir ./toronto
   ```

3. **Upload results**
   - Audit logs (90-day retention)
   - Apply results
   - Deployment summary

4. **Notify on completion**
   - GitHub step summary
   - Can add Slack/email notifications

---

## 🔐 Environment Configuration

### **GitHub Environments Setup**

Create three environments in repository settings:

#### **1. Development (Dev branch)**
- **Protection rules:** None (auto-deploy)
- **Reviewers:** Optional
- **Wait timer:** 0 minutes

#### **2. Staging (Staging branch)**
- **Protection rules:** Optional
- **Reviewers:** 1 required (team lead)
- **Wait timer:** 0 minutes

#### **3. Production (Production branch)**
- **Protection rules:** Required
- **Reviewers:** 2 required (senior engineers)
- **Wait timer:** 5 minutes
- **Prevent self-review:** Enabled

### **Required Secrets**

Same as before - configure in repository settings:

**OCI Credentials:**
- `OCI_USER`
- `OCI_TENANCY`
- `OCI_FINGERPRINT`
- `OCI_REGION`
- `OCI_PRIVATE_KEY`

**AWS Credentials (State Backend):**
- `AWS_ROLE_ARN`
- `AWS_REGION`

---

## 🎛️ Configuration Options

### **Branch Strategy**

**Option 1: GitFlow (Recommended)**
```
feature/* → Dev → Staging → Production
```

**Option 2: Simplified**
```
feature/* → main
```

**Option 3: Environment Branches**
```
feature/* → dev-branch
fix/*     → staging-branch
hotfix/*  → production-branch
```

### **Auto-PR Target**

Edit workflow to change default target:

```yaml
base: Dev  # Change to: Staging, Production, or main
```

### **Approval Requirements**

**For stricter controls:**

```yaml
environment:
  name: production
  # Requires:
  # - Manual approval
  # - 2 reviewers
  # - Wait 5 minutes before deploy
```

---

## 🆚 Comparison: Single-Repo vs Multi-Repo

### **This Workflow (Single-Repo)**

```
OCI_Terraform Repo (Single)
  ├── toronto/ (services)
  ├── modules/
  ├── scripts/ (orchestrator)
  └── .github/workflows/
      └── oci-terraform-pr-based.yml
```

**Pros:**
- ✅ Simpler to manage (one repo)
- ✅ Easier for CD3 exports (all in one place)
- ✅ Built-in PR review process
- ✅ No cross-repo dispatch needed

**Cons:**
- ⚠️ All team members need repo access
- ⚠️ Can't isolate controller from infrastructure code

---

### **AWS Approach (Multi-Repo)**

```
dev-deployment (Repo 1)        centralized-controller (Repo 2)
  ├── S3/                        ├── scripts/
  └── triggers controller →      ├── policies/
                                 └── main.tf
```

**Pros:**
- ✅ Separation of concerns
- ✅ Controller code isolated
- ✅ Can control access per repo

**Cons:**
- ❌ More complex (repository_dispatch)
- ❌ Harder to track changes
- ❌ Two repos to manage

---

## 🎯 Use Case Examples

### **Use Case 1: CD3 Export Update**

```bash
# 1. Run CD3 tool (exports to toronto/network/)
cd3_automation.py --export subnets

# 2. Create feature branch
git checkout -b feature/cd3-export-subnets

# 3. Commit CD3 changes
git add toronto/network/cd3-demo-tenancy_subnets.auto.tfvars
git commit -m "CD3 export: Add new subnets for web tier"
git push

# 4. Auto-PR created → Plan runs → Review → Approve → Merge → Apply ✅
```

---

### **Use Case 2: Manual Infrastructure Change**

```bash
# 1. Create feature branch
git checkout -b feature/add-database

# 2. Edit terraform
vim toronto/database/db.tf

# 3. Push
git push origin feature/add-database

# 4. Auto-PR → Plan → Shows new database resources → Approve → Apply ✅
```

---

### **Use Case 3: Emergency Hotfix**

```bash
# 1. Create hotfix branch
git checkout -b hotfix/fix-security-group

# 2. Fix issue
vim toronto/network/cd3-demo-tenancy_seclists.auto.tfvars

# 3. Push
git push

# 4. Auto-PR to Dev → Fast approval → Merge → Apply
# 5. Cherry-pick to Staging/Production if needed
```

---

## 🚨 Error Handling

### **What if Plan Fails?**

1. Plan failure posted in PR comment
2. PR cannot be merged (check fails)
3. Developer fixes issue
4. Push update → Plan re-runs

### **What if Apply Fails?**

1. Apply stops at failed service
2. Error logged in audit
3. Workflow marked as failed
4. Team investigates
5. Fix in new PR or rollback

---

## 📊 Monitoring & Audit

### **View Deployment History**

```bash
# GitHub Actions
Actions → Workflows → "OCI Terraform Controller (PR-Based)"

# Artifacts
Actions → Run → Artifacts → terraform-apply-*
```

### **Audit Logs**

Each apply creates `terraform-audit.json`:

```json
{
  "timestamp": "2025-12-17T10:30:00Z",
  "environment": "Dev",
  "actor": "pragadeeswarpa",
  "services": ["compute", "network"],
  "results": [...]
}
```

---

## ✅ Testing Checklist

Before going live:

- [ ] Create test feature branch
- [ ] Push small change to toronto/identity/
- [ ] Verify auto-PR created
- [ ] Check plan output in PR comment
- [ ] Approve PR
- [ ] Merge and verify apply runs
- [ ] Check artifacts uploaded
- [ ] Test Production approval gate

---

## 🎉 Summary

**This PR-based workflow provides:**

✅ **Automation:** Auto-PR creation from feature branches  
✅ **Validation:** Terraform plan on every PR  
✅ **Safety:** Human approval required before apply  
✅ **Audit:** Complete deployment history  
✅ **Flexibility:** Environment-specific approval gates  
✅ **Simplicity:** Single-repo approach for CD3  

**vs. Old Workflow:**
- ❌ Manual PR creation → ✅ Auto-created
- ❌ No approval process → ✅ Built-in PR review
- ❌ Direct apply on push → ✅ Apply only after approval

---

**Ready to deploy!** 🚀
