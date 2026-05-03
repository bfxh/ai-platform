#!/usr/bin/env python3
import asyncio
import functools
import json
import logging
import os
import shlex
import ssl
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, FrozenSet, List, Optional, Sequence, Set, Union

try:
    import certifi
except ImportError:
    certifi = None

try:
    import defusedxml.ElementTree as defused_ET
except ImportError:
    defused_ET = None

try:
    from simpleeval import simple_eval as _simple_eval, EvalWithCompoundTypes
except ImportError:
    _simple_eval = None
    EvalWithCompoundTypes = None

try:
    import httpx
except ImportError:
    httpx = None

try:
    import keyring as _keyring
except ImportError:
    _keyring = None

logger = logging.getLogger("secure_utils")

DEFAULT_ALLOWED_COMMANDS: FrozenSet[str] = frozenset({
    "git", "python", "python3", "pip", "node", "npm", "npx",
    "cargo", "rustc", "java", "javac", "go",
    "curl", "wget",
    "echo", "ls", "dir", "cat", "head", "tail", "find", "grep",
    "mkdir", "cp", "mv", "touch", "chmod",
    "docker", "podman",
    "explorer", "notepad", "code",
    "tasklist", "taskkill",
    "powershell", "cmd", "bash", "sh",
    "ollama",
    "blender", "unreal", "unity",
    "7z", "tar", "zip", "unzip",
})

_DANGEROUS_SHELL_CHARS = set(";|&$`\\!><\n\r")


class CommandNotAllowedError(PermissionError):
    pass


class SecureEvalError(ValueError):
    pass


def safe_exec_command(
    cmd: Union[str, List[str]],
    allowed_commands: Optional[Set[str]] = None,
    timeout: int = 300,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    capture_output: bool = True,
    text: bool = True,
) -> subprocess.CompletedProcess:
    if isinstance(cmd, str):
        if any(c in cmd for c in _DANGEROUS_SHELL_CHARS):
            raise CommandNotAllowedError(
                f"Command contains dangerous shell characters: {cmd[:80]}"
            )
        parts = shlex.split(cmd, posix=sys.platform != "win32")
    else:
        parts = list(cmd)

    if not parts:
        raise CommandNotAllowedError("Empty command")

    base_cmd = Path(parts[0]).stem.lower()
    if sys.platform == "win32":
        base_cmd = base_cmd.replace(".exe", "").replace(".cmd", "").replace(".bat", "")

    allowed = allowed_commands if allowed_commands is not None else DEFAULT_ALLOWED_COMMANDS
    if base_cmd not in allowed:
        raise CommandNotAllowedError(
            f"Command '{base_cmd}' not in allowed list. "
            f"Allowed: {sorted(allowed)}"
        )

    logger.info("safe_exec_command: %s (cwd=%s)", parts[0], cwd)

    return subprocess.run(
        parts,
        capture_output=capture_output,
        text=text,
        timeout=timeout,
        cwd=cwd,
        env=env,
        shell=False,
    )


def safe_xml_parse(xml_string: str, forbid_dtd: bool = True, forbid_entities: bool = True):
    if defused_ET is not None:
        return defused_ET.fromstring(xml_string)
    import xml.etree.ElementTree as ET
    logger.warning("defusedxml not available, using unsafe xml.etree.ElementTree")
    return ET.fromstring(xml_string)


def safe_xml_parse_file(xml_path: str, forbid_dtd: bool = True, forbid_entities: bool = True):
    if defused_ET is not None:
        return defused_ET.parse(xml_path)
    import xml.etree.ElementTree as ET
    logger.warning("defusedxml not available, using unsafe xml.etree.ElementTree")
    return ET.parse(xml_path)


def safe_eval_expr(
    expr: str,
    names: Optional[Dict[str, Any]] = None,
    functions: Optional[Dict[str, Any]] = None,
) -> Any:
    if _simple_eval is None:
        raise SecureEvalError("simpleeval not installed. Run: pip install simpleeval")

    if not expr or not isinstance(expr, str):
        raise SecureEvalError("Expression must be a non-empty string")

    dangerous = ("__", "import", "exec", "eval", "compile", "open", "globals", "locals", "vars")
    for d in dangerous:
        if d in expr:
            raise SecureEvalError(f"Expression contains forbidden token: '{d}'")

    try:
        if EvalWithCompoundTypes is not None:
            evaluator = EvalWithCompoundTypes(names=names, functions=functions)
            return evaluator.eval(expr)
        return _simple_eval(expr, names=names, functions=functions)
    except Exception as e:
        raise SecureEvalError(f"Safe eval failed: {e}") from e


class SecureKeyManager:
    _SERVICE_PREFIX = "D-AI"

    def __init__(self, service_name: str = "secure-keys"):
        self.service_name = f"{self._SERVICE_PREFIX}/{service_name}"
        self._keyring_available = _keyring is not None
        if not self._keyring_available:
            logger.warning("keyring not available, falling back to environment variables")

    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        if self._keyring_available:
            try:
                value = _keyring.get_password(self.service_name, key)
                if value is not None:
                    return value
            except Exception as e:
                logger.warning("keyring get failed for '%s': %s, falling back to env", key, e)

        env_key = key.upper().replace("-", "_").replace("/", "_").replace(".", "_")
        env_value = os.environ.get(env_key)
        if env_value is not None:
            return env_value

        return default

    def set(self, key: str, value: str) -> bool:
        if self._keyring_available:
            try:
                _keyring.set_password(self.service_name, key, value)
                return True
            except Exception as e:
                logger.warning("keyring set failed for '%s': %s, falling back to env file", key, e)

        env_key = key.upper().replace("-", "_").replace("/", "_").replace(".", "_")
        env_file = Path(r"\python") / ".env"
        try:
            lines = []
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            new_lines = []
            found = False
            for line in lines:
                if line.strip().startswith(f"{env_key}="):
                    new_lines.append(f"{env_key}={value}\n")
                    found = True
                else:
                    new_lines.append(line)
            if not found:
                new_lines.append(f"{env_key}={value}\n")
            with open(env_file, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
            os.environ[env_key] = value
            return True
        except Exception as e:
            logger.error("Failed to store key '%s': %s", key, e)
            return False

    def generate_and_store(self, key: str, length: int = 32) -> str:
        existing = self.get(key)
        if existing:
            return existing

        import secrets
        value = secrets.token_hex(length)
        if self.set(key, value):
            logger.info("Generated and stored new key for '%s'", key)
        return value

    def delete(self, key: str) -> bool:
        if self._keyring_available:
            try:
                _keyring.delete_password(self.service_name, key)
                return True
            except Exception:
                pass
        return False


def create_ssl_context(
    verify: bool = True,
    dev_mode_config: Optional[str] = None,
) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2

    if verify:
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = True
        if certifi is not None:
            ctx.load_verify_locations(certifi.where())
        else:
            ctx.load_default_certs()
    else:
        if dev_mode_config:
            logger.warning("SSL dev mode enabled via config: %s", dev_mode_config)
        else:
            logger.warning("SSL verification disabled - use only in development!")
        ctx.verify_mode = ssl.CERT_NONE
        ctx.check_hostname = False

    return ctx


def get_ssl_verify_path() -> Union[str, bool]:
    dev_config = Path(r"\python\config\ssl_dev_mode.json")
    if dev_config.exists():
        try:
            with open(dev_config, "r", encoding="utf-8") as f:
                config = json.load(f)
            if config.get("enabled", False):
                logger.warning("SSL dev mode active - verification disabled for: %s",
                             config.get("domains", "all"))
                return False
        except Exception:
            pass

    if certifi is not None:
        return certifi.where()
    return True


def get_http_client(
    async_client: bool = True,
    timeout: float = 30.0,
    verify: Optional[bool] = None,
    **kwargs,
):
    if httpx is None:
        raise ImportError("httpx not installed. Run: pip install httpx")

    if verify is None:
        verify = get_ssl_verify_path()

    client_kwargs = {
        "timeout": timeout,
        "verify": verify,
        **kwargs,
    }

    if async_client:
        return httpx.AsyncClient(**client_kwargs)
    return httpx.Client(**client_kwargs)


def safe_error_handler(func=None, *, default_message="Internal server error"):
    def decorator(f):
        if asyncio.iscoroutinefunction(f):
            @functools.wraps(f)
            async def async_wrapper(*args, **kwargs):
                try:
                    return await f(*args, **kwargs)
                except Exception as e:
                    logger.error("Error in %s: %s", f.__name__, e, exc_info=True)
                    return {"error": default_message}
            return async_wrapper
        else:
            @functools.wraps(f)
            def sync_wrapper(*args, **kwargs):
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    logger.error("Error in %s: %s", f.__name__, e, exc_info=True)
                    return {"error": default_message}
            return sync_wrapper

    if func is not None:
        return decorator(func)
    return decorator


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    if not value or len(value) <= visible_chars:
        return "***"
    return value[:visible_chars] + "*" * (len(value) - visible_chars)
