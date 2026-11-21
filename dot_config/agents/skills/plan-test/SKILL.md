---
name: plan-test
description: Use to create implemantation plan in form of tests names.
---

This skill is used to embrace TDD/BDD approach. Instead of focusing on implementation details. The goal is to convert requirements and scope into list of tests that will be implemented. Do not attempt to implement any of the established tests. Do not attempt to implement any code.

1. Obtain file where list of tests should be stored.
2. Discover what type of tests are supported by the repository and what is testing conventions.
3. Convert problem into set of tests. Use below format. Use numbered list. Keep `[]()` brackets from down below format. All parts are required. Test name should not use Camel Cases or other just plain sentence string.
4. Group test by class names.

`1. [N/E](type) test name - <optional-description>` where:
`[N]` - new test to be added.
`[E]` - for already existing test that requires to be changed.
`(Unit)` - unit test.
`(Func)` - functional/integration test.
`(Spec)` - database test.
`(UI)` - fronted component test.
`(Vis)` - visual regression test.
`(E2E)` - end to end test that set up whole stack.
`(User)` - user journey that emulating real user actions of fronted.
`<optional-description>` - Use only with `[E]` describing in one sentence what will change in test.

Do not record any implementation details. No narrative just pure test names.
