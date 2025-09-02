# Contributing to Kubernetes A2A Multi-Agent Autoscaling System

We welcome contributions to the Kubernetes A2A Multi-Agent Autoscaling System! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Issues
- Use the GitHub issue tracker to report bugs
- Include detailed information about your environment
- Provide steps to reproduce the issue
- Include relevant logs and error messages

### Suggesting Features
- Open an issue with the "enhancement" label
- Describe the feature and its use case
- Explain how it aligns with the project goals

### Code Contributions
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for all public functions and classes
- Keep functions small and focused

### Testing
- Write unit tests for new functionality
- Ensure integration tests pass
- Test Kubernetes deployments locally
- Verify A2A protocol compliance

### Documentation
- Update documentation for new features
- Include examples in docstrings
- Update the README if needed
- Add architecture diagrams for significant changes

## 🔧 Development Setup

### Prerequisites
- Python 3.8+
- Docker
- Kubernetes cluster (k3s/minikube for local development)
- kubectl configured

### Local Development
```bash
# Clone your fork
git clone https://github.com/your-username/kubernetes-a2a-autoscaling.git
cd kubernetes-a2a-autoscaling

# Set up development environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Running Tests
```bash
# Unit tests
python -m pytest tests/unit/

# Integration tests
python -m pytest tests/integration/

# Kubernetes tests
./scripts/testing/test_integration_complete.py
```

### Building and Testing Locally
```bash
# Build Docker images
./docker/build-scripts/build_all_images.sh

# Deploy to local cluster
kubectl apply -f k8s/agents/
kubectl apply -f k8s/monitoring/
kubectl apply -f k8s/autoscaling/

# Run validation
./scripts/validation/validate_kubernetes_deployment.sh
```

## 🏗️ Project Structure

```
kubernetes-a2a-autoscaling/
├── src/                    # Source code
│   ├── agents/            # A2A agent implementations
│   ├── clients/           # Client libraries
│   ├── common/            # Shared utilities
│   └── testing/           # Testing framework
├── k8s/                   # Kubernetes manifests
│   ├── agents/            # Agent deployments
│   ├── autoscaling/       # HPA configurations
│   └── monitoring/        # Monitoring stack
├── docker/                # Docker configurations
├── scripts/               # Automation scripts
├── docs/                  # Documentation
├── tests/                 # Test suites
└── configs/               # Configuration templates
```

## 🎯 Contribution Areas

### High Priority
- Performance optimizations
- Additional agent implementations
- Enhanced monitoring and alerting
- Security improvements
- Documentation improvements

### Medium Priority
- Additional deployment targets (EKS, GKE, AKS)
- CI/CD pipeline improvements
- Load testing enhancements
- Grafana dashboard improvements

### Low Priority
- Code refactoring
- Additional examples
- Blog posts and tutorials

## 📝 Pull Request Guidelines

### Before Submitting
- [ ] Code follows project style guidelines
- [ ] Tests are written and passing
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive
- [ ] Changes are backwards compatible (or breaking changes are documented)

### Pull Request Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 🔍 Code Review Process

1. **Automated Checks**: All CI checks must pass
2. **Peer Review**: At least one maintainer review required
3. **Testing**: Changes must be tested in a Kubernetes environment
4. **Documentation**: Documentation must be updated for user-facing changes

## 🚀 Release Process

### Versioning
We follow [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking changes
- MINOR: New features (backwards compatible)
- PATCH: Bug fixes (backwards compatible)

### Release Checklist
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in relevant files
- [ ] Docker images tagged and pushed
- [ ] GitHub release created

## 🤔 Questions?

- Open an issue for questions about contributing
- Join our community discussions
- Check existing issues and documentation first

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to the Kubernetes A2A Multi-Agent Autoscaling System! 🎉
