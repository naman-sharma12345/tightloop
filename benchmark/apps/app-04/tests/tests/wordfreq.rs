use std::io::Write;
use std::process::{Command, Stdio};

fn run(args: &[&str], input: &str) -> String {
    let mut c = Command::new(env!("CARGO_BIN_EXE_wordfreq"))
        .args(args)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .spawn()
        .unwrap();
    c.stdin.as_mut().unwrap().write_all(input.as_bytes()).unwrap();
    let out = c.wait_with_output().unwrap();
    assert!(out.status.success());
    String::from_utf8(out.stdout).unwrap()
}

#[test]
fn counts_and_order() {
    let out = run(&[], "b a b\na c a\n");
    assert_eq!(out, "3 a\n2 b\n1 c\n");
}

#[test]
fn punctuation_and_case() {
    let out = run(&[], "Hello, hello! HELLO.\n");
    assert_eq!(out, "3 hello\n");
}

#[test]
fn top_n() {
    let out = run(&["--top", "2"], "x y z x y x\n");
    assert_eq!(out, "3 x\n2 y\n");
}
