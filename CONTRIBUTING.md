# Contributing to Braille STL Generator (OpenSCAD)

Thank you for your interest in contributing to the Braille STL Generator! This document provides guidelines and instructions for contributing to the OpenSCAD version of the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR-USERNAME/braille-cylinder-stl-generator-openscad.git
   cd braille-cylinder-stl-generator-openscad
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/BrennenJohnston/braille-cylinder-stl-generator-openscad.git
   ```

## Development Setup

### Prerequisites

- OpenSCAD 2026.01.03+ with Manifold backend (recommended for faster rendering)
- Git
- Python 3.9+ (for running automated tests)

### Testing Your Changes

#### Manual Testing

1. Open the `.scad` file in OpenSCAD
2. Use the Customizer panel (View → Customizer) to adjust parameters
3. Press F5 for preview, F6 for full render
4. Test with various configurations:
   - Cylinder shape (card support permanently removed)
   - Positive (emboss) vs Negative (counter) plates
   - Rounded vs Cone dot shapes
   - With and without indicator shapes

#### Automated Testing

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Run validation tests
pytest tests/cross_platform_validation.py -v

# Run specific test
pytest tests/cross_platform_validation.py -k cylinder_rounded_emboss_indicators_on
```

See `tests/README.md` for comprehensive testing documentation.

## Making Changes

### Branch Naming

Use descriptive branch names:
- `feature/add-new-dot-shape`
- `fix/cylinder-positioning-error`
- `docs/update-parameter-mapping`

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `refactor`: Code refactoring
- `chore`: Maintenance tasks

**Examples:**
```
feat(geometry): add hexagonal dot shape option

fix(cylinder): correct dot positioning on curved surface

docs(readme): update parameter descriptions
```

## Pull Request Process

1. **Update your fork** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes** and test thoroughly in OpenSCAD

4. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request** on GitHub

### PR Requirements

- [ ] Changes tested in OpenSCAD (both preview and render)
- [ ] Documentation updated (if applicable)
- [ ] Commit messages follow conventions
- [ ] PR description explains the changes
- [ ] Default values remain consistent with web app (if applicable)

## Coding Standards

### OpenSCAD

- **Modules**: Use descriptive module names with underscore separation
- **Parameters**: Document parameters with comments in Customizer format
- **Constants**: Use ALL_CAPS for constants
- **Comments**: Document complex geometry logic
- **Indentation**: Use consistent 4-space indentation

### Parameter Documentation

When adding new parameters, follow this format:
```openscad
/* [Section Name] */
// Parameter description (unit)
parameter_name = default_value; // [min:step:max] or [option1, option2]
```

## Documentation

### When to Update Documentation

- Adding new parameters
- Changing default values
- Modifying geometry calculations
- Fixing bugs that affect documented behavior

### Documentation Files

- `README.md` — Project overview and quick start
- `docs/PARAMETER_MAPPING.md` — Maps parameters to web app UI controls
- `OPENSCAD_COORDINATE_SYSTEM_SPECIFICATIONS.md` — Technical coordinate system details

## Related Projects

- **Web App**: [braille-card-and-cylinder-stl-gener.vercel.app](https://braille-card-and-cylinder-stl-gener.vercel.app)
- **Web App Source**: [github.com/BrennenJohnston/braille-cylinder-stl-generator](https://github.com/BrennenJohnston/braille-cylinder-stl-generator)

## Questions?

If you have questions or need help:

1. Check existing documentation
2. Search existing issues
3. Open a new issue with the `question` label

Thank you for contributing! 🙏
