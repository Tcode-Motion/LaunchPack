#!/usr/bin/env python3
"""LaunchPack GUI: pick a source, tick platforms, get posts. No API key."""
import os, sys, tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import launchpack as lp

BG, PANEL, FG, ACCENT, MUTED = "#0b0f16", "#121826", "#e8edf5", "#f5b83d", "#8b96a8"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LaunchPack: repo in, launch posts out")
        self.geometry("860x640")
        self.configure(bg=BG)
        self.platforms = lp.load_platforms()
        self.checks = {}
        self._build()

    def _label(self, parent, text, size=11, color=FG, bold=False):
        return tk.Label(parent, text=text, bg=parent["bg"], fg=color,
                        font=("Segoe UI", size, "bold" if bold else "normal"))

    def _build(self):
        top = tk.Frame(self, bg=BG)
        top.pack(fill="x", padx=16, pady=(12, 4))
        self._label(top, "LaunchPack", 20, ACCENT, True).pack(side="left")
        self._label(top, f"  {len(self.platforms)} platforms, both .md and .txt, no API key", 10, MUTED).pack(side="left", pady=(8, 0))

        src = tk.LabelFrame(self, text=" 1. Your product ", bg=PANEL, fg=FG, font=("Segoe UI", 11, "bold"))
        src.pack(fill="x", padx=16, pady=8)
        self.mode = tk.StringVar(value="github")
        for val, txt in (("github", "GitHub URL"), ("folder", "Project folder"), ("para", "A paragraph"), ("manual", "Type details")):
            tk.Radiobutton(src, text=txt, variable=self.mode, value=val, bg=PANEL, fg=FG,
                           selectcolor=BG, activebackground=PANEL, activeforeground=ACCENT,
                           font=("Segoe UI", 10)).pack(side="left", padx=6, pady=6)
        row = tk.Frame(src, bg=PANEL)
        row.pack(fill="x", padx=8, pady=(0, 4))
        self.url = tk.Entry(row, bg=BG, fg=FG, insertbackground=FG, font=("Segoe UI", 10))
        self.url.pack(side="left", fill="x", expand=True)
        self.url.insert(0, "https://github.com/you/your-repo")
        tk.Button(row, text="Folder...", command=self._pick_folder, bg=BG, fg=FG).pack(side="left", padx=6)
        self.para = scrolledtext.ScrolledText(src, height=3, bg=BG, fg=FG, insertbackground=FG, font=("Segoe UI", 10))
        self.para.pack(fill="x", padx=8, pady=(0, 8))
        self.para.insert("1.0", "Or paste a paragraph here, like: MyApp is a free tool that ...")

        mid = tk.Frame(self, bg=BG)
        mid.pack(fill="both", expand=True, padx=16)
        left = tk.LabelFrame(mid, text=" 2. Platforms ", bg=PANEL, fg=FG, font=("Segoe UI", 11, "bold"))
        left.pack(side="left", fill="both", expand=True)
        btns = tk.Frame(left, bg=PANEL)
        btns.pack(fill="x", padx=6, pady=4)
        for txt, cmd in (("All", lambda: self._set_all(True)), ("None", lambda: self._set_all(False)),
                         ("Launch day", lambda: self._preset("launch")), ("Social", lambda: self._preset("social")),
                         ("Dev", lambda: self._preset("dev"))):
            tk.Button(btns, text=txt, command=cmd, bg=BG, fg=FG, font=("Segoe UI", 9)).pack(side="left", padx=2)
        canvas = tk.Canvas(left, bg=PANEL, highlightthickness=0)
        scroll = tk.Scrollbar(left, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=PANEL)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        cat = None
        for p in self.platforms:
            if p["category"] != cat:
                cat = p["category"]
                self._label(inner, cat, 10, ACCENT, True).pack(anchor="w", padx=6, pady=(8, 2))
            v = tk.BooleanVar(value=p["id"] in lp.PRESETS["launch"])
            self.checks[p["id"]] = v
            tk.Checkbutton(inner, text=p["name"], variable=v, bg=PANEL, fg=FG, selectcolor=BG,
                           activebackground=PANEL, activeforeground=ACCENT, font=("Segoe UI", 10)).pack(anchor="w", padx=10)

        right = tk.Frame(mid, bg=BG)
        right.pack(side="left", fill="y", padx=(12, 0))
        self._label(right, "3. Formats", 11, FG, True).pack(anchor="w")
        self.fmt_md = tk.BooleanVar(value=True)
        self.fmt_txt = tk.BooleanVar(value=True)
        for t, v in (("Markdown (.md)", self.fmt_md), ("Plain text (.txt)", self.fmt_txt)):
            tk.Checkbutton(right, text=t, variable=v, bg=BG, fg=FG, selectcolor=PANEL,
                           activebackground=BG, activeforeground=ACCENT, font=("Segoe UI", 10)).pack(anchor="w")
        self._label(right, "Output folder", 11, FG, True).pack(anchor="w", pady=(14, 2))
        self.out = tk.Entry(right, bg=PANEL, fg=FG, insertbackground=FG, font=("Segoe UI", 10), width=26)
        self.out.pack(anchor="w")
        self.out.insert(0, os.path.join(os.getcwd(), "launchpack_out"))
        self.status = self._label(right, "Ready.", 10, MUTED)
        self.status.pack(anchor="w", pady=(14, 6))
        tk.Button(right, text="GENERATE POSTS", command=self._go, bg=ACCENT, fg="#11131a",
                  font=("Segoe UI", 12, "bold"), padx=14, pady=8).pack(anchor="w")
        tk.Button(right, text="Open output folder", command=self._open_out, bg=PANEL, fg=FG,
                  font=("Segoe UI", 10)).pack(anchor="w", pady=(8, 0))

    def _pick_folder(self):
        d = filedialog.askdirectory()
        if d:
            self.mode.set("folder")
            self.url.delete(0, "end")
            self.url.insert(0, d)

    def _set_all(self, on):
        for v in self.checks.values():
            v.set(on)

    def _preset(self, name):
        ids = lp.PRESETS[name]
        for pid, v in self.checks.items():
            v.set(pid in ids)

    def _open_out(self):
        path = self.out.get().strip()
        if not os.path.isdir(path):
            return
        if sys.platform.startswith("win"):
            os.startfile(path)
        elif sys.platform == "darwin":
            os.system(f'open "{path}" >/dev/null 2>&1 &')
        else:
            os.system(f'xdg-open "{path}" >/dev/null 2>&1 &')

    def _facts(self):
        mode = self.mode.get()
        if mode == "github":
            return lp.facts_from_github(self.url.get().strip())
        if mode == "folder":
            return lp.facts_from_folder(self.url.get().strip())
        if mode == "para":
            return lp.facts_from_paragraph(self.para.get("1.0", "end").strip())
        return {"name": "My Product", "tagline": "[one line: what it does]", "desc": "[what it is]",
                "features": [], "link": "", "topics": [], "lang": ""}

    def _go(self):
        chosen = [p for p in self.platforms if self.checks[p["id"]].get()]
        formats = (["md"] if self.fmt_md.get() else []) + (["txt"] if self.fmt_txt.get() else [])
        if not chosen or not formats:
            messagebox.showwarning("LaunchPack", "Pick at least one platform and one format.")
            return
        self.status.config(text="Working...")
        self.update_idletasks()
        try:
            d = self._facts()
            made = lp.generate(d, chosen, self.out.get().strip(), formats)
            self.status.config(text=f"Done: {len(made)} posts for {d['name']}.")
        except Exception as e:
            self.status.config(text="Failed. See the error box.")
            messagebox.showerror("LaunchPack", str(e))


if __name__ == "__main__":
    App().mainloop()
