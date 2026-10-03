import os, re, json, uuid, html, hmac, threading
from flask import Flask, request, session, jsonify, send_from_directory, abort

BASE = os.environ.get("DATA_DIR", os.path.dirname(os.path.abspath(__file__)))
UP = os.path.join(BASE, "uploads")
DB = os.path.join(BASE, "data.json")
os.makedirs(UP, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
USER = os.environ.get("ADMIN_USER", "admin")
PASS = os.environ.get("ADMIN_PASS", "admin123")
lock = threading.Lock()

DEFAULT = {
    "settings": {"title": "My Official Website", "name": "Your Name", "tagline": "Official Website",
                 "footer": "(c) 2026 Your Name. All Rights Reserved.", "accent": "#00e5ff",
                 "avatar": "", "bg": "", "weather": True,
                 "com_en": "Facing problems with your projects? Join our official community for help and guidance.",
                 "com_bn": "", "com_tg": "https://t.me/", "com_yt": "https://youtube.com/"},
    "cards": [
        {"title": "Free Website", "badge": "100% Free", "icon": "globe", "url": "#versions"},
        {"title": "APK Building", "badge": "100% Free", "icon": "phone", "url": ""},
        {"title": "Bot Making", "badge": "100% Free", "icon": "bot", "url": "#bots"},
        {"title": "Security", "badge": "100% Free", "icon": "shield", "url": "#security"},
        {"title": "Review Project", "badge": "100% Free", "icon": "star", "url": "#reviews"},
    ],
    "pages": [
        {"id": "versions", "title": "Versions", "password": "", "color": False, "build": "", "start": "",
         "items": [{"title": "Version 1.0", "desc": "Password protected", "url": "#v1", "icon": "shield"},
                   {"title": "Version 5.5", "desc": "Node project with Render commands", "url": "#v55", "icon": "globe"}]},
        {"id": "v1", "title": "V1.0", "password": "1234", "color": True, "build": "", "start": "",
         "items": [{"title": "Notepad", "desc": "Open browser notepad", "url": "#notepad", "icon": "file"},
                   {"title": "Netlify", "desc": "Deploy your website instantly", "url": "https://www.netlify.com/", "icon": "link"},
                   {"title": "Download Main File", "desc": "Get the final project file", "url": "https://example.com", "icon": "download"}]},
        {"id": "v55", "title": "V5.5", "password": "", "color": True, "build": "npm install", "start": "npm start",
         "items": [{"title": "Render", "desc": "Host web apps", "url": "https://render.com/", "icon": "link"},
                   {"title": "GitHub", "desc": "Code hosting platform", "url": "https://github.com/", "icon": "link"}]},
        {"id": "bots", "title": "Bot Versions", "password": "", "color": False, "build": "", "start": "",
         "items": [{"title": "Version 1.0", "desc": "Bot Version 1.0", "url": "https://example.com", "icon": "bot"}]},
        {"id": "security", "title": "Security", "password": "", "color": False, "build": "", "start": "",
         "items": [{"title": "App Security", "desc": "Version 1.0", "url": "https://example.com", "icon": "shield"}]},
        {"id": "reviews", "title": "Reviews", "password": "", "color": False, "build": "", "start": "",
         "items": [{"title": "Free Hosting", "desc": "Get free hosting for your website", "url": "https://example.com", "icon": "globe"}]},
    ],
    "socials": [
        {"title": "YouTube", "handle": "@yourname", "icon": "youtube", "url": "#", "img": ""},
        {"title": "Facebook", "handle": "@yourname", "icon": "facebook", "url": "#", "img": ""},
        {"title": "Telegram", "handle": "@yourname", "icon": "telegram", "url": "#", "img": ""},
    ],
}

ICONS = {
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15 15 0 0 1 0 20M12 2a15 15 0 0 0 0 20"/>',
    "phone": '<rect x="5" y="2" width="14" height="20" rx="2"/><path d="M12 18h.01"/>',
    "bot": '<rect x="4" y="8" width="16" height="12" rx="3"/><path d="M12 8V4M8 14h.01M16 14h.01M9 18h6"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "star": '<path d="M12 2l3 7 7 .6-5.3 4.7 1.6 7.2L12 17.8 5.7 21.5l1.6-7.2L2 9.6 9 9z"/>',
    "youtube": '<rect x="2" y="5" width="20" height="14" rx="4"/><path d="M10 9l5 3-5 3z"/>',
    "facebook": '<path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z"/>',
    "instagram": '<rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>',
    "tiktok": '<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>',
    "discord": '<path d="M21 11.5a8.4 8.4 0 0 1-9 8.4 8.5 8.5 0 0 1-3.8-.9L3 21l1.9-5.7A8.4 8.4 0 0 1 4 11.5 8.5 8.5 0 0 1 12.5 3 8.4 8.4 0 0 1 21 11.5z"/>',
    "telegram": '<path d="M22 2L11 13M22 2l-7 20-4-9-9-4z"/>',
    "link": '<path d="M10 13a5 5 0 0 0 7 0l3-3a5 5 0 0 0-7-7l-1 1M14 11a5 5 0 0 0-7 0l-3 3a5 5 0 0 0 7 7l1-1"/>',
    "download": '<path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16"/>',
    "upload": '<path d="M12 15V3m0 0L8 7m4-4l4 4M4 21h16"/>',
    "left": '<path d="M15 6l-6 6 6 6"/>', "file": '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9zM14 3v6h6M8 13h8M8 17h5"/>',
    "go": '<path d="M9 6l6 6-6 6"/>', "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "up": '<path d="M6 15l6-6 6 6"/>', "down": '<path d="M6 9l6 6 6-6"/>',
    "trash": '<path d="M3 6h18M8 6V4h8v2M6 6l1 14h10l1-14"/>', "plus": '<path d="M12 5v14M5 12h14"/>',
}

CSS = r"""
:root{--a:#00e5ff;--bg:#05070d;--t:#e8eef7;--m:#8b97a8}
*{box-sizing:border-box;margin:0}
body{background:var(--bg) center/cover fixed;color:var(--t);font-family:system-ui,'Noto Sans Bengali',sans-serif;min-height:100vh}
svg.i{width:1.2em;height:1.2em;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round;flex:none}
.orbs i{position:fixed;width:46vmax;height:46vmax;border-radius:50%;filter:blur(90px);opacity:.25;background:var(--a);top:-15%;left:-10%;animation:fl 18s ease-in-out infinite alternate;z-index:-1}
.orbs i:nth-child(2){background:#7c3aed;left:55%;top:40%;animation-duration:24s}
.orbs i:nth-child(3){background:#ec4899;left:-10%;top:60%;animation-duration:30s}
@keyframes fl{to{transform:translate(8vw,-10vh) scale(1.2)}}
@keyframes up{from{opacity:0;transform:translateY(18px)}to{opacity:1}}
a{color:inherit;text-decoration:none}
"""

PUB_CSS = r"""
main{max-width:760px;margin:auto;padding:40px 18px 60px}
header{text-align:center;margin-bottom:30px}
.ring{position:relative;width:112px;height:112px;margin:auto}
.ring:before{content:"";position:absolute;inset:-4px;border-radius:50%;background:conic-gradient(var(--a),#7c3aed,#ec4899,var(--a));animation:sp 5s linear infinite}
.ring img{position:relative;width:100%;height:100%;border-radius:50%;object-fit:cover;border:4px solid var(--bg);background:#111}
@keyframes sp{to{transform:rotate(360deg)}}
h1{margin-top:18px;font-size:28px;background:linear-gradient(90deg,var(--a),#a78bfa,#f472b6,var(--a));background-size:200%;-webkit-background-clip:text;background-clip:text;color:transparent;animation:sh 6s linear infinite}
@keyframes sh{to{background-position:200%}}
header p{color:var(--m);margin-top:6px}
.sec{margin:30px 0 12px;font-size:13px;letter-spacing:.15em;text-transform:uppercase;color:var(--m)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.card{display:flex;align-items:center;gap:14px;padding:16px;border-radius:16px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.09);backdrop-filter:blur(12px);transition:.3s;cursor:pointer;opacity:0;animation:up .6s forwards}
.card:hover{transform:translateY(-4px);border-color:var(--a);box-shadow:0 8px 30px -8px var(--a)}
.card small{display:block;color:var(--a);font-size:11px;margin-bottom:2px}
.ib{width:42px;height:42px;display:grid;place-items:center;border-radius:12px;background:rgba(255,255,255,.06);color:var(--a);font-size:20px}
.ar{margin-left:auto;color:var(--m)}
.wx{margin-top:26px;justify-content:space-between;cursor:default;animation-delay:.6s}
.wx:hover{transform:none}
#wt{font-size:34px;font-weight:700;color:var(--a)}
#wm{color:var(--m);font-size:13px}
footer{text-align:center;color:var(--m);font-size:12px;margin-top:40px}
.modal{position:fixed;inset:0;background:rgba(0,0,0,.6);backdrop-filter:blur(6px);display:none;place-items:center;padding:18px;z-index:9}
.modal.on{display:grid}
.mdl{width:100%;max-width:460px;max-height:80vh;overflow:auto;background:#0b1019;border:1px solid rgba(255,255,255,.1);border-radius:18px;padding:20px;animation:up .3s}
.mdl h3{margin-bottom:10px}
.x{float:right;background:none;border:0;color:var(--t);cursor:pointer;font-size:20px}
.row{display:flex;gap:12px;align-items:center;padding:12px;border-radius:12px;background:rgba(255,255,255,.05);margin-top:8px;border:1px solid transparent;transition:.2s;cursor:pointer}
.row:hover{border-color:var(--a);transform:translateX(4px)}
.row div span{display:block;color:var(--m);font-size:13px;margin-top:2px}
.ib img{width:100%;height:100%;border-radius:12px;object-fit:cover}
.back{background:none;border:0;color:var(--m);cursor:pointer;display:inline-flex;gap:4px;align-items:center;margin-bottom:8px;font:inherit}
.back:hover{color:var(--a)}
.mdl .box{margin-top:12px;padding:12px;border-radius:12px;background:rgba(255,255,255,.05);display:grid;gap:6px}
.mdl small{color:var(--m)}
code{display:block;padding:8px 10px;border-radius:8px;background:#000;color:var(--a);cursor:pointer;font-size:13px;word-break:break-all;min-height:1.6em}
.mdl input[type=password],.mdl textarea{width:100%;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);color:var(--t);font:inherit;margin:8px 0}
.mdl input[type=color]{width:100%;height:44px;border:0;background:none;padding:0}
.mdl textarea{min-height:200px}
.mdl p{color:var(--m);margin:8px 0;line-height:1.5}
.acts{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}
.btn{display:inline-flex;gap:8px;align-items:center;padding:10px 16px;border-radius:12px;background:var(--a);color:#001018;font-weight:600;border:0;cursor:pointer;font-size:14px;transition:.2s}
.btn:hover{filter:brightness(1.15);transform:translateY(-1px)}
.ck{display:flex;gap:8px;align-items:center;font-size:13px;color:var(--m);margin:10px 0}
#tt{position:fixed;bottom:24px;left:50%;transform:translate(-50%,20px);opacity:0;background:#0b1019;border:1px solid var(--a);padding:10px 18px;border-radius:12px;transition:.3s;z-index:20;pointer-events:none}
#tt.on{opacity:1;transform:translate(-50%,0)}
"""

ADM_CSS = r"""
main{max-width:900px;margin:auto;padding:20px 16px 80px}
.bar{position:sticky;top:0;z-index:5;display:flex;gap:10px;align-items:center;justify-content:space-between;padding:12px 16px;background:rgba(5,7,13,.85);backdrop-filter:blur(10px);border-bottom:1px solid rgba(255,255,255,.08)}
h2{margin:28px 0 8px;font-size:15px;color:var(--a);letter-spacing:.1em;text-transform:uppercase}
.box{border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:14px;margin:16px 0;position:relative;background:rgba(255,255,255,.03);animation:up .4s}
.g{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:10px;margin-bottom:10px}
label{display:block;font-size:12px;color:var(--m)}
input,select,textarea{width:100%;margin-top:4px;padding:10px;border-radius:10px;border:1px solid rgba(255,255,255,.12);background:rgba(255,255,255,.05);color:var(--t);font:inherit}
input[type=color]{height:42px;padding:3px}
textarea{min-height:80px}
option{background:#111}
.ck{display:flex;gap:8px;align-items:center;margin-top:8px}
.ck input{width:auto;margin:0}
.btn{display:inline-flex;gap:8px;align-items:center;padding:10px 16px;border-radius:12px;background:var(--a);color:#001018;font-weight:600;border:0;cursor:pointer;font-size:14px;transition:.2s}
.btn:hover{filter:brightness(1.15);transform:translateY(-1px)}
.ctl{position:absolute;right:10px;top:-16px;display:flex;gap:4px}
.ctl button{width:32px;height:32px;border-radius:9px;border:1px solid rgba(255,255,255,.15);background:#0b1019;color:var(--t);cursor:pointer;display:grid;place-items:center}
.ctl button:hover{border-color:var(--a)}
.files{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}
.files img{width:90px;height:90px;object-fit:cover;border-radius:10px;display:block}
.files .btn{padding:4px 10px;width:100%;justify-content:center;margin-top:4px}
#tt{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#0b1019;border:1px solid var(--a);padding:10px 18px;border-radius:12px;display:none;z-index:9}
.login{max-width:340px;margin:18vh auto;padding:24px;border-radius:18px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1)}
.login h2{margin:0 0 14px}
.login .btn{width:100%;justify-content:center;margin-top:14px}
"""

PUB = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITLE__</title><style>__CSS__</style></head><body>
<div class="orbs"><i></i><i></i><i></i></div>
<main><header><div class="ring"><img id="av" alt=""></div><h1 id="nm"></h1><p id="tg"></p></header>
<section id="cards" class="grid"></section>
<h2 class="sec">Connect</h2><section id="soc" class="grid"></section>
<div class="card wx" id="wxb"><div><div id="wt">--</div><div id="wd">Locating...</div></div><div id="wm"></div></div>
<footer id="ft"></footer></main>
<div class="modal" id="md"><div class="mdl"><button class="x" id="cx"></button><div id="mb"></div></div></div>
<div class="modal" id="cm"></div><div id="tt"></div>
<script>
const I=__ICONS__;
const ic=k=>'<svg class="i" viewBox="0 0 24 24">'+(I[k]||I.link)+'</svg>';
const E=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let D,cur=null,ST=[];cx.innerHTML=ic('x');
const P=id=>D.pages.find(p=>p.id==id);
function T(m){tt.textContent=m;tt.classList.add('on');clearTimeout(T.t);T.t=setTimeout(()=>tt.classList.remove('on'),1800)}
function cp(t){navigator.clipboard.writeText(t);T('Copied')}
function closeM(){md.classList.remove('on');cur=null;ST=[]}
cx.onclick=closeM;md.onclick=e=>{if(e.target==md)closeM()};
document.onkeydown=e=>{if(e.key=='Escape')closeM()};
function nav(u,top){if(!u)return;if(u[0]!='#')return window.open(u,'_blank','noopener');
 if(top)ST=[];else if(cur)ST.push(cur);cur=u.slice(1);show()}
function bk(){cur=ST.pop();cur?show():closeM()}
function body(p){let h=(p.items||[]).map(i=>'<div class="row" data-u="'+E(i.url)+'" onclick="nav(this.dataset.u)"><span class="ib">'+ic(i.icon||'link')+'</span><div><b>'+E(i.title)+'</b><span>'+E(i.desc)+'</span></div></div>').join('');
 if(p.build)h+='<div class="box"><b>Render command</b><small>Build Command</small><code onclick="cp(this.textContent)">'+E(p.build)+'</code><small>Start Command</small><code onclick="cp(this.textContent)">'+E(p.start)+'</code></div>';
 if(p.color)h+='<div class="box"><b>Color Picker</b><input type="color" id="cl" value="#00e5ff" oninput="cc(this.value)"><small>HEX</small><code id="hx" onclick="cp(this.textContent)"></code><small>RGB</small><code id="rg" onclick="cp(this.textContent)"></code></div>';
 return h}
function cc(v){hx.textContent=v;rg.textContent=[1,3,5].map(i=>parseInt(v.substr(i,2),16)).join(', ')}
function show(){let h='<button class="back" onclick="bk()">'+ic('left')+' Back</button>';
 if(cur=='notepad')h+='<h3>Notepad</h3><textarea id="np" placeholder="Type here..."></textarea><div class="acts"><label class="btn">'+ic('upload')+' Upload file<input type="file" accept=".txt,.html,.js,.json" hidden onchange="nf(this)"></label><button class="btn" onclick="ns()">'+ic('download')+' Save</button></div>';
 else{const p=P(cur);if(!p)return closeM();h+='<h3>'+E(p.title)+'</h3>';
  if(p.locked&&!p.open)h+='<p>Enter the secret password to unlock.</p><input id="pw" type="password" placeholder="Password"><button class="btn" onclick="ul()">Unlock</button>';
  else h+=body(p)}
 mb.innerHTML=h;md.classList.add('on');if(document.getElementById('cl'))cc('#00e5ff')}
async function ul(){const r=await fetch('/api/unlock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:cur,pw:pw.value})});
 if(!r.ok)return T('Wrong password');const p=P(cur);p.items=(await r.json()).items;p.open=1;show()}
function nf(e){if(!e.files[0])return;const r=new FileReader();r.onload=()=>np.value=r.result;r.readAsText(e.files[0])}
function ns(){const n=prompt('File name (.txt will be added)');if(!n)return;const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([np.value]));a.download=n.replace(/[^\w\- ]/g,'')+'.txt';a.click()}
function com(){const s=D.settings;try{if(!s.com_en||localStorage.getItem('nc'))return}catch(e){}
 cm.innerHTML='<div class="mdl"><h3>Join Community</h3><p>'+E(s.com_en)+'</p><p>'+E(s.com_bn)+'</p><div class="acts"><a class="btn" target="_blank" rel="noopener" href="'+E(s.com_tg)+'">'+ic('telegram')+' Telegram</a><a class="btn" target="_blank" rel="noopener" href="'+E(s.com_yt)+'">'+ic('youtube')+' YouTube</a></div><label class="ck"><input type="checkbox" id="nsh"> Don\'t show this again</label><button class="btn" onclick="cm2()">Close</button></div>';
 setTimeout(()=>cm.classList.add('on'),800)}
function cm2(){try{if(nsh.checked)localStorage.setItem('nc',1)}catch(e){}cm.classList.remove('on')}
function wx(la,lo){fetch('https://api.open-meteo.com/v1/forecast?latitude='+la+'&longitude='+lo+'&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code')
 .then(r=>r.json()).then(j=>{const c=j.current,k=c.weather_code;
  wt.textContent=Math.round(c.temperature_2m)+'\u00b0C';
  wd.textContent=k==0?'Clear Sky':k<4?'Cloudy':k<50?'Fog':k<70?'Rain':k<80?'Snow':k<90?'Showers':'Thunderstorm';
  wm.textContent=c.wind_speed_10m+' km/h  |  '+c.relative_humidity_2m+'%  |  Feels '+Math.round(c.apparent_temperature)+'\u00b0'}).catch(()=>{wd.textContent='Unavailable'})}
fetch('/api/data').then(r=>r.json()).then(d=>{D=d;const s=d.settings;
 document.documentElement.style.setProperty('--a',s.accent);
 if(s.bg)document.body.style.backgroundImage='linear-gradient(rgba(5,7,13,.82),rgba(5,7,13,.82)),url('+s.bg+')';
 av.src=s.avatar||'';av.style.display=s.avatar?'':'none';nm.textContent=s.name;tg.textContent=s.tagline;ft.textContent=s.footer;
 cards.innerHTML=d.cards.map((c,n)=>'<div class="card" style="animation-delay:'+n*.08+'s" onclick="nav(D.cards['+n+'].url,1)"><span class="ib">'+ic(c.icon)+'</span><div><small>'+E(c.badge)+'</small><b>'+E(c.title)+'</b></div><span class="ar">'+ic('go')+'</span></div>').join('');
 soc.innerHTML=d.socials.map((c,n)=>'<a class="card" style="animation-delay:'+(.4+n*.08)+'s" target="_blank" rel="noopener" href="'+E(c.url)+'"><span class="ib">'+(c.img?'<img src="'+E(c.img)+'" alt="">':ic(c.icon))+'</span><div><small>'+E(c.handle)+'</small><b>'+E(c.title)+'</b></div><span class="ar">'+ic('go')+'</span></a>').join('');
 if(!s.weather)wxb.style.display='none';
 else navigator.geolocation?navigator.geolocation.getCurrentPosition(p=>wx(p.coords.latitude,p.coords.longitude),()=>wx(23.81,90.41),{timeout:5000}):wx(23.81,90.41);com()});
</script></body></html>"""

LOGIN = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Login</title><style>__CSS__</style></head><body><div class="orbs"><i></i><i></i><i></i></div>
<form class="login" method="post"><h2>Admin Login</h2>
<label>Username<input name="u" autocomplete="username" required></label><br>
<label>Password<input name="p" type="password" autocomplete="current-password" required></label>
<button class="btn">Sign in</button><p style="color:#f87171;margin-top:10px;font-size:13px">__ERR__</p></form></body></html>"""

ADM = r"""<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Panel</title><style>__CSS__</style></head><body><div class="orbs"><i></i><i></i><i></i></div>
<div class="bar"><b>Admin Panel</b><div style="display:flex;gap:8px"><a class="btn" href="/" target="_blank" id="vw"></a><button class="btn" onclick="save()" id="sv"></button><a class="btn" href="/admin/logout" id="lo">Logout</a></div></div>
<main id="app"></main><div id="tt"></div>
<script>
const I=__ICONS__;
const ic=k=>'<svg class="i" viewBox="0 0 24 24">'+(I[k]||I.link)+'</svg>';
const E=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const Q=s=>document.querySelector(s);let D;
vw.innerHTML=ic('globe')+' View site';sv.innerHTML=ic('download')+' Save';
function T(m){tt.textContent=m;tt.style.display='block';clearTimeout(T.t);T.t=setTimeout(()=>tt.style.display='none',2200)}
function S(e){const k=e.dataset.p.split('.');let o=D;while(k.length>1)o=o[k.shift()];o[k[0]]=e.type=='checkbox'?e.checked:e.value}
const F=(p,l,v,t)=>'<label>'+l+'<input '+(t?'type="'+t+'" ':'')+'data-p="'+p+'" value="'+E(v)+'" oninput="S(this)"></label>';
const sel=(p,v)=>'<label>Icon<select data-p="'+p+'" oninput="S(this)">'+Object.keys(I).map(k=>'<option'+(k==v?' selected':'')+'>'+k+'</option>').join('')+'</select></label>';
const imgF=(k,l,v)=>'<div>'+F('settings.'+k,l+' (URL)',v)+'<label class="btn" style="margin-top:8px">'+ic('upload')+' Upload photo<input type="file" accept="image/*" hidden onchange="U(this,\''+k+'\')"></label></div>';
const ctl=(a,n)=>'<div class="ctl"><button onclick="mv(\''+a+'\','+n+',-1)">'+ic('up')+'</button><button onclick="mv(\''+a+'\','+n+',1)">'+ic('down')+'</button><button onclick="rm(\''+a+'\','+n+')">'+ic('trash')+'</button></div>';
const pageH=(p,n)=>{if(p._t===undefined)p._t=(p.items||[]).map(i=>[i.title,i.desc,i.url,i.icon].join(' | ')).join('\n');
 return '<div class="box">'+ctl('pages',n)+'<div class="g">'+F('pages.'+n+'.id','Page ID (link it as #id)',p.id)+F('pages.'+n+'.title','Title',p.title)+F('pages.'+n+'.password','Password (empty = open)',p.password)+F('pages.'+n+'.build','Render build command (optional)',p.build)+F('pages.'+n+'.start','Render start command (optional)',p.start)+'</div><label class="ck"><input type="checkbox" data-p="pages.'+n+'.color" '+(p.color?'checked':'')+' oninput="S(this)"> Show color picker</label><label>Items, one per line: Title | Description | URL or #pageid or #notepad | icon<textarea data-p="pages.'+n+'._t" oninput="S(this)">'+E(p._t)+'</textarea></label></div>'};
const cardH=(c,n)=>'<div class="box">'+ctl('cards',n)+'<div class="g">'+F('cards.'+n+'.title','Title',c.title)+F('cards.'+n+'.badge','Badge text',c.badge)+sel('cards.'+n+'.icon',c.icon)+F('cards.'+n+'.url','Link, or #pageid to open a page',c.url)+'</div></div>';
const socH=(c,n)=>'<div class="box">'+ctl('socials',n)+'<div class="g">'+F('socials.'+n+'.title','Name',c.title)+F('socials.'+n+'.handle','Handle',c.handle)+sel('socials.'+n+'.icon',c.icon)+F('socials.'+n+'.url','Link',c.url)+F('socials.'+n+'.img','Photo URL (optional)',c.img)+'</div></div>';
function draw(){const s=D.settings;
 Q('#app').innerHTML='<h2>Site</h2><div class="g">'+F('settings.title','Page title',s.title)+F('settings.name','Name',s.name)+F('settings.tagline','Tagline',s.tagline)+F('settings.footer','Footer text',s.footer)+F('settings.accent','Accent color',s.accent,'color')+'</div><div class="g">'+imgF('avatar','Profile photo',s.avatar)+imgF('bg','Background photo',s.bg)+'</div>'
 +'<label class="ck"><input type="checkbox" data-p="settings.weather" '+(s.weather?'checked':'')+' oninput="S(this)"> Show weather widget</label><h2>Community popup (empty English text = off)</h2><div class="g">'+F('settings.com_en','English text',s.com_en)+F('settings.com_bn','Bengali text',s.com_bn)+F('settings.com_tg','Telegram link',s.com_tg)+F('settings.com_yt','YouTube link',s.com_yt)+'</div>'
 +'<h2>Cards</h2>'+D.cards.map(cardH).join('')+'<button class="btn" onclick="add(\'cards\')">'+ic('plus')+' Add card</button>'
 +'<h2>Pages (popups)</h2>'+D.pages.map(pageH).join('')+'<button class="btn" onclick="add(\'pages\')">'+ic('plus')+' Add page</button>'
 +'<h2>Social links</h2>'+D.socials.map(socH).join('')+'<button class="btn" onclick="add(\'socials\')">'+ic('plus')+' Add link</button>'
 +'<h2>Media library</h2><label class="btn" style="display:inline-flex">'+ic('upload')+' Upload file<input type="file" accept="image/*" hidden onchange="U(this)"></label><div id="fl" class="files"></div>';files()}
function mv(k,n,d){const a=D[k],j=n+d;if(j<0||j>=a.length)return;[a[n],a[j]]=[a[j],a[n]];draw()}
function rm(k,n){if(confirm('Delete this item?')){D[k].splice(n,1);draw()}}
function add(k){D[k].push({cards:{title:'New card',badge:'100% Free',icon:'link',url:''},pages:{id:'page'+Date.now().toString(36),title:'New page',password:'',color:false,build:'',start:'',items:[]},socials:{title:'New link',handle:'',icon:'link',url:'',img:''}}[k]);draw()}
async function U(e,k){if(!e.files[0])return;const f=new FormData();f.append('file',e.files[0]);
 const j=await (await fetch('/api/upload',{method:'POST',body:f})).json();
 if(!j.url)return T(j.error||'Upload failed');
 if(k){D.settings[k]=j.url;draw()}else files();T('Uploaded')}
async function files(){const j=await (await fetch('/api/files')).json();
 Q('#fl').innerHTML=j.map(u=>'<div><img src="'+u+'"><button class="btn" onclick="navigator.clipboard.writeText(location.origin+\''+u+'\');T(\'Link copied\')">'+ic('link')+'</button></div>').join('')}
async function save(){D.pages.forEach(p=>{if(p._t!==undefined)p.items=p._t.split('\n').map(l=>l.trim()).filter(Boolean).map(l=>{const x=l.split('|').map(y=>y.trim());return{title:x[0],desc:x[1]||'',url:x[2]||'',icon:x[3]||'link'}})});
 const r=await fetch('/api/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(D)});T(r.ok?'Saved':'Save failed')}
fetch('/api/admin-data').then(r=>r.json()).then(d=>{D=d;draw()});
</script></body></html>"""


def load():
    try:
        with open(DB, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        d = {}
    base = json.loads(json.dumps(DEFAULT))
    d = {k: d.get(k, base[k]) for k in base}
    d["settings"] = {**base["settings"], **d["settings"]}
    return d


def clean_items(lst):
    return [{k: str(i.get(k, ""))[:300] for k in ("title", "desc", "url", "icon")} for i in lst][:60]


def clean(d):
    s = d.get("settings", {})
    out = {"settings": {k: s.get(k, v) for k, v in DEFAULT["settings"].items()}, "cards": [], "pages": [], "socials": []}
    for c in d.get("cards", []):
        out["cards"].append({k: str(c.get(k, ""))[:300] for k in ("title", "badge", "icon", "url")})
    for p in d.get("pages", []):
        x = {k: str(p.get(k, ""))[:300] for k in ("title", "password", "build", "start")}
        x["id"] = re.sub(r"[^a-z0-9_-]", "", str(p.get("id", "")).lower())[:40] or uuid.uuid4().hex[:6]
        x["color"] = bool(p.get("color"))
        x["items"] = clean_items(p.get("items", []))
        out["pages"].append(x)
    for c in d.get("socials", []):
        out["socials"].append({k: str(c.get(k, ""))[:300] for k in ("title", "handle", "icon", "url", "img")})
    return out


def page(t, **kw):
    t = t.replace("__CSS__", CSS + kw.pop("extra", "")).replace("__ICONS__", json.dumps(ICONS))
    for k, v in kw.items():
        t = t.replace(k, v)
    return t


def need():
    if not session.get("ok"):
        abort(401)


@app.route("/")
def index():
    return page(PUB, extra=PUB_CSS, __TITLE__=html.escape(load()["settings"]["title"]))


@app.route("/api/data")
def api_data():
    d = load()
    for p in d["pages"]:
        p["locked"] = bool(p["password"])
        p["password"] = ""
        if p["locked"]:
            p["items"] = []
    return jsonify(d)


@app.route("/api/admin-data")
def api_admin_data():
    need()
    return jsonify(load())


@app.route("/api/unlock", methods=["POST"])
def api_unlock():
    j = request.get_json(force=True)
    for p in load()["pages"]:
        if p["id"] == j.get("id") and p["password"] and hmac.compare_digest(p["password"].encode(), str(j.get("pw", "")).encode()):
            return jsonify(items=p["items"])
    return jsonify(error="wrong"), 403


@app.route("/uploads/<path:f>")
def uploads(f):
    return send_from_directory(UP, f)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    err = ""
    if request.method == "POST":
        ok = hmac.compare_digest(request.form.get("u", "").encode(), USER.encode()) and hmac.compare_digest(request.form.get("p", "").encode(), PASS.encode())
        if ok:
            session["ok"] = True
        else:
            err = "Wrong username or password"
    if session.get("ok"):
        return page(ADM, extra=ADM_CSS)
    return page(LOGIN, extra=ADM_CSS, __ERR__=err)


@app.route("/admin/logout")
def logout():
    session.clear()
    return "", 302, {"Location": "/admin"}


@app.route("/api/save", methods=["POST"])
def api_save():
    need()
    data = clean(request.get_json(force=True))
    with lock:
        with open(DB, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
    return jsonify(ok=True)


@app.route("/api/upload", methods=["POST"])
def api_upload():
    need()
    f = request.files.get("file")
    ext = (f.filename.rsplit(".", 1)[-1].lower() if f and "." in f.filename else "")
    if ext not in {"png", "jpg", "jpeg", "gif", "webp", "ico"}:
        return jsonify(error="Only png, jpg, gif, webp, ico allowed"), 400
    name = uuid.uuid4().hex[:12] + "." + ext
    f.save(os.path.join(UP, name))
    return jsonify(url="/uploads/" + name)


@app.route("/api/files")
def api_files():
    need()
    fs = sorted(os.listdir(UP), key=lambda n: os.path.getmtime(os.path.join(UP, n)), reverse=True)
    return jsonify(["/uploads/" + n for n in fs])


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
