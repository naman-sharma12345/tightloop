# Todo app (small website)

Build a single-page todo list app. The user can add a task by typing in a text input and pressing Enter
or clicking an Add button; mark a task done or not done with a checkbox (done tasks look visibly
different); delete a task; filter the list by All / Active / Done; see how many tasks are left; and
clear all done tasks with one button. Empty or whitespace-only tasks are not added. The list survives a
page reload (use localStorage). Element ids the checker uses: the text input is `#new-task`, each task is
an `li` inside `#list`, and the remaining-count element is `#left` (its text contains the number).

Files: plain HTML, CSS and JavaScript in the current directory, with `index.html` as the entry
point. No build step, no npm packages, no CDN or other network requests; it must work when served with
`python3 -m http.server`. One screen, and it should look good on a laptop browser window.