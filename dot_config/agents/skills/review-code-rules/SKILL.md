---
name: review-code-rules
description: Review code against the repository's coding rules when the user requests a rules review.
---

Goal of review:
  1. Standards: does the code conform to this repo's documented coding standards?
  2. Does the code faithfully implement the originating plan?

When reviewing the code use those rules:

- Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line.
- Guard single responsibility rule.
- Already in this codebase (a helper, component, service, pattern)? Use it the way the surrounding code does.
- Does it follow existing patterns or introduce a new one? If new, is it justified? 
- Standard library or a platform feature? Use it, unless the project has its own. A house component beats a native widget.
- An installed dependency? Use it. Never add a dependency for a few lines.
- If repository use DDD map all requirements to DDD patterns.
- Comment only the why the code cannot show, in one line.
- Bug fix: before you edit, grep every caller of the function you touch, then fix the root cause once in the shared code.
- Code you move or merge keeps its error handling and validation.
- Duplicated Code: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- Data Clumps: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- Primitive Obsession: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.

Look for Lean:

- code that should not exist or should be smaller.
- delete: dead code, unused options, speculative features
