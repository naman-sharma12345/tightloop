# app-03: shorty (Go, stdlib only)

Build a tiny URL shortener HTTP service in Go (module `shorty`, package
`main`, Go standard library only).

Requirements:
- The package must expose `func newMux() *http.ServeMux` so tests can mount
  it with httptest.
- `POST /shorten` with JSON body `{"url":"https://example.com/x"}` stores
  the URL and replies `201 Created` with JSON `{"code":"1"}`. Codes are
  sequential decimal strings starting at "1" ("1", "2", "3", ...).
- `GET /{code}` replies `302 Found` with a `Location` header set to the
  stored URL.
- `GET` for an unknown code replies `404 Not Found`.
- `POST /shorten` with a missing or empty `url` field replies
  `400 Bad Request`.
- `func main()` should serve the mux on :8080 with `http.ListenAndServe`,
  but tests only use `newMux()`.

The store may be in memory. Only the Go standard library may be used.
