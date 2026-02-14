# GitHub Copilot Agents

This directory contains GitHub Copilot agent configurations for the littleCat project.

## Available Agents

### 1. Issue Manager Agent
**File**: `issue-manager.agent.yaml`  
**Purpose**: GitHub Issues specialist for managing, triaging, and responding to project issues

**Key Capabilities**:
- Issue triage and categorization
- Automated responses to bug reports, feature requests, and questions
- Label management and priority assessment
- Project health monitoring
- Duplicate issue detection

**Usage**:
```
@issue-manager Help me triage issue #123
@issue-manager Respond to the bug report in issue #45
@issue-manager Find all open performance-related issues
```

**Documentation**: See [ISSUE_MANAGER_AGENT.md](../../ISSUE_MANAGER_AGENT.md) for complete guide.

---

### 2. Refactor Agent
**File**: `refactor.agent.yaml`  
**Purpose**: Senior code health specialist focused on maintaining project standards and code quality

**Key Capabilities**:
- Code quality assessment
- Standards enforcement (PEP 8, project conventions)
- Refactoring guidance
- Technical debt management
- Code review and improvement suggestions

**Usage**:
```
@refactor-agent Review this code for quality improvements
@refactor-agent Suggest refactoring for the cat_brain.py file
@refactor-agent Check if this code follows project standards
```

---

### 3. Reviewer Agent
**File**: `reviewer.agent.yaml`  
**Purpose**: Senior Security & Performance Reviewer

**Key Capabilities**:
- Security audit (OWASP Top 10, vulnerabilities)
- Logic validation and edge case detection
- Performance impact analysis
- Test coverage verification
- Risk assessment

**Usage**:
```
@reviewer Audit this code for security vulnerabilities
@reviewer Check for performance issues in this implementation
@reviewer Validate the logic in this function
```

---

## How to Use Agents

### In GitHub Copilot Chat

1. Open GitHub Copilot Chat in your IDE
2. Mention the agent using `@agent-name`
3. Provide your request or question
4. The agent will respond with specialized knowledge

### Example Workflows

**Managing Issues**:
```
@issue-manager Triage all open bugs from the last week
@issue-manager Draft a response to issue #56 about installation problems
```

**Code Review**:
```
@reviewer Review this pull request for security issues
@refactor-agent Suggest improvements for better code quality
```

**Development**:
```
@refactor-agent How can I improve the modularity of this code?
@reviewer Does this code have any performance bottlenecks?
```

---

## Agent Configuration Format

All agents follow this YAML structure:

```yaml
name: Agent Name
description: Brief description of the agent's purpose

systemPrompt: |
  Detailed system prompt that defines:
  - Agent's role and responsibilities
  - Project-specific knowledge
  - Response style and guidelines
  - Best practices to follow

tools:
  - tool_name_1
  - tool_name_2
```

---

## Adding New Agents

To add a new agent:

1. Create a new `.agent.yaml` file in this directory
2. Follow the structure of existing agents
3. Define the agent's:
   - Name and description
   - System prompt with role, responsibilities, and knowledge
   - Available tools (if needed)
4. Document the agent in this README
5. Create a detailed guide if the agent is complex

---

## Project Context

All agents have knowledge of the littleCat project:

**Technology Stack**:
- Python 3.8+
- Pygame for game engine
- Custom reinforcement learning AI
- OpenCV for computer vision

**Key Components**:
- `src/cat_brain.py` - AI learning system
- `src/game.py` - Game loop and UI
- `src/config.py` - Configuration
- `src/screen_agent_poc.py` - Screen agent

**Documentation**:
- See root directory for complete documentation
- [INDEX.md](../../INDEX.md) provides a full documentation map

---

## Best Practices

**When Using Agents**:
- Be specific in your requests
- Provide context and examples
- Reference specific files or issues
- Ask follow-up questions for clarification

**When Creating Agents**:
- Define a clear, focused role
- Include project-specific knowledge
- Provide example interactions
- Document capabilities thoroughly
- Keep system prompts well-organized

---

## Learn More

- **GitHub Copilot Documentation**: https://docs.github.com/copilot
- **Model Context Protocol (MCP)**: https://modelcontextprotocol.io
- **Project Documentation**: See [INDEX.md](../../INDEX.md)

---

## Feedback

Have suggestions for improving existing agents or ideas for new ones?  
Open an issue or submit a pull request!

---

**Last Updated**: February 2026  
**Maintained By**: littleCat Project Team
