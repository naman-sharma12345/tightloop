# Unit converter (small website)

Build a single-page unit converter. The user picks a category (Length, Weight, Temperature), a "from"
unit and a "to" unit, types a number, and sees the converted value update live as they type. Length
covers mm, cm, m, km, in, ft, mi; Weight covers g, kg, oz, lb; Temperature covers C, F, K. A swap
button exchanges the from and to units. Results are shown to at most 4 decimal places with no trailing
zeros. Invalid or empty input shows a clear message instead of a number. Element ids the checker uses:
`select#category`, `select#from`, `select#to`, `input#value`, and `#result` (its text contains the
converted number); option values are the unit symbols listed above.

Files: plain HTML, CSS and JavaScript in the current directory, with `index.html` as the entry
point. No build step, no npm packages, no CDN or other network requests; it must work when served with
`python3 -m http.server`. One screen, and it should look good on a laptop browser window.