# PyPI Deployment Guide

This repository includes a unified CI/CD GitHub Actions workflow that handles testing and deployment to PyPI.

## Overview

The unified pipeline performs the following stages:

1. **Lint**: Code quality checks (runs first)
2. **Test**: Parallel testing across all supported platforms grouped by OS
   - Linux: Python 3.10, 3.11, 3.12, 3.13
   - macOS: Python 3.10, 3.11, 3.12, 3.13
   - Windows: Python 3.10, 3.11, 3.12, 3.13
3. **Build**: Wheel compilation for multiple platforms and architectures (only after tests pass)
   - Linux: x86_64, aarch64 (ARM64)
   - macOS: x86_64 (Intel), aarch64 (Apple Silicon)
   - Windows: x64, x86, aarch64 (ARM64)
4. **Publish**: Deploy to PyPI (only when triggered by v* tags)

The workflow uses PyO3's maturin-action for building Rust-based Python packages and OIDC for secure authentication with PyPI.

## Workflow Behavior

- **On Pull Requests**: Runs lint, tests, and builds wheels (no deployment)
- **On Push to main**: Runs lint, tests, and builds wheels (no deployment)
- **On Version Tags (v*)**: Runs lint, tests, builds wheels, AND deploys to PyPI
- **Manual Trigger**: Can be triggered manually with optional deployment

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

The unified workflow runs on every push and pull request, but deployment only happens on version tags.

### Creating a Release

When you push a tag starting with `v`, the workflow automatically runs all stages including deployment:

```bash
# Update version in both files
# Edit pyproject.toml: version = "0.1.0"
# Edit Cargo.toml: version = "0.1.0"

# Create and push a version tag
git add pyproject.toml Cargo.toml
git commit -m "Bump version to 0.1.0"
git push origin main
git tag v0.1.0
git push origin v0.1.0
```

The workflow will:
1. ✅ Run linter
2. ✅ Run tests on Linux, macOS, and Windows
3. ✅ Build wheels for all platforms
4. ✅ **Deploy to PyPI** (only happens with v* tags)

### Testing Without Deployment

Push to main branch or create a pull request:

```bash
git push origin main
```

The workflow will:
1. ✅ Run linter
2. ✅ Run tests on Linux, macOS, and Windows
3. ✅ Build wheels for all platforms
4. ⏭️  Skip deployment (no tag present)

## Workflow Details

### Stage 1: Lint

Runs code quality checks using:
- Python linting (ruff)
- Rust formatting (cargo fmt)
- Type checking (pyrefly)

### Stage 2: Test (Parallel by OS)

Three parallel job groups run tests:
- **test-linux**: Tests on Ubuntu with Python 3.10-3.13
- **test-windows**: Tests on Windows with Python 3.10-3.13
- **test-macos**: Tests on macOS with Python 3.10-3.13

All tests must pass before proceeding to the build stage.

### Stage 3: Build (Parallel by OS)

After tests pass, wheels are built in parallel:
- **build-linux**: x86_64, aarch64 (uses manylinux)
- **build-windows**: x64, x86, aarch64
- **build-macos**: x86_64, aarch64
- **build-sdist**: Source distribution

Each job:
- Uses PyO3's maturin-action for Rust compilation
- Enables sccache for faster builds
- Builds release-optimized wheels
- Uploads artifacts

### Stage 4: Publish (Conditional)

Runs only when:
- All builds complete successfully
- Triggered by a tag matching `v*`

The publish job:
1. Downloads all wheel artifacts and sdist
2. Uses maturin to upload to PyPI via OIDC
3. Uses `--skip-existing` to avoid errors on republish

## Version Management

Update the version in both files before creating a release:

**pyproject.toml:**
```toml
[project]
name = "charsetrs"
version = "0.1.0"  # Update this
```

**Cargo.toml:**
```toml
[package]
name = "charsetrs"
version = "0.1.0"  # Update this
```

## Testing Before Release

Before creating a release tag:

```bash
# Run the full test suite locally
uv run task test

# Run linting
uv run task lint

# Build locally to verify
uv run maturin build --release
```

Or push to a branch and let the CI/CD pipeline validate everything:

```bash
git push origin feature-branch
```

The workflow will run lint, tests, and builds without deploying.

## Troubleshooting

### Build Failures

If a build fails:
1. Check the Actions tab for detailed logs
2. Verify Rust dependencies compile on the target platform
3. Test locally using the same maturin command
4. Ensure all tests pass before builds run

### Test Failures

If tests fail:
1. The build and deploy stages are skipped automatically
2. Fix the failing tests
3. Push changes to trigger the workflow again

### Publishing Failures

If publishing fails:
1. Verify OIDC configuration on PyPI matches the workflow
2. Check that the `pypi` environment exists in GitHub
3. Ensure the version doesn't already exist on PyPI
4. Confirm all builds completed successfully

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
