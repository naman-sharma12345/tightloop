# Pipeline check fixtures (not benchmark results)

These rows come from a pipeline check: the runner launched a stub solver
(tests/stub-claude) that applies the task's reference fix (pass mode) or
does nothing (fail mode). They exist as regression fixtures for
benchmark/runner.py: after any runner change, re-running the pipeline check
must still produce correct pass rows and fail rows with the same schema.

They are not benchmark numbers. No model was involved; every token field is
"unmeasured" because the stub reports nothing.

Skill prompt size context (char-based estimate, not tokenizer output):
tightloop SKILL.md is 12053 chars (~3013 tokens
estimated at 4 chars/token); the average first-5 task instruction is
64 chars (~16 tokens estimated). The skill is
the marginal prompt cost of the tightloop arm over the no-skill arm.
Char-based counts are estimates; real token counts come from the agent CLI
during a real run.
