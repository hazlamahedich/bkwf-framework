# Git Workflow Guide

## 🔄 Branching Strategy

This project follows a **Git Flow** branching model to ensure stable releases and organized development.

### Branch Structure

```
main (production-ready code)
├── develop (integration branch)
│   ├── feature/feature-name (new features)
│   ├── feature/bug-fixes (bug fixes)
│   └── feature/improvements (enhancements)
└── hotfix/critical-fix (emergency fixes)
```

### Branch Descriptions

| Branch | Purpose | Protected | Merge Method |
|--------|---------|-----------|--------------|
| `main` | Production-ready, stable code | ✅ Yes | Pull Request only |
| `develop` | Integration branch for features | ✅ Yes | Pull Request only |
| `feature/*` | New features and improvements | ❌ No | Direct merge to develop |
| `hotfix/*` | Critical production fixes | ❌ No | Direct merge to main + develop |

## 🚀 Current Setup Status

✅ **Main Branch**: Protected production branch  
✅ **Develop Branch**: Created and pushed to remote  
✅ **Feature Branch**: `feature/documentation-updates` ready for work  

## 📋 Developer Workflow

### 1. Starting New Work

```bash
# Always start from develop branch
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/your-feature-name

# Example feature branch names:
# feature/new-strategy-implementation
# feature/risk-management-improvements  
# feature/performance-optimization
# feature/bug-fixes
```

### 2. Making Changes

```bash
# Make your changes
# Edit files, add features, fix bugs

# Stage changes
git add .

# Commit with descriptive message
git commit -m "Add: new CNN-LSTM strategy implementation

- Implement deep learning model architecture
- Add training pipeline with validation
- Include export functionality for MT5/Pine
- Update documentation and parameter reference"
```

### 3. Pushing Feature Branch

```bash
# Push feature branch to remote
git push -u origin feature/your-feature-name
```

### 4. Merging to Develop

```bash
# Switch to develop
git checkout develop

# Merge your feature
git merge feature/your-feature-name

# Push to remote develop
git push origin develop

# Clean up feature branch
git branch -d feature/your-feature-name
git push origin --delete feature/your-feature-name
```

### 5. Promoting to Main (Release)

```bash
# When develop is stable and ready for release
git checkout main
git pull origin main

# Merge develop into main
git merge develop

# Tag the release
git tag -a v1.0.0 -m "Release v1.0.0: Initial stable release with documentation"

# Push main and tags
git push origin main
git push origin --tags
```

## 🔒 Branch Protection Rules

### Main Branch Protection
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date
- ✅ Restrict pushes to main branch
- ✅ Include administrators in restrictions

### Develop Branch Protection  
- ✅ Require pull request reviews (optional)
- ✅ Allow force pushes (for rebasing)
- ❌ Less restrictive than main

## 🎯 Recommended Workflow for This Project

### Phase 1: Documentation & Setup (Current)
```bash
# Current branch: feature/documentation-updates
git checkout feature/documentation-updates

# All documentation is complete
# Ready to merge to develop
git checkout develop
git merge feature/documentation-updates
git push origin develop
```

### Phase 2: Feature Development
```bash
# For new strategy development
git checkout develop
git checkout -b feature/new-strategy-xxx

# For bug fixes
git checkout develop  
git checkout -b feature/bug-fixes

# For performance improvements
git checkout develop
git checkout -b feature/performance-optimization
```

### Phase 3: Release Preparation
```bash
# When develop is stable
git checkout main
git merge develop
git tag -a v1.1.0 -m "Release v1.1.0: Strategy improvements and optimizations"
git push origin main --tags
```

## 📝 Commit Message Convention

### Format
```
Type: Brief description (50 chars max)

Detailed explanation of what and why (if needed)
- List specific changes
- Include any breaking changes
- Reference issues if applicable
```

### Types
- **Add**: New features or functionality
- **Fix**: Bug fixes
- **Update**: Improvements to existing features  
- **Remove**: Deleted functionality
- **Refactor**: Code restructuring without functional changes
- **Docs**: Documentation updates
- **Test**: Test additions or modifications
- **Config**: Configuration changes

### Examples
```bash
git commit -m "Add: Triple Threat strategy optimization

- Implement Optuna-based parameter tuning
- Add multi-objective optimization support
- Include walk-forward validation
- Export optimized parameters to MT5/Pine formats"

git commit -m "Fix: Memory leak in CNN-LSTM training pipeline

- Resolve torch tensor accumulation in training loop
- Add proper garbage collection after epochs
- Update documentation with memory requirements"

git commit -m "Update: Risk management calculations

- Improve position sizing accuracy
- Add margin requirement validation  
- Include broker-specific spread handling"
```

## 🔧 Git Aliases (Optional)

Add these to your `~/.gitconfig` for faster workflow:

```ini
[alias]
    co = checkout
    br = branch
    st = status
    cm = commit -m
    ps = push
    pl = pull
    mg = merge --no-ff
    lg = log --oneline --graph --all
    
    # Workflow shortcuts
    feature = "!f() { git checkout develop && git pull && git checkout -b feature/$1; }; f"
    done = "!f() { git checkout develop && git merge --no-ff $1 && git branch -d $1; }; f"
    release = "!f() { git checkout main && git merge develop && git tag -a $1 -m \"Release $1\"; }; f"
```

Usage:
```bash
git feature new-strategy-name    # Creates feature/new-strategy-name from develop
git done feature/new-strategy-name  # Merges and deletes feature branch
git release v1.2.0               # Creates release tag
```

## 🎛️ IDE Integration

### VS Code
Install extensions:
- **GitLens**: Enhanced Git capabilities
- **Git Graph**: Visual branch history
- **Git History**: File history viewer

### PyCharm
Built-in Git integration:
- VCS → Git → Branches (for branch management)
- VCS → Commit (for staging and committing)
- VCS → Git → Push (for pushing changes)

## 🚨 Emergency Hotfix Process

For critical production issues:

```bash
# Create hotfix from main
git checkout main
git checkout -b hotfix/critical-issue-description

# Make minimal fix
# Edit only necessary files

# Commit fix
git commit -m "Hotfix: Critical issue description"

# Merge to main
git checkout main
git merge hotfix/critical-issue-description
git tag -a v1.0.1 -m "Hotfix v1.0.1: Critical issue fix"

# Merge back to develop
git checkout develop
git merge hotfix/critical-issue-description

# Push all changes
git push origin main
git push origin develop
git push origin --tags

# Clean up
git branch -d hotfix/critical-issue-description
```

## 📊 Branch Status Summary

| Branch | Status | Description | Next Action |
|--------|--------|-------------|-------------|
| `main` | ✅ Stable | Production code | Ready for hotfixes |
| `develop` | ✅ Ready | Integration branch | Ready for feature merges |
| `feature/documentation-updates` | 🔄 Active | Documentation work | Ready to merge to develop |

## 🎯 Quick Commands Reference

```bash
# Check current status
git status
git branch -a

# Switch branches  
git checkout develop
git checkout main
git checkout -b feature/new-work

# Sync with remote
git pull origin develop
git push origin feature/branch-name

# Merge workflow
git checkout develop
git merge feature/branch-name
git push origin develop

# Release workflow
git checkout main  
git merge develop
git tag -a v1.0.0 -m "Release message"
git push origin main --tags
```

This workflow ensures clean development, stable releases, and easy collaboration while maintaining code quality and project history.