# tightloop v5 blind run: integrity record

Status: PREP ONLY. No v5 build, no v5 key and no v5 session exists at the commit that adds this file.
Design and criteria: benchmark/design/tightloop-v5/DESIGN.md (base eace66f, A1 0be26dc, A2 70b7958). Nothing here
changes a criterion, a prediction or a rule in that file.

## 1. App specs (committed before any v5 key exists)

Three new apps, none of round 1 or round 2 (todo, notes, units, kanban, expenses, bookmarks):

| app | file | bytes | sha256 |
|---|---|---|---|
| habit tracker | benchmark/blind/specs/v5/habits.md | 3321 | 116b0fbedf29400a93b7de739f8f9422eaa851608d4eef47a84b9e111d7629fb |
| recipe box | benchmark/blind/specs/v5/recipes.md | 3490 | 235b01522418f1a938e24e4dff868b45818f789d6e8f5781dc76c0c264fb68e1 |
| pomodoro timer | benchmark/blind/specs/v5/pomodoro.md | 3403 | 04b99b2a8efe35b7ece9b6e935662d95eec566138bb82fcecbfe9cd7cc0c3e05 |

Who wrote them: a separate helper worker that was told not to open, list or grep benchmark/arms/tightloop-v5/,
benchmark/arms/tightloop-v5b/, benchmark/design/ or .claude/skills/, and wrote from the round-2 spec shape only
(the helper's own statement: "no v5/v5b/design/.claude files opened"). One edit after the helper handed them over,
by the prep worker: a stray ",." in pomodoro.md ("requestAnimationFrame alone,.") became "alone." (helper's sha was
6b13d19b4d1bf210291eca2fca2f69e2bccf7b583d3dd6a60328e23a2a6f8a41; the table above is the committed file).
The specs are frozen from this commit on.
