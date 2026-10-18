package main

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func post(t *testing.T, srv *httptest.Server, body string) (int, map[string]string) {
	t.Helper()
	r, err := http.Post(srv.URL+"/shorten", "application/json", bytes.NewBufferString(body))
	if err != nil {
		t.Fatal(err)
	}
	defer r.Body.Close()
	var m map[string]string
	json.NewDecoder(r.Body).Decode(&m)
	return r.StatusCode, m
}

func TestShortenAndRedirect(t *testing.T) {
	srv := httptest.NewServer(newMux())
	defer srv.Close()

	code, m := post(t, srv, `{"url":"https://example.com/a"}`)
	if code != 201 || m["code"] != "1" {
		t.Fatalf("first shorten: got %d %v", code, m)
	}
	_, m2 := post(t, srv, `{"url":"https://example.com/b"}`)
	if m2["code"] != "2" {
		t.Fatalf("second shorten: got %v", m2)
	}

	c := &http.Client{CheckRedirect: func(*http.Request, []*http.Request) error {
		return http.ErrUseLastResponse
	}}
	r, err := c.Get(srv.URL + "/1")
	if err != nil {
		t.Fatal(err)
	}
	r.Body.Close()
	if r.StatusCode != 302 || r.Header.Get("Location") != "https://example.com/a" {
		t.Fatalf("redirect: got %d %q", r.StatusCode, r.Header.Get("Location"))
	}

	r2, _ := c.Get(srv.URL + "/zzz")
	r2.Body.Close()
	if r2.StatusCode != 404 {
		t.Fatalf("unknown code: got %d", r2.StatusCode)
	}

	bad, _ := post(t, srv, `{}`)
	if bad != 400 {
		t.Fatalf("empty url: got %d", bad)
	}
}
