# Markdown notes app (small website)

Build a single-page notes app. A sidebar lists notes by title (the first line of the note) with a
"New note" button; the main area has a text editor on one side and a live rendered preview on the other
that updates as the user types. The preview supports headings (#, ##, ###), **bold**, *italic*,
`inline code`, links [text](url), and "- " bullet lists; any HTML typed by the user is shown as text,
never executed. Notes can be deleted, the selected note is highlighted, and notes survive a page reload
(use localStorage). Element ids the checker uses: the editor is a `textarea#editor` and the preview is
`#preview`.

Files: plain HTML, CSS and JavaScript in the current directory, with `index.html` as the entry
point. No build step, no npm packages, no CDN or other network requests; it must work when served with
`python3 -m http.server`. One screen, and it should look good on a laptop browser window.