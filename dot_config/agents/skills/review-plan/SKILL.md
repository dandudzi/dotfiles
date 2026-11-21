---
name: review-plan
description: Review an implementation plan when the user asks for a plan review.
---

When reviewing implementation plan always check the content

- Guard single responsibility rule.
- Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line.
- Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does.
- Standard library or a platform feature? Use it, unless the project has its own. A house component beats a native widget.
- An installed dependency? Use it. Never add a dependency for a few lines.
- If repository use DDD map all requirements to DDD patterns.
- Comment only the why the code cannot show, in one line.
- Bug fix: before you edit, grep every caller of the function you touch, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
