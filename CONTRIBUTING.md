# Contributing to AstraSync Python SDK

We love your input! We want to make contributing to the AstraSync Python SDK as easy and transparent as possible.

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code follows the existing style.
6. Issue that pull request!

## Setting Up Development Environment

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/astrasync-python-sdk.git
cd astrasync-python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install package in development mode
pip install -e .
```

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=astrasync

# Run specific test file
python tests/integration/test_langchain_integration.py
```

## Code Style

We use [Black](https://black.readthedocs.io/) for code formatting:

```bash
# Format all Python files
black .

# Check formatting without making changes
black --check .
```

## Adding New Agent Framework Support

To add support for a new AI agent framework:

1. Create a new adapter in `astrasync/adapters/framework_name.py`
2. Implement the `normalize_agent_data()` function
3. Add framework detection to `astrasync/utils/detector.py`
4. Create tests in `tests/integration/test_framework_name_integration.py`
5. Add an example in `examples/framework_name_example.py`
6. Update the README with the new framework

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the version number in `setup.py` and README.md following [SemVer](http://semver.org/)
3. The PR will be merged once you have the sign-off of at least one maintainer

## Any contributions you make will be under the MIT Software License

When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE.txt) that covers the project.

## Report bugs using GitHub's [issue tracker](https://github.com/AstraSyncAI/astrasync-python-sdk/issues)

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/AstraSyncAI/astrasync-python-sdk/issues/new).

## License

By contributing, you agree that your contributions will be licensed under its MIT License.