import tkinter as tk
from tkinter import ttk, messagebox
from pynput import keyboard
import threading

# Touches disponibles
KEYS = (
    list("abcdefghijklmnopqrstuvwxyz")
    + list("0123456789")
    + [f"f{i}" for i in range(1, 13)]
    + [
        "space", "enter", "tab", "esc", "backspace",
        "delete", "insert", "home", "end", "page_up",
        "page_down", "up", "down", "left", "right",
        "shift", "ctrl", "alt", "caps_lock",
        "cmd", "print_screen", "scroll_lock", "pause",
        "minus", "equal", "left_bracket", "right_bracket",
        "backslash", "semicolon", "quote", "comma",
        "period", "slash", "num_lock"
    ]
)

# Noms lisibles pour pynput
SPECIAL = {
    "space": keyboard.Key.space,
    "enter": keyboard.Key.enter,
    "tab": keyboard.Key.tab,
    "esc": keyboard.Key.esc,
    "backspace": keyboard.Key.backspace,
    "delete": keyboard.Key.delete,
    "insert": keyboard.Key.insert,
    "home": keyboard.Key.home,
    "end": keyboard.Key.end,
    "page_up": keyboard.Key.page_up,
    "page_down": keyboard.Key.page_down,
    "up": keyboard.Key.up,
    "down": keyboard.Key.down,
    "left": keyboard.Key.left,
    "right": keyboard.Key.right,
    "shift": keyboard.Key.shift,
    "ctrl": keyboard.Key.ctrl,
    "alt": keyboard.Key.alt,
    "cmd": keyboard.Key.cmd,
    "caps_lock": keyboard.Key.caps_lock,
    "print_screen": keyboard.Key.print_screen,
    "scroll_lock": keyboard.Key.scroll_lock,
    "pause": keyboard.Key.pause,
    "num_lock": keyboard.Key.num_lock,
}

for i in range(1, 13):
    SPECIAL[f"f{i}"] = getattr(keyboard.Key, f"f{i}")


def get_key(name):
    """Convertit un nom en touche pynput."""
    if name in SPECIAL:
        return SPECIAL[name]
    if name in ("minus", "equal", "left_bracket",
                "right_bracket", "backslash", "semicolon",
                "quote", "comma", "period", "slash"):
        chars = {
            "minus": "-", "equal": "=", "left_bracket": "[",
            "right_bracket": "]", "backslash": "\\",
            "semicolon": ";", "quote": "'",
            "comma": ",", "period": ".", "slash": "/"
        }
        return chars[name]
    return name


root = tk.Tk()
root.title("Clavier personnalisé")
root.geometry("720x650")
root.minsize(620, 550)

controller = keyboard.Controller()
mappings = {}
enabled = {}
held = set()
injected = set()
lock = threading.RLock()
listener = None
running = False

trigger_var = tk.StringVar(value="f")
target_var = tk.StringVar(value="g")
status_var = tk.StringVar(value="Désactivé")


def display(name):
    return name.upper() if len(name) == 1 else name.replace("_", " ").upper()


def add_mapping():
    trigger = trigger_var.get()
    target = target_var.get()

    if trigger == target:
        messagebox.showwarning(
            "Attention", "Choisis deux touches différentes."
        )
        return

    mappings[trigger] = target
    enabled[trigger] = True
    refresh_list()


def remove_mapping():
    selected = mapping_list.curselection()
    if not selected:
        return

    trigger = list(mappings)[selected[0]]
    with lock:
        mappings.pop(trigger, None)
        enabled.pop(trigger, None)
    refresh_list()


def toggle_mapping():
    selected = mapping_list.curselection()
    if not selected:
        return

    trigger = list(mappings)[selected[0]]
    enabled[trigger] = not enabled[trigger]
    refresh_list()


def refresh_list():
    mapping_list.delete(0, tk.END)

    for trigger, target in mappings.items():
        state = "ON" if enabled.get(trigger, False) else "OFF"
        mapping_list.insert(
            tk.END,
            f"[{state}]  {display(trigger)}  →  {display(target)}"
        )


def on_press(key):
    global running

    try:
        name = key.char.lower() if key.char else None
    except AttributeError:
        name = None

    if name is None:
        for key_name, special_key in SPECIAL.items():
            if key == special_key:
                name = key_name
                break

    if name is None:
        return

    with lock:
        if name in injected:
            return

        if name in held:
            return

        held.add(name)

        target = mappings.get(name)
        if running and target and enabled.get(name, False):
            target_key = get_key(target)
            injected.add(target)
            try:
                controller.press(target_key)
            except Exception:
                injected.discard(target)


def on_release(key):
    try:
        name = key.char.lower() if key.char else None
    except AttributeError:
        name = None

    if name is None:
        for key_name, special_key in SPECIAL.items():
            if key == special_key:
                name = key_name
                break

    if name is None:
        return

    with lock:
        held.discard(name)

        target = mappings.get(name)
        if target and target in injected:
            try:
                controller.release(get_key(target))
            except Exception:
                pass
            injected.discard(target)


def start_listener():
    global listener, running

    if running:
        return

    listener = keyboard.Listener(
        on_press=on_press,
        on_release=on_release
    )
    listener.start()
    running = True
    status_var.set("ACTIF")
    status_label.config(foreground="#16a34a")


def stop_listener():
    global listener, running

    running = False

    with lock:
        for target in list(injected):
            try:
                controller.release(get_key(target))
            except Exception:
                pass
        injected.clear()
        held.clear()

    if listener:
        listener.stop()
        listener = None

    status_var.set("Désactivé")
    status_label.config(foreground="#dc2626")


root.protocol("WM_DELETE_WINDOW", lambda: (stop_listener(), root.destroy()))

# Interface
title = tk.Label(
    root, text="⌨ CLAVIER PERSONNALISÉ",
    font=("Segoe UI", 19, "bold")
)
title.pack(pady=(18, 5))

tk.Label(
    root,
    text="Associe une touche à une autre touche.",
    font=("Segoe UI", 10)
).pack()

status_frame = tk.Frame(root)
status_frame.pack(pady=12)

tk.Label(status_frame, text="Statut :").pack(side="left")
status_label = tk.Label(
    status_frame, textvariable=status_var,
    font=("Segoe UI", 10, "bold"), foreground="#dc2626"
)
status_label.pack(side="left", padx=5)

editor = ttk.LabelFrame(root, text="Créer une combinaison", padding=14)
editor.pack(fill="x", padx=22, pady=8)

tk.Label(editor, text="Quand j'appuie sur :").grid(
    row=0, column=0, sticky="w", padx=5, pady=6
)
trigger_box = ttk.Combobox(
    editor, textvariable=trigger_var,
    values=KEYS, state="readonly", width=17
)
trigger_box.grid(row=0, column=1, padx=5, pady=6)

tk.Label(editor, text="Appuyer aussi sur :").grid(
    row=1, column=0, sticky="w", padx=5, pady=6
)
target_box = ttk.Combobox(
    editor, textvariable=target_var,
    values=KEYS, state="readonly", width=17
)
target_box.grid(row=1, column=1, padx=5, pady=6)

ttk.Button(
    editor, text="＋ Ajouter la combinaison",
    command=add_mapping
).grid(row=0, column=2, rowspan=2, padx=12)

section = ttk.LabelFrame(root, text="Mes combinaisons", padding=10)
section.pack(fill="both", expand=True, padx=22, pady=8)

mapping_list = tk.Listbox(
    section, font=("Consolas", 11),
    selectmode=tk.SINGLE, height=10
)
mapping_list.pack(fill="both", expand=True, pady=5)

actions = tk.Frame(section)
actions.pack(fill="x", pady=5)

ttk.Button(
    actions, text="Activer / Désactiver",
    command=toggle_mapping
).pack(side="left", padx=4)

ttk.Button(
    actions, text="Supprimer",
    command=remove_mapping
).pack(side="left", padx=4)

controls = tk.Frame(root)
controls.pack(pady=12)

tk.Button(
    controls, text="▶ ACTIVER",
    command=start_listener,
    bg="#16a34a", fg="white",
    font=("Segoe UI", 11, "bold"),
    padx=18, pady=8
).pack(side="left", padx=8)

tk.Button(
    controls, text="■ ARRÊTER",
    command=stop_listener,
    bg="#dc2626", fg="white",
    font=("Segoe UI", 11, "bold"),
    padx=18, pady=8
).pack(side="left", padx=8)

tk.Label(
    root,
    text="Exemple : F → G | La touche G reste enfoncée tant que F l'est.",
    font=("Segoe UI", 9), foreground="gray"
).pack(pady=(0, 12))

root.mainloop()
