async function j(url, opts){
  const r = await fetch(url, opts);
  return await r.json();
}

function setMood(text){
  document.getElementById("mood").textContent = text;
}

function out(obj){
  document.getElementById("out").textContent = JSON.stringify(obj, null, 2);
}

async function friendline(){
  const data = await j("/api/friendline");
  const lines = data.lines || [];
  const pick = lines[Math.floor(Math.random()*Math.max(1,lines.length))] || "I’m here.";
  document.getElementById("friendline").textContent = pick;
}

async function doScan(){
  setMood("WATCHING");
  const data = await j("/api/scan", {method:"POST"});
  out(data);
  setMood("CALM");
}

async function doDiff(){
  const data = await j("/api/diff");
  out(data);
  const sev = (data.risk && data.risk.severity) ? data.risk.severity.toUpperCase() : "CALM";
  setMood(sev);
}

async function loadPs(){
  const data = await j("/api/ps?limit=40");
  out(data);
  setMood("CALM");
}

async function loadPorts(){
  const data = await j("/api/ports");
  out(data);
  setMood("CALM");
}

friendline();
