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
async function maybeSpeak(text){
  try{
    const s = await j("/api/settings");
    const cfg = (s.settings || {});
    if(!cfg.voice_enabled) return;
    await j("/api/say", {
      method:"POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({text})
    });
  }catch(e){}
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

async function runCmd(text){
  const data = await j("/api/command", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({text})
  });
  out(data);

  if(data.kind === "diff" && data.data && data.data.risk){
    const sev = (data.data.risk.severity || "low").toUpperCase();
    setMood(sev);
  } else {
    setMood("CALM");
  }

  if(data.say) appendBubble("shona", data.say);
  if(data.say) await maybeSpeak(data.say);

}

async function doScan(){ appendBubble("user","scan"); await runCmd("scan"); }
async function doDiff(){ appendBubble("user","diff"); await runCmd("diff"); }
async function loadPorts(){ appendBubble("user","ports"); await runCmd("ports"); }
async function loadPs(){ appendBubble("user","ps"); await runCmd("ps 40"); }

async function send(){
  const q = $("q").value.trim();
  if(!q) return;
  $("q").value = "";
  appendBubble("user", q);
  await runCmd(q);
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
