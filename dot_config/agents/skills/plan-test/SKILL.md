---
name: plan-test
description: Use to create implemantation plan in form of tests names.
---

This skill is used to embrace TDD/BDD approach. Instead of focusing on implementation details. The goal is to convert requirements and scope into list of tests that will be implemented. Do not attempt to implement any of the established tests. Do not attempt to implement any code.

1. Obtain file where list of tests should be stored.
2. Discover what type of tests are supported by the repository and testing is testing conventions.
3. Convert problem into set of tests. Use below format.

`[N/E](type) test name` where:
`[N]` - new test to be added.
`[E]` - for already existing test that requires to be changed.
`(U)` - unit test.
`(Func)` - functional/integration test.
`(Spec)` - database test.
`(UI)` - fronted component test.
`(Vis)` - visual regression test.
`(E2E)` - end to end test that sett up whole stack.

Do not record any implementation details. No narrative just pure test names.
