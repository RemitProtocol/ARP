# Contributing to the Agent Remittance Protocol (ARP)

First off, thank you for considering contributing to the Agent Remittance Protocol! We are building the premier consent-enforced execution layer for AI agents routing cross-border payments, and your contributions are essential to our success.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. We expect all contributors to maintain a professional, respectful, and inclusive environment. Harassment, discrimination, or abusive behavior will not be tolerated and may result in a permanent ban from the project.

## Development Workflow

We follow a strict, production-grade workflow aligned with top-tier Web3 foundations. Please adhere to the following steps when contributing:

### 1. Branching Strategy
- Always create a new branch for your work from the `main` branch.
- Use descriptive and structured branch names: 
  - `feature/your-feature-name`
  - `fix/issue-description`
  - `docs/update-readme`

### 2. Conventional Commits
All commit messages must follow the [Conventional Commits](https://www.conventionalcommits.org/) specification. This ensures automated and accurate changelog generation.

Examples:
- `feat: add IntaSend payment rail integration`
- `fix: resolve execution lock race condition in FSM`
- `docs: update Circle API configuration instructions`
- `test: add unit tests for Tier-3 policy evaluation`

### 3. Opening a Pull Request (PR)
- Ensure your PR description clearly outlines the problem solved or the feature added.
- Link any relevant GitHub issues using keywords (e.g., `Closes #42`).
- Keep PRs focused and atomic. If you are solving multiple separate issues, please open separate PRs for each.

## Testing & Quality Requirements

To maintain our stringent Web3 security posture and zero-defect execution layer, all code merged into the repository must pass our rigorous quality checks. **Pull Requests modifying `src/arp/` will not be reviewed if they fail these checks.**

1. **Unit Tests:** Any new feature or bug fix must include corresponding unit tests using `pytest`. The tests should validate both expected behavior and edge-case invariants.
2. **Linting and Formatting:** We enforce strict Python code style.
   - Run `black src/` to automatically format your code.
   - Run `flake8 src/` to ensure no syntax errors or styling violations exist.
3. **Type Hinting:** All new code must be fully type-hinted and pass static analysis.

Once you open a PR, our automated CI pipeline will run these checks. Please ensure they pass locally before requesting a review from the core maintainers.
