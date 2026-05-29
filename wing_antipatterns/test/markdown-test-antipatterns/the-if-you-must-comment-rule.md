## The "if you must" comment rule

Any test that asserts a specific string literal or a length bound on a Markdown file
**must** carry a comment that answers three questions:

1. **Why does this constraint exist?** Name the downstream system, runtime behaviour, or
   quality concern it guards.
2. **Is this a hard boundary or a heuristic?** Hard: the system breaks above the limit.
   Heuristic: it was a reasonable default when written.
3. **What should happen if it fires?** Fix the content, raise the threshold, or delete
   the test — whichever is correct depends on context the comment must supply.

An agent reading a failing test with this comment can make an informed decision. An agent
reading a failing test without it will either contort output to pass or raise the threshold
blindly — both outcomes degrade the codebase.
