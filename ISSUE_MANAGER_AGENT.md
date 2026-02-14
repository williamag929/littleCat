# Issue Manager Agent

## Overview

The **Issue Manager Agent** is a GitHub Copilot agent specifically designed to help manage, triage, and respond to GitHub issues for the littleCat project.

## Location

`.github/agents/issue-manager.agent.yaml`

## Purpose

This MCP (Model Context Protocol) agent assists with:

1. **Issue Triage** - Quickly assess and categorize incoming issues
2. **Issue Response** - Provide helpful, professional responses to issue reporters
3. **Issue Management** - Track issue lifecycle from open to closed
4. **Project Health Monitoring** - Monitor issue trends and patterns

## Features

### Core Capabilities

- **Automated Triage**: Categorize issues as bugs, features, questions, or documentation
- **Smart Labeling**: Apply appropriate labels based on issue content
- **Response Templates**: Pre-configured responses for common scenarios
- **Priority Assessment**: Determine severity (critical, high, medium, low)
- **Duplicate Detection**: Identify and link duplicate issues
- **Status Tracking**: Monitor and update issue progress

### Available Tools

The agent has access to:
- `github_issues_read` - Read and search existing issues
- `github_issues_write` - Create, update, and close issues
- `github_search` - Search across the repository
- `code_analysis` - Analyze code related to issues

## Usage

### How to Invoke

In GitHub Copilot, you can invoke this agent to help with issue management tasks:

```
@issue-manager Help me triage the recent bug reports
@issue-manager Respond to issue #123 about the save/load problem
@issue-manager Find all open performance-related issues
```

### Common Use Cases

#### 1. Triaging New Issues
```
@issue-manager Please triage issue #45
```

The agent will:
- Read the issue content
- Categorize it (bug/feature/question)
- Suggest appropriate labels
- Assess priority level
- Recommend next steps

#### 2. Responding to Bug Reports
```
@issue-manager Draft a response to issue #67 asking for more details
```

The agent will:
- Review the existing bug report
- Identify missing information
- Generate a friendly response template
- Request necessary reproduction steps

#### 3. Managing Feature Requests
```
@issue-manager Evaluate the feature request in issue #89
```

The agent will:
- Assess alignment with project goals
- Consider complexity vs value
- Provide feedback on feasibility
- Suggest implementation approach

#### 4. Closing Resolved Issues
```
@issue-manager Help me close resolved issues from the last release
```

The agent will:
- Identify resolved issues
- Draft closure messages
- Link to relevant commits/PRs
- Update issue status

## Issue Categories

### Bug Reports
**Labels**: `bug`, `critical`, `high-priority`, `low-priority`

Required information:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python version, OS)
- Error messages or stack traces

### Feature Requests
**Labels**: `enhancement`, `feature-request`, `ui-improvement`, `ai-enhancement`

Considerations:
- Alignment with project goals
- Implementation complexity
- Educational value
- Impact on existing features

### Questions & Support
**Labels**: `question`, `documentation`, `help-wanted`

Response approach:
- Point to relevant documentation
- Provide clear guidance
- Offer code examples
- Suggest related features

### Documentation Issues
**Labels**: `documentation`, `good-first-issue`

Common issues:
- Missing documentation
- Unclear instructions
- Outdated information
- Typos or formatting

## Response Templates

The agent has built-in templates for:

- **Bug Report Response** - Requesting reproduction steps
- **Feature Request Response** - Acknowledging and gathering requirements
- **Question Response** - Providing helpful answers with links
- **Duplicate Issue** - Linking to existing issues
- **Resolved Issue** - Confirming fix and closure

## Project-Specific Knowledge

The agent understands the littleCat project structure:

### Key Components
- `src/cat_brain.py` - Core AI learning system
- `src/game.py` - Main game loop and UI
- `src/config.py` - Centralized configuration
- `src/screen_agent_poc.py` - Screen agent implementation

### Common Issues
- Installation problems (dependencies, Python version)
- Game behavior (cat not learning, save/load issues)
- Performance issues (FPS adjustments needed)
- Feature confusion (AI mechanics, stat system)

### Documentation References
- `README.md` - Main project overview
- `AGENT_GUIDE.md` - Complete agent documentation
- `DEVELOPER_GUIDE.md` - Development best practices
- `INSTALL.md` - Installation instructions

## Best Practices

### Communication Style
- **Friendly**: Use emojis and welcoming language
- **Clear**: Avoid jargon, explain concepts simply
- **Helpful**: Provide actionable next steps
- **Professional**: Maintain project standards

### Triage Workflow
1. **Assess** - Understand the issue (within 24 hours)
2. **Categorize** - Add appropriate labels
3. **Prioritize** - Determine urgency level
4. **Respond** - Acknowledge and guide next steps
5. **Track** - Monitor progress until closure

### Quality Standards
- Verify issues have sufficient detail
- Check for duplicates before creating new issues
- Keep issue scope focused (one problem per issue)
- Link related issues and PRs
- Update status as situations evolve

## Integration

### With GitHub Workflows
The agent works alongside:
- Issue templates (if configured)
- Automated labeling systems
- Project boards
- Milestone tracking

### With Other Agents
Complements:
- **Refactor Agent** - Code quality improvements from issue feedback
- **Reviewer Agent** - Security/performance concerns raised in issues

## Metrics to Track

- **Response Time** - First response within 24-48 hours
- **Resolution Time** - Fixes within 1-2 weeks for high-priority
- **Open Issue Count** - Maintain manageable backlog
- **Contributor Satisfaction** - Positive interactions

## Examples

### Example 1: Triaging a Bug Report

**Issue**: "Game crashes when loading saved cat"

**Agent Response**:
```markdown
Thanks for reporting this! 🐛

To help us investigate, could you please provide:
- [ ] Python version and operating system
- [ ] Steps to reproduce the crash
- [ ] Any error messages or stack traces
- [ ] The cat_brain.json file (if you're comfortable sharing)

This will help us identify and fix the problem faster!
```

**Labels Applied**: `bug`, `high-priority`, `needs-info`

### Example 2: Evaluating a Feature Request

**Issue**: "Add multiplayer mode where cats can interact"

**Agent Assessment**:
```markdown
Thanks for the suggestion! 💡

This is an interesting idea that aligns with the future enhancements listed in 
the README (multiple cats that interact with each other).

Questions to consider:
- How would cats communicate/interact?
- Would it be local multiplayer or networked?
- What would be the educational value for learning AI concepts?

This is a significant feature that would require substantial architectural 
changes. We'll mark it as a future enhancement and consider it for a future 
release. Contributions welcome!
```

**Labels Applied**: `enhancement`, `future`, `good-first-issue`

### Example 3: Answering a Question

**Issue**: "How do I make my cat learn faster?"

**Agent Response**:
```markdown
Great question! 🤔

The cat's learning speed is controlled by the learning rate in `src/cat_brain.py`. 
You can adjust it by modifying:

```python
self.learned_behaviors[action] += reward * 0.1  # Increase 0.1 for faster learning
```

However, keep in mind:
- The game is designed to show gradual learning (realistic AI simulation)
- Faster learning may make the cat less "natural" feeling
- Typical learning curve is 4-7 days for pattern recognition

For more details, check out:
- [README.md - Learning System](README.md#learning-system)
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

Feel free to ask if you need more help!
```

**Labels Applied**: `question`, `documentation`

## Troubleshooting

### If the agent isn't working:
1. Verify the YAML syntax is valid
2. Check that the file is in `.github/agents/`
3. Ensure GitHub Copilot has access to agent files
4. Restart your IDE/editor

### If responses aren't helpful:
1. Provide more context in your request
2. Reference specific issue numbers
3. Be explicit about what you need
4. Try rephrasing your question

## Contributing

To improve this agent:
1. Update the `systemPrompt` in `issue-manager.agent.yaml`
2. Add new response templates
3. Expand the project-specific knowledge
4. Test with real issues
5. Submit a PR with improvements

## License

This agent configuration is part of the littleCat project and follows the same license.

---

**Need help?** Open an issue or ask in discussions!
