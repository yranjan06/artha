import os, json
import gradio as gr
from dotenv import load_dotenv
load_dotenv()

from utils.audio import process_audio
from stt import transcribe
from tts import speak
from intent import classify
from memory import load_memory, save_memory
from agent import agent_turn, sync_memory, build_system_prompt
from llm import call_llm_simple
from ledger import load_ledger

DEFAULT_USER = "default"

ORB = """<iframe srcdoc='<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:100%;height:460px;background:#080808;font-family:"Courier New",monospace;overflow:hidden;display:flex;flex-direction:column}
nav{height:56px;border-bottom:1px solid #1a1a1a;display:flex;align-items:center;justify-content:space-between;padding:0 32px;flex-shrink:0}
.logo{font-size:18px;font-weight:700;color:#f0f0ee;letter-spacing:.14em}.logo em{color:#cc2200;font-style:normal}
.pill{font-size:9px;padding:4px 14px;border-radius:20px;background:#160500;color:#cc2200;border:1px solid #3a0d00;letter-spacing:.12em;text-transform:uppercase}
.hero{flex:1;display:flex;align-items:center;justify-content:center}
canvas{display:block}
.bottom{height:64px;border-top:1px solid #1a1a1a;display:grid;grid-template-columns:1fr 1fr 1fr;flex-shrink:0}
.stat{display:flex;flex-direction:column;align-items:center;justify-content:center;border-right:1px solid #1a1a1a}
.stat:last-child{border-right:none}
.sn{font-size:22px;font-weight:700;color:#cc2200;letter-spacing:-.02em}
.sl{font-size:8px;color:#3a3a38;letter-spacing:.12em;text-transform:uppercase;margin-top:2px}
</style></head><body>
<nav><div class="logo">AR<em>TH</em>A</div><span class="pill">voice finance agent</span></nav>
<div class="hero"><canvas id="c" width="300" height="300"></canvas></div>
<div class="bottom">
  <div class="stat"><div class="sn">RAW</div><div class="sl">no frameworks</div></div>
  <div class="stat"><div class="sn">5</div><div class="sl">finance tools</div></div>
  <div class="stat"><div class="sn">∞</div><div class="sl">session memory</div></div>
</div>
<script>
const cv=document.getElementById("c"),ctx=cv.getContext("2d");
const R="#cc2200",W=300,CX=W/2,CY=W/2;
const FONT={
  A:[[0,0,1,0,0],[0,1,0,1,0],[1,0,0,0,1],[1,1,1,1,1],[1,0,0,0,1],[1,0,0,0,1]],
  R:[[1,1,1,0,0],[1,0,0,1,0],[1,1,1,0,0],[1,0,1,0,0],[1,0,0,1,0],[1,0,0,0,1]],
  T:[[1,1,1,1,1],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0],[0,0,1,0,0]],
  H:[[1,0,0,0,1],[1,0,0,0,1],[1,1,1,1,1],[1,0,0,0,1],[1,0,0,0,1],[1,0,0,0,1]]
};
const WORD="ARTHA".split(""),ST=7,GW=5*ST,GAP=6;
const TW=WORD.length*GW+(WORD.length-1)*GAP,TH=6*ST;
const TX=CX-TW/2,TY=CY-TH/2;
let state="idle",t=0;
const RINGS=[{r:110,n:44,s:1.5},{r:88,n:34,s:2},{r:66,n:24,s:2.6},{r:44,n:14,s:3.2}];

function draw(){
  ctx.clearRect(0,0,W,W);
  ctx.fillStyle="#080808";ctx.fillRect(0,0,W,W);

  // glow
  const gr2=ctx.createRadialGradient(CX,CY,30,CX,CY,130);
  const ga=state==="idle"?.06:.14+.06*Math.sin(t*.07);
  gr2.addColorStop(0,"rgba(204,34,0,0)");
  gr2.addColorStop(.5,"rgba(204,34,0,"+ga+")");
  gr2.addColorStop(1,"rgba(204,34,0,0)");
  ctx.beginPath();ctx.arc(CX,CY,130,0,Math.PI*2);ctx.fillStyle=gr2;ctx.fill();

  // rings
  RINGS.forEach((ring,ri)=>{
    for(let i=0;i<ring.n;i++){
      const a=(i/ring.n)*Math.PI*2;
      const px=CX+Math.cos(a)*ring.r,py=CY+Math.sin(a)*ring.r;
      let al=.08+.03*Math.sin(t*.02+ri*.8);
      if(state==="listening"){const w=Math.sin(t*.15-ri*1.4-i*.2);al=.08+.5*Math.max(0,w);}
      else if(state==="thinking"){const sw=(t*.05)%(Math.PI*2),da=((a-sw)%(Math.PI*2)+Math.PI*2)%(Math.PI*2);al=.08+(da<1.1?.45*(1-da/1.1):0);}
      else if(state==="speaking"){const p=Math.sin(t*.12+ri*.9);al=.08+.38*Math.max(0,p);}
      ctx.globalAlpha=Math.min(1,al);
      ctx.beginPath();ctx.arc(px,py,ring.s,0,Math.PI*2);ctx.fillStyle=R;ctx.fill();
    }
  });
  ctx.globalAlpha=1;

  // center fill
  const cg=ctx.createRadialGradient(CX,CY,0,CX,CY,32);
  cg.addColorStop(0,"#1c0600");cg.addColorStop(1,"rgba(8,3,0,0)");
  ctx.beginPath();ctx.arc(CX,CY,32,0,Math.PI*2);ctx.fillStyle=cg;ctx.fill();

  // ARTHA letters
  const la=state==="idle"?.6:.85+.12*Math.sin(t*.06);
  WORD.forEach((ch,ci)=>{
    const rows=FONT[ch]||FONT.A;
    const cx2=TX+ci*(GW+GAP);
    rows.forEach((row,ry)=>{row.forEach((px,rx)=>{
      if(!px)return;
      const x=cx2+rx*ST+ST/2,y=TY+ry*ST+ST/2;
      ctx.globalAlpha=la;
      ctx.beginPath();ctx.arc(x,y,ST*.4,0,Math.PI*2);
      ctx.fillStyle=R;ctx.fill();
    });});
  });
  ctx.globalAlpha=1;
  t++;requestAnimationFrame(draw);
}
draw();
window.addEventListener("message",e=>{if(e.data&&e.data.s)state=e.data.s;});
</script></body></html>'
style="width:100%;height:460px;border:none;background:#080808;display:block" scrolling="no"></iframe>"""

CSS = """
* { box-sizing: border-box; }
body, .gradio-container {
    background: #080808 !important;
    font-family: "Courier New", monospace !important;
    color: #f0f0ee !important;
}
/* tabs */
.gradio-container .tabs { background: #080808 !important; }
.gradio-container .tab-nav { background: #080808 !important; border-bottom: 1px solid #1a1a1a !important; padding: 0 24px !important; }
.gradio-container .tab-nav button { color: #404040 !important; font-family: "Courier New", monospace !important; font-size: 11px !important; letter-spacing: .14em !important; text-transform: uppercase !important; border: none !important; background: transparent !important; padding: 14px 20px !important; border-bottom: 2px solid transparent !important; }
.gradio-container .tab-nav button.selected { color: #cc2200 !important; border-bottom: 2px solid #cc2200 !important; }
/* labels */
.gradio-container label span { font-size: 10px !important; letter-spacing: .16em !important; text-transform: uppercase !important; color: #404040 !important; font-family: "Courier New", monospace !important; }
/* inputs */
.gradio-container textarea { background: #111 !important; color: #f0f0ee !important; font-family: "Courier New", monospace !important; font-size: 15px !important; line-height: 1.6 !important; border: 1px solid #222 !important; border-radius: 6px !important; }
.gradio-container textarea:focus { border-color: #3a0d00 !important; outline: none !important; }
/* audio */
.gradio-container .audio-container, .gradio-container audio { background: #111 !important; border: 1px solid #222 !important; border-radius: 6px !important; }
/* chatbot */
.gradio-container .message { font-family: "Courier New", monospace !important; font-size: 14px !important; line-height: 1.7 !important; }
.gradio-container .message.user { background: #111 !important; border: 1px solid #222 !important; border-radius: 10px 10px 2px 10px !important; }
.gradio-container .message.bot { background: #110500 !important; border: 1px solid #2a0a00 !important; border-radius: 10px 10px 10px 2px !important; color: #f0d8c8 !important; }
/* status box */
#artha-status textarea { color: #cc2200 !important; background: transparent !important; border: none !important; font-size: 13px !important; letter-spacing: .05em !important; }
/* call buttons */
#call-btn { background: #050f05 !important; color: #00dd55 !important; border: 1px solid #1a4a1a !important; border-radius: 6px !important; font-family: "Courier New", monospace !important; font-size: 13px !important; letter-spacing: .16em !important; text-transform: uppercase !important; font-weight: 700 !important; }
#call-btn:hover { background: #071507 !important; border-color: #00dd55 !important; box-shadow: 0 0 20px rgba(0,221,85,.15) !important; }
#end-btn { background: #0f0303 !important; color: #cc2200 !important; border: 1px solid #3a0d00 !important; border-radius: 6px !important; font-family: "Courier New", monospace !important; font-size: 13px !important; letter-spacing: .16em !important; text-transform: uppercase !important; font-weight: 700 !important; }
#end-btn:hover { background: #1a0505 !important; border-color: #cc2200 !important; box-shadow: 0 0 20px rgba(204,34,0,.15) !important; }
/* section dividers */
.sec-hdr { font-size: 10px !important; color: #333330 !important; letter-spacing: .18em !important; text-transform: uppercase !important; padding: 20px 0 10px !important; font-family: "Courier New", monospace !important; }
.sec-hdr em { color: #5a1500 !important; font-style: normal !important; }
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: #080808; }
::-webkit-scrollbar-thumb { background: #2a2a2a; }
"""


def process_voice(audio_path, history, user_id):
    if audio_path is None:
        return history, "", "", None
    processed = process_audio(audio_path)
    if not processed:
        return history, "Audio processing failed.", "", None
    text = transcribe(processed)
    if not text:
        return history, "Could not understand.", "", None
    print(f"\n[USER] {text}")
    memory = load_memory(user_id)
    intent = classify(text)
    print(f"[INTENT] {intent}")
    messages = [{"role": "user", "content": text}]
    if intent == "finance":
        reply = agent_turn(messages, memory, user_id)
    else:
        reply = call_llm_simple([
            {"role": "system", "content": build_system_prompt(memory)},
            {"role": "user", "content": text}
        ])
    if not reply:
        reply = "Kuch problem aa gayi — dobara try karo."
    print(f"[ARTHA] {reply}")
    audio_out = speak(reply)
    history = history or []
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})
    return history, text, reply, audio_out


def end_session(history, user_id):
    memory = load_memory(user_id)
    messages = [{"role": m["role"], "content": m["content"]} for m in (history or [])]
    if messages:
        memory = sync_memory(memory, messages)
        save_memory(user_id, memory)
    return [], "", "", None, "Session ended — memory saved."


def on_load(user_id):
    memory = load_memory(user_id)
    if not memory.user_profile:
        return "Ready. Tell me your name and monthly income to begin."
    name = memory.user_profile.get("name", "")
    return f"Welcome back{', ' + name if name else ''}."


def get_memory_log(user_id):
    m = load_memory(user_id)
    lines = ["PROFILE", "-------"]
    for k, v in m.user_profile.items():
        lines.append(f"  {k}: {v}")
    lines += ["", "SUMMARY", "-------", f"  {m.summary or 'none'}"]
    lines += ["", "GOALS", "-----"]
    for g in m.goals:
        lines.append(f"  {g}")
    lines += ["", "COMMITMENTS", "-----------"]
    for c in m.commitments:
        lines.append(f"  {c}")
    lines += ["", "PATTERNS", "--------"]
    for p in m.observed_patterns:
        lines.append(f"  {p}")
    lines.append(f"\nLast updated: {m.last_updated or 'never'}")
    return "\n".join(lines)


def get_ledger_log(user_id):
    ledger = load_ledger(user_id)
    if not ledger:
        return "No transactions yet."
    lines = [f"{'DATE':<13} {'AMOUNT':>10}  CATEGORY         NOTE", "-"*60]
    for tx in reversed(ledger[-50:]):
        amt = tx.get("amount", 0)
        lines.append(f"{tx.get('date','?'):<13} {'+' if amt>=0 else ''}{amt:>9}  {tx.get('category','?'):<16} {tx.get('note','')}")
    return "\n".join(lines)


AUTO_JS = """<script>
(function(){
  let on=false;
  document.addEventListener('click',e=>{
    if(e.target.closest('#call-btn'))on=true;
    if(e.target.closest('#end-btn'))on=false;
  });
  const obs=new MutationObserver(()=>{
    if(!on)return;
    const ao=document.querySelector('#artha-audio audio');
    if(ao&&!ao._wired){ao._wired=true;ao.addEventListener('ended',()=>{
      if(!on)return;
      setTimeout(()=>{
        const rec=document.querySelector('#mic-in button[aria-label="Record from microphone"]');
        if(rec&&on)rec.click();
      },500);
    });}
  });
  obs.observe(document.body,{childList:true,subtree:true});
})();
</script>"""


with gr.Blocks(title="Artha") as demo:
    user_id = gr.State(DEFAULT_USER)
    history = gr.State([])

    gr.HTML(ORB)

    with gr.Tabs():

        with gr.Tab("Conversation"):
            status_msg = gr.Textbox(
                label="Status",
                interactive=False,
                elem_id="artha-status",
                value="Initializing...",
                lines=1,
            )

            with gr.Row(equal_height=True):
                call_btn = gr.Button("Call", size="lg", elem_id="call-btn")
                end_btn  = gr.Button("End Call", size="lg", elem_id="end-btn")

            audio_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="Speak",
                visible=False,
                elem_id="mic-in",
            )

            audio_output = gr.Audio(
                label="Artha Response",
                autoplay=True,
                elem_id="artha-audio",
            )

            with gr.Row():
                transcription = gr.Textbox(label="You said", interactive=False, lines=3)
                reply_box     = gr.Textbox(label="Artha replied", interactive=False, lines=3)

            chatbox = gr.Chatbot(label="Conversation", height=320)

            gr.HTML(AUTO_JS)

            call_btn.click(fn=lambda: gr.update(visible=True), outputs=[audio_input])
            end_btn.click(
                fn=end_session,
                inputs=[history, user_id],
                outputs=[chatbox, transcription, reply_box, audio_output, status_msg],
            ).then(fn=lambda: gr.update(visible=False), outputs=[audio_input])

            audio_input.stop_recording(
                fn=process_voice,
                inputs=[audio_input, history, user_id],
                outputs=[chatbox, transcription, reply_box, audio_output],
            )

        with gr.Tab("Memory"):
            gr.Button("Refresh", size="sm").click(
                fn=get_memory_log, inputs=[user_id],
                outputs=[gr.Textbox(label="Memory State", lines=24, interactive=False)]
            )

        with gr.Tab("Transactions"):
            gr.Button("Refresh", size="sm").click(
                fn=get_ledger_log, inputs=[user_id],
                outputs=[gr.Textbox(label="Transaction Log", lines=24, interactive=False)]
            )

    demo.load(fn=on_load, inputs=[user_id], outputs=[status_msg])

if __name__ == "__main__":
    demo.launch(css=CSS)