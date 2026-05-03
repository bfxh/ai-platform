import winreg
import ctypes
import os

PATH_TO_ADD = r"C:\Users\888\AppData\Roaming\npm"
ENV_KEY = r"Environment"
ENV_ROOT = winreg.HKEY_CURRENT_USER


def get_user_path():
    try:
        with winreg.OpenKey(ENV_ROOT, ENV_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, "PATH")
            return value
    except FileNotFoundError:
        return ""


def set_user_path(new_path):
    with winreg.OpenKey(ENV_ROOT, ENV_KEY, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)


def broadcast_setting_change():
    ctypes.windll.user32.SendMessageTimeoutW(
        0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, None
    )


def main():
    current = get_user_path()
    paths = [p.strip() for p in current.split(";") if p.strip()]

    if PATH_TO_ADD in paths:
        print(f"路径已存在于用户 PATH 中: {PATH_TO_ADD}")
        return

    paths.append(PATH_TO_ADD)
    new_path = ";".join(paths)
    set_user_path(new_path)
    broadcast_setting_change()
    print(f"已添加到用户 PATH: {PATH_TO_ADD}")
    print(f"当前用户 PATH: {new_path}")


if __name__ == "__main__":
    main()
