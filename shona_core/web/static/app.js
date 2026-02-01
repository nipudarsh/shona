const $ = (id) => document.getElementById(id);

function setMood(sev){
  const mood = (sev || "CALM").toUpperCase();
  $("mood").textContent = mood;

  const dot = $("dot");
  if(mood === "HIGH"){
    dot.style.background = "var(--red)";
    dot.style.boxShadow = "0 0 18px rgba(255,92,122,0.55)";
  } else if(mood === "MEDIUM"){
    dot.style.background = "var(--amber)";
    dot.style.boxShadow = "0 0 18px rgba(255,214,107,0.45)";
  } else {
    dot.style.background = "var(--mint)";
    dot.style.boxShadow = "0 0 18px rgba(98,255,182,0.55)";
  }
}

function out(obj){
  $("out").textContent = JSON.stringify(obj, null, 2);
}

function appendBubble(who, text){
  const box = $("chatbox");
  const wrap = document.createElement("div");
  wrap.className = `bubble ${who}`;
  wrap.innerHTML = `
    <div class="name">${who === "user" ? "YOU" : "SHONA"}</div>
    <div class="msg"></div>
  `;
  wrap.querySelector(".msg").textContent = text;
  box.appendChild(wrap);
  box.scrollTop = box.scrollHeight;
}

async function j(url, opts){
  const r = await fetch(url, opts);
  return await r.json();
}

async function friendline(){
  const data = await j("/api/friendline");
  const lines = data.lines || [];
  const pick = lines[Math.floor(Math.random()*Math.max(1,lines.length))] || "I’m here.";
  $("friendline").textContent = pick;
}

async function doScan(){
  appendBubble("user", "scan");
  setMood("WATCHING");
  const data = await j("/api/scan", {method:"POST"});
  appendBubble("shona", "Snapshot saved. Want a diff?");
  out(data);
  setMood("CALM");
}

async function doDiff(){
  appendBubble("user", "diff");
  const data = await j("/api/diff");
  out(data);
  const sev = (data.risk && data.risk.severity) ? data.risk.severity : "low";

  if(sev === "high"){
    appendBubble("shona", "Something looks risky. I can explain the changes if you want.");
  } else if(sev === "medium"){
    appendBubble("shona", "A few things changed. Probably normal, but worth a look.");
  } else {
    appendBubble("shona", "All calm. No meaningful changes detected.");
  }
  setMood(sev.toUpperCase());
}

async function loadPs(){
  appendBubble("user", "ps");
  const data = await j("/api/ps?limit=40");
  out(data);
  appendBubble("shona", "Here are the running processes (top slice).");
  setMood("CALM");
}

async function loadPorts(){
  appendBubble("user", "ports");
  const data = await j("/api/ports");
  out(data);
  appendBubble("shona", "Here are listening ports. New unexpected ports can matter.");
  setMood("CALM");
}

async function send(){
  const q = $("q").value.trim();
  if(!q) return;
  $("q").value = "";
  const cmd = q.toLowerCase();

  appendBubble("user", q);

  if(cmd === "scan") return doScan();
  if(cmd === "diff") return doDiff();
  if(cmd === "ports") return loadPorts();
  if(cmd === "ps" || cmd === "processes") return loadPs();

  appendBubble("shona", "I can run: scan, diff, ports, ps. (Web UI v0.1.1)");
}

async function copyOut(){
  const text = $("out").textContent || "";
  await navigator.clipboard.writeText(text);
  appendBubble("shona", "Copied.");
}

function clearOut(){
  $("out").textContent = "{}";
  appendBubble("shona", "Cleared.");
}

document.addEventListener("keydown", (e)=>{
  if(e.key === "Enter" && document.activeElement === $("q")){
    send();
  }
});

friendline();
setMood("CALM");
