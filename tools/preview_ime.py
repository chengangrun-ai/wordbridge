"""真实输入预览：开记事本 → 切到公子输入法 → 打 diannao → 截图候选窗。

只用系统 API（ctypes），不依赖任何第三方键盘库。
跑完自动关闭记事本，不保存任何东西。
"""

import ctypes
import subprocess
import sys
import time
from ctypes import wintypes

from PIL import ImageGrab

u = ctypes.windll.user32

VK = {c: ord(c.upper()) for c in "abcdefghijklmnopqrstuvwxyz"}
VK_LWIN, VK_SPACE, VK_SHIFT, VK_CTRL = 0x5B, 0x20, 0x10, 0x11
KEYUP = 2


def tap(vk, delay=0.12):
    u.keybd_event(vk, 0, 0, 0)
    time.sleep(0.03)
    u.keybd_event(vk, 0, KEYUP, 0)
    time.sleep(delay)


def combo(*vks, delay=0.35):
    for vk in vks:
        u.keybd_event(vk, 0, 0, 0)
        time.sleep(0.03)
    for vk in reversed(vks):
        u.keybd_event(vk, 0, KEYUP, 0)
        time.sleep(0.03)
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


def main():
    # 要打的串可以从命令行传，默认 diannao
    word = sys.argv[1] if len(sys.argv) > 1 else "diannao"

    print("启动记事本...")
    subprocess.Popen(["notepad.exe"])
    time.sleep(2.0)

    wins = find_window(["记事本", "Notepad"])
    if not wins:
        print("[!] 没找到记事本窗口")
        return 1
    hwnd, title = wins[0]
    print(f"窗口: {title}")

    u.ShowWindow(hwnd, 9)          # SW_RESTORE
    u.SetForegroundWindow(hwnd)
    u.BringWindowToTop(hwnd)
    time.sleep(0.8)

    # 点一下编辑区中心：SetForegroundWindow 不保证输入焦点落到子控件上
    rect = wintypes.RECT()
    u.GetWindowRect(hwnd, ctypes.byref(rect))
    cx = (rect.left + rect.right) // 2
    cy = (rect.top + rect.bottom) // 2
    u.SetCursorPos(cx, cy)
    time.sleep(0.2)
    u.mouse_event(0x0002, 0, 0, 0, 0)   # LEFTDOWN
    u.mouse_event(0x0004, 0, 0, 0, 0)   # LEFTUP
    time.sleep(0.6)

    # 列表里只有两个输入法（公子 / 微软拼音），Win+Space 在两者间循环。
    # 落点取决于当前状态，所以按一次、截一张，多跑几次取对的那张。
    print("切换输入法（Win+Space）...")
    combo(VK_LWIN, VK_SPACE, delay=1.2)
    time.sleep(1.0)

    print(f"输入 {word} ...")
    for ch in word:
        tap(VK[ch])

    time.sleep(1.2)

    # 截全屏：竖排候选窗在光标下方，可能超出窗口边界
    img = ImageGrab.grab(all_screens=True)
    img.save("_preview_ime_full.png")
    print(f"已保存 _preview_ime_full.png {img.size}")

    # 不保存直接关掉
    u.PostMessageW(hwnd, 0x0010, 0, 0)   # WM_CLOSE
    time.sleep(0.6)
    for h, _t in find_window(["记事本", "Notepad"]):
        u.PostMessageW(h, 0x0010, 0, 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
