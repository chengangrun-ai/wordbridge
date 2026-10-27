"""实测跨词语境：打 san → 空格上屏「三」→ 打 mi → 截图看注释。

验证的是：上文有「三」时，「米」的注释应该变成 meter 而不是 rice。
"""

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes

from PIL import ImageGrab

u = ctypes.windll.user32
VK = {c: ord(c.upper()) for c in "abcdefghijklmnopqrstuvwxyz"}
VK_SPACE = 0x20
KEYUP = 2


def tap(vk, delay=0.1):
    u.keybd_event(vk, 0, 0, 0)
    time.sleep(0.02)
    u.keybd_event(vk, 0, KEYUP, 0)
    time.sleep(delay)


def find_window(keywords):
    hit = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        n = u.GetWindowTextLengthW(hwnd)
        if n == 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, buf, n + 1)
        if any(k in buf.value for k in keywords):
            hit.append((hwnd, buf.value))
        return True

    u.EnumWindows(cb, 0)
    return hit


def type_word(word):
    for ch in word:
        tap(VK[ch])


def main():
    subprocess.Popen(["notepad.exe"])
    time.sleep(2.0)

    wins = find_window(["记事本", "Notepad"])
    if not wins:
        print("[!] 没找到记事本")
        return 1
    hwnd, title = wins[0]
    print(f"窗口: {title}")

    u.ShowWindow(hwnd, 9)
    u.SetForegroundWindow(hwnd)
    u.BringWindowToTop(hwnd)
    time.sleep(0.8)

    rect = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(rect))
    cx, cy = (rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2
    u.SetCursorPos(cx, cy)
    time.sleep(0.2)
    u.mouse_event(0x0002, 0, 0, 0, 0)
    u.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.6)

    print("切换输入法（Win+Space）...")
    for vk in (0x5B, VK_SPACE):
        u.keybd_event(vk, 0, 0, 0)
        time.sleep(0.03)
    for vk in (VK_SPACE, 0x5B):
        u.keybd_event(vk, 0, KEYUP, 0)
        time.sleep(0.03)
    time.sleep(1.4)          # 等切换浮层消失

    print("打 san ...")
    type_word("san")
    time.sleep(0.9)

    print("空格上屏「三」...")
    tap(VK_SPACE, delay=0.7)

    print("打 mi ...")
    type_word("mi")
    time.sleep(1.2)

    img = ImageGrab.grab(all_screens=True)
    img.save("_test_context_full.png")
    print(f"已保存 _test_context_full.png {img.size}")

    u.PostMessageW(hwnd, 0x0010, 0, 0)
    time.sleep(0.5)
    for h, _t in find_window(["记事本", "Notepad"]):
        u.PostMessageW(h, 0x0010, 0, 0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
