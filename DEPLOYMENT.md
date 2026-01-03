# PyPI Deployment Guide

This repository includes a GitHub Actions workflow for automatically publishing the `charsetrs` package to PyPI.

## Overview

The deployment workflow builds wheels for multiple platforms and architectures:

- **Linux**: x86_64, aarch64 (ARM64)
- **macOS**: x86_64 (Intel), aarch64 (Apple Silicon M1/M2/M3/M4)
- **Windows**: x64, x86, aarch64 (ARM64)

The workflow uses PyO3's maturin-action for building Rust-based Python packages and OIDC for secure authentication with PyPI.

## Setup Instructions

### 1. Configure PyPI Trusted Publishing (OIDC)

PyPI supports Trusted Publishing, which eliminates the need for manually managing API tokens. Instead, it uses OpenID Connect (OIDC) to authenticate GitHub Actions workflows.

#### Steps to enable Trusted Publishing:

1. Go to your PyPI account: https://pypi.org/manage/account/publishing/
2. Scroll to "Pending publishers" or "Add a new pending publisher"
3. Fill in the following details:
   - **PyPI Project Name**: `charsetrs`
   - **Owner**: `mariotaddeucci` (your GitHub username or organization)
   - **Repository name**: `charsetrs`
   - **Workflow name**: `deploy.yml`
   - **Environment name**: `pypi`

4. Click "Add"

**Note**: You can configure a pending publisher before the package exists on PyPI. The first successful workflow run will create the package.

### 2. Create a PyPI Environment in GitHub

1. Go to your repository on GitHub: https://github.com/mariotaddeucci/charsetrs
2. Navigate to **Settings** → **Environments**
3. Click **New environment**
4. Name it `pypi` (must match the environment name in the workflow)
5. Optionally, add deployment protection rules:
   - Required reviewers (recommended for production releases)
   - Wait timer
   - Deployment branches (e.g., only tags matching `v*`)

## Triggering a Deployment

The workflow is triggered in two ways:

### 1. Automatic deployment on version tags

When you push a tag starting with `v`, the workflow automatically runs:

```bash
# Create and push a version tag
git tag v0.1.0
git push origin v0.1.0
```

### 2. Manual deployment

You can manually trigger the workflow from GitHub:

1. Go to the **Actions** tab in your repository
2. Select the "Deploy to PyPI" workflow
3. Click **Run workflow**
4. Select the branch or tag to deploy
5. Click **Run workflow**

## Workflow Details

### Build Jobs

The workflow consists of four parallel build jobs:

1. **Linux builds** (`linux`): Builds wheels for x86_64 and aarch64 using manylinux containers
2. **Windows builds** (`windows`): Builds wheels for x64, x86, and aarch64
3. **macOS builds** (`macos`): Builds wheels for x86_64 (Intel) and aarch64 (Apple Silicon)
4. **Source distribution** (`sdist`): Creates a source distribution (.tar.gz)

Each job:
- Uses PyO3's maturin-action for efficient Rust compilation
- Enables sccache for faster builds
- Builds release-optimized wheels
- Uploads artifacts for the publish job

### Publish Job

After all builds complete successfully:

1. Downloads all wheel artifacts and the source distribution
2. Uses maturin to upload to PyPI via OIDC authentication
3. Uses `--skip-existing` to avoid errors if a version is already published

## Version Management

Update the version in `pyproject.toml` before creating a release:

```toml
[project]
name = "charsetrs"
version = "0.1.0"  # Update this
```

Also update the version in `Cargo.toml` to keep them in sync:

```toml
[package]
name = "charsetrs"
version = "0.1.0"  # Update this
```

## Testing Before Release

Before creating a release tag, ensure all tests pass:

```bash
# Run the full test suite
uv run task test

# Run linting
uv run task lint

# Build locally to verify
uv run maturin build --release
```

## Troubleshooting

### Build Failures

If a build fails:
1. Check the Actions tab for detailed logs
2. Verify Rust dependencies compile on the target platform
3. Test locally using the same maturin command

### Publishing Failures

If publishing fails:
1. Verify OIDC configuration on PyPI matches the workflow
2. Check that the `pypi` environment exists in GitHub
3. Ensure the version doesn't already exist on PyPI

### Platform-Specific Issues

- **Linux ARM64**: Uses QEMU emulation; builds may be slower
- **Windows ARM64**: Uses cross-compilation with maturin
- **macOS Universal2**: Currently builds separate x86_64 and aarch64 wheels

## Security

This workflow uses OIDC/Trusted Publishing instead of API tokens, providing:
- No long-lived credentials to manage or rotate
- Automatic token generation per workflow run
- Tokens are scoped to specific repositories and workflows
- Reduced risk of credential leakage

The workflow only has the following permissions:
- `contents: read` - To check out the repository
- `id-token: write` - To generate OIDC tokens for PyPI authentication

## References

- [PyPI Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [PyO3 maturin-action](https://github.com/PyO3/maturin-action)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
