#!/usr/bin/env python3
"""LaunchPack pro web UI: a local page served by Python's stdlib server.

Opens in a pywebview window when pywebview is installed, otherwise in
your default browser. Everything runs on 127.0.0.1, fully offline
except the GitHub fetch you ask for. No dependencies beyond Python.
"""
import json, os, subprocess, sys, threading, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import launchpack as lp

PAGE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LaunchPack</title>
<style>
:root{--bg:#060a13;--panel:#0a101d;--card:#0e1626;--card2:#0b1322;--line:#1d2a42;--txt:#e9eef6;--mut:#8b96a8;--amber:#f5b83d;--amber2:#cf9420;--green:#3ddc74}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(1100px 650px at 50% -10%,#132441 0%,var(--bg) 60%);color:var(--txt);font-family:"Segoe UI",system-ui,-apple-system,sans-serif;min-height:100vh;padding:20px}
.app{max-width:1260px;margin:0 auto;background:linear-gradient(180deg,#0b1220,#080d17);border:1px solid var(--line);border-radius:16px;box-shadow:0 30px 80px rgba(0,0,0,.6);overflow:hidden}
header{display:flex;align-items:center;gap:12px;padding:14px 20px;border-bottom:1px solid var(--line)}
.logo{width:38px;height:38px}
h1{font-size:27px;margin:0;font-weight:700;letter-spacing:.2px}
.pill{border:1px solid var(--amber2);color:var(--amber);background:rgba(245,184,61,.08);border-radius:999px;padding:4px 12px;font-size:12px;font-weight:700}
.right{margin-left:auto;display:flex;align-items:center;gap:16px;color:var(--mut);font-size:13px}
.gdot{width:8px;height:8px;border-radius:50%;background:var(--green);display:inline-block;margin-left:4px;box-shadow:0 0 8px var(--green)}
.settings{background:var(--card);border:1px solid var(--line);color:var(--txt);border-radius:9px;padding:8px 14px;font-size:13px;cursor:pointer}
main{display:grid;grid-template-columns:330px 1fr 320px;gap:14px;padding:16px}
section{background:var(--card2);border:1px solid var(--line);border-radius:13px;padding:16px;display:flex;flex-direction:column}
.shead{display:flex;justify-content:space-between;align-items:baseline}
h2{font-size:12px;letter-spacing:2.2px;color:#c7d2e4;margin:0;text-transform:uppercase;font-weight:700}
.num{color:#54637c;font-size:12px;font-weight:700}
.modes{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:14px 0 6px}
.mode{display:flex;align-items:center;gap:9px;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 12px;cursor:pointer;font-size:13.5px}
.mode.sel{border-color:var(--amber);background:#16213a;box-shadow:0 0 0 1px var(--amber2),0 4px 14px rgba(245,184,61,.12)}
.rdot{width:14px;height:14px;border-radius:50%;border:2px solid var(--mut);flex:0 0 14px}
.mode.sel .rdot{border-color:var(--amber);background:var(--amber);box-shadow:inset 0 0 0 3px #16213a}
label.flabel{font-size:13px;color:#c7d2e4;display:block;margin:14px 0 6px;font-weight:600}
input[type=text],textarea{width:100%;background:#0a1220;border:1px solid var(--line);border-radius:9px;color:var(--txt);padding:10px 12px;font-size:13.5px;outline:none;font-family:inherit}
input[type=text]:focus,textarea:focus{border-color:var(--amber2);box-shadow:0 0 0 3px rgba(245,184,61,.14)}
textarea{resize:vertical;min-height:96px}
.modeblock{display:none}.modeblock.on{display:block}
.browse{margin-top:8px;background:var(--card);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:7px 12px;font-size:12.5px;cursor:pointer}
.extract{margin-top:auto;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:13px 14px;display:flex;gap:12px;align-items:flex-start}
.extract h3{margin:0 0 4px;font-size:13.5px}
.extract p{margin:0;color:var(--mut);font-size:12.5px;line-height:1.5}
.tgl{margin-left:auto;flex:0 0 44px;width:44px;height:24px;border-radius:999px;background:#22314d;position:relative;cursor:pointer;border:1px solid var(--line)}
.tgl::after{content:"";position:absolute;top:2px;left:2px;width:18px;height:18px;border-radius:50%;background:#93a3bb;transition:.18s}
.tgl.on{background:var(--amber2)}.tgl.on::after{left:22px;background:#141414}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}
.chip{background:var(--card);border:1px solid var(--line);color:var(--txt);border-radius:999px;padding:5px 12px;font-size:12.5px;cursor:pointer}
.chip.sel{border-color:var(--amber);color:var(--amber);background:rgba(245,184,61,.08);font-weight:700}
.plist{overflow:auto;max-height:472px;padding-right:4px;flex:1}
.plist::-webkit-scrollbar{width:8px}.plist::-webkit-scrollbar-thumb{background:#22314d;border-radius:4px}
.cat{color:var(--amber);font-size:11.5px;letter-spacing:1.6px;font-weight:700;margin:13px 0 5px;text-transform:uppercase}
.prow{display:flex;align-items:center;gap:10px;padding:6.5px 8px;border-radius:8px;cursor:pointer;font-size:14px}
.prow:hover{background:var(--card)}
.prow input{accent-color:var(--amber);width:16px;height:16px;flex:0 0 16px}
.lim{margin-left:auto;background:#131f38;border:1px solid var(--line);color:#a9b8cf;border-radius:999px;font-size:11.5px;padding:2.5px 9px;white-space:nowrap}
.pfoot{color:var(--mut);font-size:12.5px;text-align:center;padding-top:10px;border-top:1px solid var(--line);margin-top:8px}
.fmtcards{display:flex;align-items:center;gap:8px}
.fmt{flex:1;background:var(--card);border:1px solid var(--line);border-radius:11px;padding:11px 12px;cursor:pointer}
.fmt .t{font-size:14px;font-weight:700}
.fmt .s{font-size:12px;color:var(--mut);margin-top:2px}
.fmt.on{border-color:var(--amber);background:linear-gradient(180deg,rgba(245,184,61,.20),rgba(245,184,61,.07))}
.fmt.on .s{color:var(--amber)}
.fmtamp{color:var(--mut);font-weight:700}
.outrow{display:flex;gap:8px}.outrow input{flex:1}
.outrow button{background:var(--card);border:1px solid var(--line);color:var(--txt);border-radius:9px;padding:0 13px;cursor:pointer;font-size:13px}
.gen{width:100%;margin-top:18px;background:linear-gradient(180deg,#ffc44d,var(--amber2));border:0;color:#171207;font-size:16.5px;font-weight:800;letter-spacing:.8px;border-radius:11px;padding:16px;cursor:pointer;box-shadow:0 12px 26px rgba(245,184,61,.28);display:flex;align-items:center;justify-content:center;gap:10px}
.gen:hover{filter:brightness(1.06)} .gen:disabled{opacity:.55;cursor:wait}
.bar{height:5px;background:#131f38;border-radius:3px;margin-top:16px;overflow:hidden}
.bar i{display:block;height:100%;width:0;background:linear-gradient(90deg,var(--amber2),var(--amber));border-radius:3px;transition:width .3s}
.status{color:#c7d2e4;font-size:13px;margin-top:10px}
.usage{color:var(--mut);font-size:12.5px;margin-top:3px}
.openlink{display:none;margin:14px auto 0;background:none;border:0;color:#dbe4f2;font-size:13.5px;text-decoration:underline;text-underline-offset:4px;cursor:pointer}
.ofoot{margin-top:auto;display:flex;justify-content:space-between;color:var(--mut);font-size:12.5px;padding-top:14px}
.modal{position:fixed;inset:0;background:rgba(3,6,11,.7);display:none;align-items:center;justify-content:center;z-index:9}
.modal.on{display:flex}
.mbox{background:#0c1424;border:1px solid var(--line);border-radius:14px;padding:22px;width:420px;max-width:92vw}
.mbox h3{margin:0 0 8px;font-size:17px}.mbox p{color:var(--mut);font-size:13px;line-height:1.6}
.mbox .x{margin-top:14px;background:var(--card);border:1px solid var(--line);color:var(--txt);border-radius:9px;padding:9px 16px;cursor:pointer}
@media(max-width:1050px){main{grid-template-columns:1fr}}
</style></head>
<body><div class="app">
<header>
<svg class="logo" viewBox="0 0 100 100"><polygon points="50,4 90,27 90,73 50,96 10,73 10,27" fill="rgba(245,184,61,.12)" stroke="#f5b83d" stroke-width="6"/><polygon points="50,27 71,39 71,61 50,74 29,61 29,39" fill="none" stroke="#f5b83d" stroke-width="6"/></svg>
<h1>LaunchPack</h1><span class="pill" id="pcount">112 Platforms</span>
<div class="right"><span>Offline &bull; Local Only<span class="gdot"></span></span><button class="settings" id="settingsBtn">&#9881; Settings</button></div>
</header>
<main>
<section>
<div class="shead"><h2>Source</h2><span class="num">01</span></div>
<div class="modes">
<div class="mode sel" data-mode="github"><span class="rdot"></span>GitHub Repo</div>
<div class="mode" data-mode="folder"><span class="rdot"></span>Local Folder</div>
<div class="mode" data-mode="readme"><span class="rdot"></span>README File</div>
<div class="mode" data-mode="para"><span class="rdot"></span>One Paragraph</div>
</div>
<div class="modeblock on" id="blk-github">
<label class="flabel">GitHub Repo</label>
<input type="text" id="url" value="https://github.com/Tcode-Motion/techscript">
</div>
<div class="modeblock" id="blk-folder">
<label class="flabel">Project Folder</label>
<input type="text" id="folder" placeholder="C:\projects\myapp  or  /home/you/myapp">
<button class="browse" id="browseFolder">Browse...</button>
</div>
<div class="modeblock" id="blk-readme">
<label class="flabel">README File Path</label>
<input type="text" id="readme" placeholder="C:\projects\myapp\README.md">
</div>
<div class="modeblock" id="blk-para">
<label class="flabel">Your Paragraph</label>
<textarea id="para" placeholder="MyApp is a free tool that ..."></textarea>
</div>
<label class="flabel">Product Link (Optional)</label>
<input type="text" id="link" placeholder="https://launchpack.app">
<div class="extract">
<div><h3>Extraction Mode (Strict No-AI)</h3>
<p>Rules, never invents facts, leaves bracketed [story gaps] for you to fill. Off fills the gaps with neutral lines instead.</p></div>
<div class="tgl on" id="strictTgl"></div>
</div>
</section>
<section>
<div class="shead"><h2>Platforms</h2><span class="num">02</span></div>
<input type="text" id="search" placeholder="Search 112 platforms..." style="margin-top:14px">
<div class="chips">
<button class="chip" data-preset="all">All</button>
<button class="chip" data-preset="none">None</button>
<button class="chip sel" data-preset="launch">Launch Day</button>
<button class="chip" data-preset="social">Social</button>
<button class="chip" data-preset="dev">Developer</button>
</div>
<div class="plist" id="plist"></div>
<div class="pfoot" id="pfoot">0 of 112 platforms selected</div>
</section>
<section>
<div class="shead"><h2>Output</h2><span class="num">03</span></div>
<label class="flabel">Formats</label>
<div class="fmtcards">
<div class="fmt on" id="fmtMd"><div class="t">Markdown (.md)</div><div class="s">Active</div></div>
<span class="fmtamp">&amp;</span>
<div class="fmt on" id="fmtTxt"><div class="t">Plain Text (.txt)</div><div class="s">Active</div></div>
</div>
<label class="flabel">Output Folder</label>
<div class="outrow"><input type="text" id="out" value="launchpack_out"><button id="browseOut">Browse</button></div>
<button class="gen" id="go"><svg width="17" height="17" viewBox="0 0 24 24" fill="#171207"><path d="M12 2c3 2 5 6 5 10l3 3-4 1c-1 2-2 3-4 4-2-1-3-2-4-4l-4-1 3-3c0-4 2-8 5-10z"/><circle cx="12" cy="9" r="2.2" fill="#ffc44d"/></svg><span id="goTxt">GENERATE 8 POSTS</span></button>
<div class="bar"><i id="barFill"></i></div>
<div class="status" id="status">Ready to generate offline.</div>
<div class="usage" id="usage">0 files written</div>
<button class="openlink" id="openbtn">Open Output Folder</button>
<div class="ofoot"><span>No AI API needed</span><span id="ofootR">Strict Local Rules</span></div>
</section>
</main>
</div>
<div class="modal" id="modal"><div class="mbox">
<h3>Settings</h3>
<p>LaunchPack runs 100 percent on this computer. No account, no API key, no data leaves the machine. The only network call it ever makes is fetching the GitHub README you paste.</p>
<p>Strict No-AI mode is controlled by the toggle in the Source panel. Default output formats are the two cards in the Output panel.</p>
<button class="x" id="modalX">Close</button>
</div></div>
<script>
let PLATS=[], PRESETS={}, mode='github', strict=true, lastOut='';
const SEL=new Set();
const $=id=>document.getElementById(id);
fetch('/api/platforms').then(r=>r.json()).then(d=>{PLATS=d.platforms;PRESETS=d.presets;$('pcount').textContent=PLATS.length+' Platforms';$('search').placeholder='Search '+PLATS.length+' platforms...';preset('launch');render();});
function render(){
  const q=$('search').value.toLowerCase();const el=$('plist');el.innerHTML='';let cat='';
  PLATS.forEach(p=>{
    if(q && !p.name.toLowerCase().includes(q) && !p.id.includes(q)) return;
    if(p.category!==cat){cat=p.category;const h=document.createElement('div');h.className='cat';h.textContent=cat;el.appendChild(h);}
    const row=document.createElement('label');row.className='prow';
    row.innerHTML=`<input type="checkbox" data-id="${p.id}" ${SEL.has(p.id)?'checked':''}><span>${p.name}</span><span class="lim">${p.limit? 'Limit: '+p.limit+' ch' : p.style}</span>`;
    row.querySelector('input').addEventListener('change',e=>{e.target.checked?SEL.add(p.id):SEL.delete(p.id);count();});
    el.appendChild(row);
  });count();
}
function count(){const n=SEL.size;$('pfoot').textContent=n+' of '+PLATS.length+' platforms selected';$('goTxt').textContent='GENERATE '+n+' POST'+(n===1?'':'S');}
function preset(name){
  SEL.clear();
  const ids = name==='all'? PLATS.map(p=>p.id) : (PRESETS[name]||[]);
  ids.forEach(i=>SEL.add(i));
  document.querySelectorAll('.chip').forEach(c=>c.classList.toggle('sel',c.dataset.preset===name));
  render();
}
document.querySelectorAll('.chip').forEach(c=>c.addEventListener('click',()=>preset(c.dataset.preset)));
$('search').addEventListener('input',render);
document.querySelectorAll('.mode').forEach(m=>m.addEventListener('click',()=>{
  document.querySelectorAll('.mode').forEach(x=>x.classList.remove('sel'));m.classList.add('sel');mode=m.dataset.mode;
  document.querySelectorAll('.modeblock').forEach(b=>b.classList.remove('on'));$('blk-'+mode).classList.add('on');
}));
function fmtToggle(el){el.classList.toggle('on');el.querySelector('.s').textContent=el.classList.contains('on')?'Active':'Off';}
$('fmtMd').addEventListener('click',()=>fmtToggle($('fmtMd')));
$('fmtTxt').addEventListener('click',()=>fmtToggle($('fmtTxt')));
$('strictTgl').addEventListener('click',()=>{strict=!strict;$('strictTgl').classList.toggle('on',strict);$('ofootR').textContent=strict?'Strict Local Rules':'Relaxed Fill On';});
$('settingsBtn').addEventListener('click',()=>$('modal').classList.add('on'));
$('modalX').addEventListener('click',()=>$('modal').classList.remove('on'));
$('modal').addEventListener('click',e=>{if(e.target===$('modal'))$('modal').classList.remove('on');});
function pickInto(inputId){
  fetch('/api/pickfolder').then(r=>r.json()).then(d=>{if(d.ok&&d.path){$(inputId).value=d.path;}else if(!d.ok){$('status').textContent='Folder picker unavailable here. Type the path instead.';}});
}
$('browseFolder').addEventListener('click',()=>pickInto('folder'));
$('browseOut').addEventListener('click',()=>pickInto('out'));
$('go').addEventListener('click',()=>{
  const formats=[];if($('fmtMd').classList.contains('on'))formats.push('md');if($('fmtTxt').classList.contains('on'))formats.push('txt');
  if(!SEL.size||!formats.length){$('status').textContent='Pick at least one platform and one format.';return;}
  const body={mode,url:$('url').value.trim(),folder:$('folder').value.trim(),readme:$('readme').value.trim(),text:$('para').value.trim(),link:$('link').value.trim(),platforms:[...SEL],formats,out:$('out').value.trim()||'launchpack_out',strict};
  $('go').disabled=true;$('status').textContent='Working...';let w=0;$('barFill').style.width='10%';
  const iv=setInterval(()=>{w=Math.min(w+9,88);$('barFill').style.width=w+'%';},160);
  fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
   .then(r=>r.json()).then(d=>{
     clearInterval(iv);$('barFill').style.width='100%';$('go').disabled=false;
     if(d.ok){lastOut=d.out;$('status').innerHTML='Done. Posts for <b>'+d.name+'</b> are ready.';$('usage').textContent=d.files+' files written to '+d.out;$('openbtn').style.display='block';}
     else{$('status').textContent='Failed: '+d.error;$('barFill').style.width='0';}
   }).catch(e=>{clearInterval(iv);$('go').disabled=false;$('status').textContent='Failed: '+e;$('barFill').style.width='0';});
});
$('openbtn').addEventListener('click',()=>fetch('/api/open',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({path:lastOut})}));
</script></body></html>"""

PICKER = (
    "import tkinter as tk\n"
    "from tkinter import filedialog\n"
    "r = tk.Tk(); r.withdraw(); r.attributes('-topmost', True)\n"
    "p = filedialog.askdirectory()\n"
    "print(p or '')\n"
)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/api/platforms":
            self._json({"platforms": lp.load_platforms(), "presets": lp.PRESETS})
        elif self.path == "/api/pickfolder":
            try:
                r = subprocess.run([sys.executable, "-c", PICKER], capture_output=True, text=True, timeout=180)
                self._json({"ok": True, "path": r.stdout.strip()})
            except Exception as e:
                self._json({"ok": False, "error": str(e)})
        else:
            body = PAGE.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self):
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/api/open":
            path = os.path.abspath(data.get("path", ""))
            try:
                if sys.platform.startswith("win"):
                    os.startfile(path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
                self._json({"ok": True})
            except Exception as e:
                self._json({"ok": False, "error": str(e)})
            return
        if self.path != "/api/generate":
            self._json({"ok": False, "error": "unknown endpoint"}, 404)
            return
        try:
            mode = data.get("mode", "github")
            if mode == "github":
                d = lp.facts_from_github(data["url"])
            elif mode == "folder":
                d = lp.facts_from_folder(data["folder"])
            elif mode == "readme":
                hint = os.path.basename(os.path.dirname(os.path.abspath(data["readme"]))).replace("-", " ").replace("_", " ").title()
                with open(data["readme"], encoding="utf-8", errors="replace") as f:
                    d = lp.facts_from_markdown(f.read(), {}, hint)
            else:
                d = lp.facts_from_paragraph(data.get("text", ""))
            if data.get("link"):
                d["link"] = data["link"]
            allp = lp.load_platforms()
            chosen = [p for p in allp if p["id"] in set(data.get("platforms", []))]
            if not chosen:
                raise ValueError("No platforms selected")
            formats = data.get("formats") or ["md", "txt"]
            out = data.get("out") or "launchpack_out"
            made = lp.generate(d, chosen, out, formats, strict=data.get("strict", True))
            self._json({"ok": True, "count": len(made), "files": len(made) * len(formats) + 1,
                        "name": d["name"], "out": os.path.abspath(out)})
        except Exception as e:
            self._json({"ok": False, "error": str(e)})


def main():
    srv = None
    for port in range(8765, 8785):
        try:
            srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
            break
        except OSError:
            continue
    if srv is None:
        sys.exit("LaunchPack: no free local port found")
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    print("LaunchPack UI running at " + url)
    try:
        import webview
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        webview.create_window("LaunchPack", url, width=1300, height=880)
        webview.start()
        return
    except ImportError:
        pass
    webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
