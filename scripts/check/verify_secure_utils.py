#!/usr/bin/env python3
import sys
sys.path.insert(0, r'\python')

from core.secure_utils import (
    safe_exec_command, CommandNotAllowedError,
    safe_xml_parse,
    safe_eval_expr, SecureEvalError,
    SecureKeyManager,
    create_ssl_context,
    get_http_client,
    safe_error_handler,
    mask_sensitive,
)

passed = 0
failed = 0

def test(name, func):
    global passed, failed
    try:
        func()
        passed += 1
    except Exception as e:
        print(f'[FAIL] {name}: {e}')
        failed += 1

def t1():
    result = safe_exec_command(['git', '--version'], timeout=10)
    assert 'git' in result.stdout.lower(), f"Unexpected output: {result.stdout}"
    print(f'[OK] safe_exec_command: git --version -> {result.stdout.strip()}')

def t2():
    try:
        safe_exec_command(['rm', '-rf', '/'], timeout=5)
        assert False, "Should have blocked rm"
    except CommandNotAllowedError:
        print('[OK] safe_exec_command: blocked rm -rf /')

def t3():
    root = safe_xml_parse('<root><item>test</item></root>')
    assert root.tag == 'root'
    print(f'[OK] safe_xml_parse: parsed root tag={root.tag}')

def t4():
    try:
        safe_xml_parse('<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><root>&xxe;</root>')
        assert False, "Should have blocked XXE"
    except Exception as e:
        print(f'[OK] safe_xml_parse: blocked XXE attack ({type(e).__name__})')

def t5():
    result = safe_eval_expr('a + b > 10', names={'a': 5, 'b': 8})
    assert result == True
    print(f'[OK] safe_eval_expr: 5 + 8 > 10 = {result}')

def t6():
    try:
        safe_eval_expr("__import__('os').system('echo hacked')")
        assert False, "Should have blocked __import__"
    except SecureEvalError:
        print('[OK] safe_eval_expr: blocked __import__')

def t7():
    km = SecureKeyManager('test-verify-service')
    test_key = km.generate_and_store('test_verify_key')
    retrieved = km.get('test_verify_key')
    assert test_key == retrieved, f"Key mismatch: {test_key} != {retrieved}"
    km.delete('test_verify_key')
    print(f'[OK] SecureKeyManager: store/retrieve key match=True')

def t8():
    ctx = create_ssl_context()
    assert ctx.verify_mode.name == 'CERT_REQUIRED', f"Expected CERT_REQUIRED, got {ctx.verify_mode}"
    print(f'[OK] create_ssl_context: verify_mode={ctx.verify_mode.name}, check_hostname={ctx.check_hostname}')

def t9():
    client = get_http_client(async_client=True)
    assert 'AsyncClient' in type(client).__name__
    print(f'[OK] get_http_client: type={type(client).__name__}')

def t10():
    result = mask_sensitive('sk-1234567890abcdef')
    assert result.startswith('sk-1')
    assert '****' in result
    print(f'[OK] mask_sensitive: sk-1234567890abcdef -> {result}')

def t11():
    @safe_error_handler
    def test_func():
        raise ValueError('secret internal error')
    result = test_func()
    assert result == {"error": "Internal server error"}
    print(f'[OK] safe_error_handler: result={result}')

test("safe_exec_command normal", t1)
test("safe_exec_command blocked", t2)
test("safe_xml_parse normal", t3)
test("safe_xml_parse XXE blocked", t4)
test("safe_eval_expr normal", t5)
test("safe_eval_expr blocked", t6)
test("SecureKeyManager", t7)
test("create_ssl_context", t8)
test("get_http_client", t9)
test("mask_sensitive", t10)
test("safe_error_handler", t11)

print(f'\n=== Results: {passed} passed, {failed} failed ===')
sys.exit(1 if failed > 0 else 0)
