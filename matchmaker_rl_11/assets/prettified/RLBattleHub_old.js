import{
g as Q,
r as l,
j as e,
Z as ve,
_ as ye,
$ as Ne,
a0 as we,
a2 as ke,
Y as Ue,
a1 as We,
v as Se,
R as U,
bb as Oe}
from"./vendor-react-core-Jcgh_-Ou.js";
import{
k as Ce,
l as Z,
W as Ke,
m as Qe,
n as ue,
o as oe,
p as Ge,
q as Ye,
r as Ee,
s as Ze,
t as Je,
R as K,
P as Xe,
v as et,
a as J,
w as tt,
x as be,
y as he,
c as ne,
G as re,
z as st,
A as rt,
B as at,
D as lt,
E as nt}
from"./index-CP74E0-C.js";
import{
a as ot,
T as it}
from"./TeamLeaderboard-34mKLlEj.js";
import{
T as ct}
from"./TeamEmblem-Bzth-1q5.js";
import{
G as fe}
from"./GameAuthOverlay-rB8tiWfP.js";
import"./vendor-three-CaO7CK4H.js";
import"./vendor-i18n-Ckwewb-z.js";
import"./vendor-rapier-DW2HfIcf.js";
const dt=({
stats:t}
)=>e.jsx(ve,
{
width:"100%",
height:"100%",
children:e.jsxs(ye,
{
cx:"50%",
cy:"50%",
outerRadius:"72%",
data:t,
children:[e.jsx(Ne,
{
stroke:"#78350f33"}
),
e.jsx(we,
{
dataKey:"subject",
tick:{
fill:"#92400e",
fontSize:8,
fontFamily:"monospace",
fontWeight:"bold"}
}
),
e.jsx(ke,
{
dataKey:"value",
stroke:"#d97706",
fill:"#d97706",
fillOpacity:.3}
)]}
)}
),
xt=({
slot:t,
slotIndex:x,
onUploadClick:r,
onDeleteClick:o,
onEditClick:C,
onStatsClick:v,
onSetAutoBattle:a,
sandboxLimits:N,
sandboxPackages:p}
)=>{
const{
t:i}
=Q(),
[u,
w]=l.useState(!1),
[E,
m]=l.useState(null),
[b,
h]=l.useState(!1),
[B,
$]=l.useState(!1);
l.useEffect(()=>{
t&&(h(!0),
Ce(t.competition_id,
t.slot_index).then(d=>m(d.stats)).catch(()=>m(null)).finally(()=>h(!1)))}
,
[t]);
const c=()=>{
Z.playClick(),
u&&t?(o(x,
t.name),
w(!1)):w(!0)}
,
n=()=>{
Z.playClick(),
w(!1)}
,
f=d=>new Date(d).toLocaleDateString("zh-TW",
{
year:"numeric",
month:"short",
day:"numeric"}
),
g=(d,
y=24)=>{
if(d.length<=y)return d;
const j=d.slice(d.lastIndexOf("."));
return`${
d.slice(0,
y-j.length-3)}
...${
j}
`}
;
return t===null?e.jsxs("div",
{
onClick:()=>{
r(x),
Z.playClick()}
,
onKeyDown:d=>{
(d.key==="Enter"||d.key===" ")&&(d.preventDefault(),
r(x))}
,
role:"button",
tabIndex:0,
className:"flex flex-col items-center justify-center gap-4 border-2 border-dashed border-stone-850 bg-stone-900/10 p-5 min-h-[200px] rounded-[4px] relative overflow-hidden group transition-all duration-300 hover:border-amber-600/70 hover:bg-stone-900/40 hover:shadow-[0_0_20px_rgba(217,
119,
6,
0.1)] shadow-lg cursor-pointer outline-none focus-visible:ring-1 focus-visible:ring-amber-500",
children:[e.jsx("div",
{
className:"absolute inset-0 bg-radial-gradient from-transparent to-black/60 pointer-events-none"}
),
e.jsx("span",
{
className:"font-epic text-[10px] text-stone-500 tracking-widest uppercase z-10 transition-colors duration-300 group-hover:text-stone-300",
children:i("rl.slot.empty_title",
{
index:x}
)}
),
e.jsx("div",
{
className:"w-12 h-12 flex items-center justify-center rounded-full border border-stone-850 bg-stone-950/60 relative z-10 transition-all duration-300 group-hover:scale-110 group-hover:border-amber-600 group-hover:shadow-[0_0_12px_rgba(217,
119,
6,
0.25)]",
children:e.jsx("svg",
{
className:"w-5 h-5 text-stone-600 group-hover:text-amber-500 transition-all duration-300 group-hover:rotate-45",
fill:"none",
viewBox:"0 0 24 24",
stroke:"currentColor",
children:e.jsx("path",
{
strokeLinecap:"round",
strokeLinejoin:"round",
strokeWidth:1.5,
d:"M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"}
)}
)}
),
e.jsx("div",
{
className:"z-10 px-4 py-2 bg-stone-800 text-stone-300 font-epic text-xs uppercase tracking-wider border border-stone-700 shadow-md transition-all duration-300 font-bold group-hover:bg-amber-600 group-hover:text-[#1A120B] group-hover:border-amber-500 group-hover:shadow-[0_0_12px_rgba(217,
119,
6,
0.15)]",
children:i("rl.slot.configure")}
),
N&&e.jsxs("div",
{
className:"z-10 flex items-center gap-3 text-stone-500 font-epic text-[9px] uppercase tracking-wider",
children:[e.jsx("span",
{
children:i("rl.slot.sandbox_limits")}
),
e.jsxs("span",
{
children:["📦 ",
i("rl.slot.limit_memory",
{
value:N.memory_mb}
)]}
),
e.jsxs("span",
{
children:["⏱ ",
i("rl.slot.limit_timeout",
{
value:N.timeout_sec}
)]}
)]}
),
p!=null&&e.jsxs("div",
{
className:"z-10 w-full px-2",
children:[e.jsx("button",
{
onClick:d=>{
d.stopPropagation(),
$(y=>!y)}
,
className:"font-epic text-[9px] text-stone-500 hover:text-stone-300 transition-colors uppercase tracking-wider",
children:i(B?"rl.slot.packages_collapse":"rl.slot.packages_expand")}
),
B&&e.jsx("div",
{
className:"mt-1 flex flex-wrap gap-1",
children:p.length===0?e.jsx("span",
{
className:"font-epic text-[9px] text-stone-600",
children:i("rl.slot.packages_custom_image")}
):p.map(d=>e.jsx("span",
{
className:"font-mono text-[9px] px-1.5 py-0.5 bg-stone-900/60 border border-stone-700 text-stone-400 rounded-sm",
children:d}
,
d))}
)]}
)]}
):e.jsxs("div",
{
className:"flex flex-col gap-2 rpg-parchment-card p-4 sm:p-5 rounded-[4px] relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl",
children:[e.jsx("div",
{
className:"absolute top-1.5 left-1.5 w-1 h-1 bg-[#5c3c1e] rounded-full shadow-[1px_1px_0_rgba(255,
255,
255,
0.2)]"}
),
e.jsx("div",
{
className:"absolute top-1.5 right-1.5 w-1 h-1 bg-[#5c3c1e] rounded-full shadow-[1px_1px_0_rgba(255,
255,
255,
0.2)]"}
),
e.jsx("div",
{
className:"absolute bottom-1.5 left-1.5 w-1 h-1 bg-[#5c3c1e] rounded-full shadow-[1px_1px_0_rgba(255,
255,
255,
0.2)]"}
),
e.jsx("div",
{
className:"absolute bottom-1.5 right-1.5 w-1 h-1 bg-[#5c3c1e] rounded-full shadow-[1px_1px_0_rgba(255,
255,
255,
0.2)]"}
),
e.jsxs("div",
{
className:"flex items-center gap-2 border-b border-[#78350F]/20 pb-2",
children:[e.jsx("span",
{
className:"bg-[#78350F]/10 border border-[#78350F]/30 px-2 py-0.5 font-epic text-[10px] text-[#5c3c1e] uppercase tracking-wider whitespace-nowrap",
children:i("rl.slot.active_slot",
{
index:x}
)}
),
t.is_auto_battle&&e.jsx("span",
{
className:"bg-amber-500/20 border border-amber-500/60 px-1.5 py-0.5 font-epic text-[9px] text-amber-700 uppercase tracking-wider whitespace-nowrap",
title:i("rl.slot.auto_battle_active",
{
defaultValue:"指定自動出戰"}
),
children:"⚡ 自動"}
),
e.jsx("h3",
{
className:"font-epic text-xs sm:text-sm text-[#2B2017] truncate flex-1 tracking-wide",
title:t.name,
children:t.name}
),
e.jsxs("span",
{
className:"relative flex h-2 w-2 shrink-0",
title:i("rl.slot.live_status"),
children:[e.jsx("span",
{
className:"animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-500 opacity-75"}
),
e.jsx("span",
{
className:"relative inline-flex rounded-full h-2 w-2 bg-emerald-600"}
)]}
)]}
),
e.jsx("div",
{
onClick:()=>{
v&&(v(t),
Z.playClick())}
,
onKeyDown:d=>{
(d.key==="Enter"||d.key===" ")&&(d.preventDefault(),
v&&v(t))}
,
role:"button",
tabIndex:0,
title:i("rl.slot.click_stats",
{
defaultValue:"點擊查看詳細分析"}
),
className:"h-36 w-full cursor-pointer rounded relative group/radar outline-none focus-visible:ring-1 focus-visible:ring-amber-500/50 transition-opacity duration-200 hover:opacity-90",
children:b?e.jsx("div",
{
className:"h-full flex items-center justify-center",
children:e.jsx("div",
{
className:"w-5 h-5 rounded-full border-2 border-stone-700 border-t-amber-500 animate-spin"}
)}
):E&&E.length>0?e.jsxs(e.Fragment,
{
children:[e.jsx(dt,
{
stats:E}
),
e.jsx("span",
{
className:"absolute bottom-0 right-1 opacity-0 group-hover/radar:opacity-100 transition-opacity text-[8px] font-epic text-[#78350F]/60 uppercase tracking-widest pointer-events-none",
children:i("rl.slot.view_agent_stats",
{
defaultValue:"詳細分析"}
)}
)]}
):e.jsxs("div",
{
className:"h-full flex flex-col items-center justify-center gap-1 text-[#5c3c1e]/40",
children:[e.jsx("svg",
{
className:"w-6 h-6",
fill:"none",
viewBox:"0 0 24 24",
stroke:"currentColor",
children:e.jsx("path",
{
strokeLinecap:"round",
strokeLinejoin:"round",
strokeWidth:1,
d:"M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"}
)}
),
e.jsx("span",
{
className:"font-epic text-[9px] uppercase tracking-wider",
children:i("rl.slot.no_battles_yet",
{
defaultValue:"尚無對戰紀錄"}
)}
)]}
)}
),
e.jsxs("div",
{
className:"flex flex-col gap-1 border-t border-[#78350F]/20 pt-2 text-[#2B2017]/80",
children:[t.description&&e.jsxs("p",
{
className:"font-parchment text-xs italic leading-relaxed line-clamp-2",
children:["「 ",
t.description,
" 」"]}
),
t.weights_filename&&e.jsx("p",
{
className:"font-mono text-[10px] text-[#5c3c1e]/85 truncate",
title:t.weights_filename,
children:i("rl.slot.weights",
{
name:g(t.weights_filename)}
)}
),
e.jsx("p",
{
className:"font-mono text-[9px] text-[#5c3c1e]/75",
children:i("rl.slot.uploaded_at",
{
date:f(t.created_at)}
)}
)]}
),
N&&e.jsxs("div",
{
className:"flex flex-col gap-1 pt-1 border-t border-[#78350F]/10",
children:[e.jsxs("div",
{
className:"flex items-center gap-3 text-[#5c3c1e]/50 font-epic text-[9px] uppercase tracking-wider",
children:[e.jsx("span",
{
children:i("rl.slot.sandbox_limits")}
),
e.jsxs("span",
{
children:["📦 ",
i("rl.slot.limit_memory",
{
value:N.memory_mb}
)]}
),
e.jsxs("span",
{
children:["⏱ ",
i("rl.slot.limit_timeout",
{
value:N.timeout_sec}
)]}
)]}
),
p!=null&&e.jsxs("div",
{
children:[e.jsx("button",
{
onClick:()=>$(d=>!d),
className:"font-epic text-[9px] text-[#5c3c1e]/40 hover:text-[#5c3c1e]/80 transition-colors uppercase tracking-wider",
children:i(B?"rl.slot.packages_collapse":"rl.slot.packages_expand")}
),
B&&e.jsx("div",
{
className:"mt-1 flex flex-wrap gap-1",
children:p.length===0?e.jsx("span",
{
className:"font-epic text-[9px] text-[#5c3c1e]/40",
children:i("rl.slot.packages_custom_image")}
):p.map(d=>e.jsx("span",
{
className:"font-mono text-[9px] px-1.5 py-0.5 bg-[#78350F]/5 border border-[#78350F]/15 text-[#5c3c1e]/70 rounded-sm",
children:d}
,
d))}
)]}
)]}
),
e.jsxs("div",
{
className:"flex flex-col gap-1.5 pt-1 mt-auto",
children:[a&&e.jsx("button",
{
onClick:()=>{
a(t),
Z.playClick()}
,
title:t.is_auto_battle?i("rl.slot.auto_battle_unset",
{
defaultValue:"取消指定，改為隨機挑選"}
):i("rl.slot.auto_battle_set",
{
defaultValue:"指定此槽位為系統自動出戰代理人"}
),
className:`w-full font-epic text-[10px] py-1.5 px-2 border cursor-pointer transition-all duration-200 uppercase tracking-wider ${
t.is_auto_battle?"bg-amber-500/25 border-amber-500/70 text-amber-700 hover:bg-amber-500/15":"bg-transparent border-[#78350F]/20 text-[#5c3c1e]/60 hover:border-amber-500/50 hover:text-amber-700/80"}
`,
children:t.is_auto_battle?i("rl.slot.auto_battle_active_btn",
{
defaultValue:"⚡ 自動出戰中 · 點擊取消"}
):i("rl.slot.auto_battle_set_btn",
{
defaultValue:"設為自動出戰"}
)}
),
e.jsx("div",
{
className:"flex items-center gap-2",
children:u?e.jsxs(e.Fragment,
{
children:[e.jsx("button",
{
onClick:c,
className:"flex-1 bg-red-800 hover:bg-red-700 text-white font-epic text-xs py-1.5 px-2 border border-red-950 shadow-md cursor-pointer transition-colors font-bold",
children:i("rl.slot.confirm_delete")}
),
e.jsx("button",
{
onClick:n,
className:"flex-1 bg-[#dfceaa] hover:bg-[#d0bd95] text-[#2B2017] font-epic text-xs py-1.5 px-2 border border-[#78350F]/30 shadow-sm cursor-pointer transition-colors",
children:i("rl.slot.cancel")}
)]}
):e.jsxs(e.Fragment,
{
children:[e.jsx("button",
{
onClick:()=>{
C(t),
Z.playClick()}
,
className:"flex-1 bg-[#dfceaa] hover:bg-[#d0bd95] text-[#2B2017] font-epic text-xs py-1.5 px-2 border border-[#78350F]/30 shadow-sm hover:shadow-md cursor-pointer transition-all duration-200",
children:i("rl.slot.edit")}
),
e.jsx("button",
{
onClick:c,
className:"flex-1 bg-transparent hover:bg-red-800/10 text-red-800 font-epic text-xs py-1.5 px-2 border border-red-800/30 hover:border-red-800 shadow-sm cursor-pointer transition-all duration-200",
children:i("rl.slot.delete")}
)]}
)}
)]}
)]}
)}
,
ge="w-full bg-black/40 border border-gray-700 text-rpg-paper px-3 py-2 font-pixel text-sm focus:outline-none focus:border-rpg-gold";
function P(t){
return t<1024*1024?`${
(t/1024).toFixed(0)}
 KB`:`${
(t/(1024*1024)).toFixed(1)}
 MB`}
const pt=({
competitionId:t,
slotIndex:x,
existingSlot:r,
envName:o,
onSuccess:C,
onCancel:v}
)=>{
const{
t:a}
=Q(),
[N,
p]=l.useState(r?.name??""),
[i,
u]=l.useState(r?.description??""),
[w,
E]=l.useState(null),
[m,
b]=l.useState(null),
[h,
B]=l.useState(null),
[$,
c]=l.useState(!1),
[n,
f]=l.useState(null),
g=(o??"").toLowerCase(),
d="mlarena";
let y=["pettingzoo",
"chess",
"pygame",
"stable-baselines3",
"sb3-contrib"];
g.includes("pacman")?y=["gymnasium[atari]",
"ale-py",
"autorom[accept-rom-license]",
"stable-baselines3[extra]",
"shimmy[atari]>=0.2.1"]:g.includes("texas")||g.includes("holdem")||g.includes("poker")?y=["pettingzoo",
"rlcard",
"pygame",
"stable-baselines3",
"sb3-contrib"]:g.includes("chess")?y=["pettingzoo",
"chess",
"pygame",
"stable-baselines3",
"sb3-contrib"]:y=["gymnasium",
"stable-baselines3"];
const j=`name: ${
d}

channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.10
  - pip`,
k=["websockets",
"joblib",
...y].join(`
`),
F=S=>{
navigator.clipboard.writeText(S),
f(S),
setTimeout(()=>f(null),
2e3)}
,
L=({
text:S}
)=>{
const R=n===S;
return e.jsxs("button",
{
type:"button",
onClick:()=>F(S),
className:`transition-all duration-200 active:scale-95 flex items-center gap-1 px-2.5 py-1 text-[10px] rounded cursor-pointer font-epic ${
R?"bg-emerald-950/80 border border-emerald-500/50 text-emerald-400 font-bold shadow-[0_0_8px_rgba(16,
185,
129,
0.2)] animate-success-flash":"bg-stone-900 border border-stone-800 text-stone-300 hover:text-amber-550 hover:border-amber-600/30 shadow-sm opacity-80 hover:opacity-100"}
`,
children:[e.jsx("span",
{
children:R?"✓":"📋"}
),
e.jsx("span",
{
children:a(R?"rl.guide.copied":"rl.guide.copy")}
)]}
)}
,
[H,
T]=l.useState(null),
[I,
W]=l.useState(null),
O=r!==null,
Y=(h?.size??0)>Ke,
D=$?I!==null?a("rl.upload.uploading_weights",
{
progress:I.percent}
):a("rl.upload.uploading"):a(O?"rl.upload.save_changes":"rl.upload.submit"),
ae=async S=>{
if(S.preventDefault(),
T(null),
!N.trim()){
T(a("rl.upload.error_name"));
return}
if(!O&&!w){
T(a("rl.upload.error_agent_required"));
return}
c(!0);
try{
const R=new FormData;
R.append("slot_index",
String(x)),
R.append("name",
N.trim()),
i.trim()&&R.append("description",
i.trim()),
w&&R.append("agent_file",
w),
m&&R.append("model_file",
m);
const A=M=>M<=0?"計算速度中...":M<1024?`${
M.toFixed(0)}
 B/s`:M<1024*1024?`${
(M/1024).toFixed(1)}
 KB/s`:`${
(M/(1024*1024)).toFixed(1)}
 MB/s`;
if(h&&Y){
W({
percent:0,
speed:"0 KB/s",
loaded:"0 MB",
total:P(h.size)}
);
const M=await Qe(t,
h,
z=>{
W({
percent:z.percent,
speed:A(z.speed),
loaded:P(z.loadedBytes),
total:P(z.totalBytes)}
)}
);
R.append("weights_upload_id",
M);
const G=await ue(t,
R);
C(G)}
else{
h&&R.append("weights_file",
h);
const M=(w?.size??0)+(m?.size??0)+(h?.size??0)+1024;
W({
percent:0,
speed:"0 KB/s",
loaded:"0 MB",
total:P(M)}
);
const G=await ue(t,
R,
z=>{
W({
percent:z.percent,
speed:A(z.speed),
loaded:P(z.loadedBytes),
total:P(z.totalBytes)}
)}
);
C(G)}
}
catch(R){
T(oe(R,
a("rl.upload.error_upload")))}
finally{
c(!1),
W(null)}
}
,
X=S=>{
S.target===S.currentTarget&&v()}
;
return e.jsx("div",
{
className:"fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4",
onClick:X,
children:e.jsxs("div",
{
className:"bg-rpg-dark pixel-border w-full max-w-lg max-h-[90vh] overflow-y-auto p-6 flex flex-col gap-5",
children:[e.jsx("h2",
{
className:"font-pixel text-sm text-rpg-gold uppercase tracking-wider",
children:O?a("rl.upload.title_edit",
{
index:x}
):a("rl.upload.title_new",
{
index:x}
)}
),
e.jsxs("form",
{
onSubmit:ae,
className:"flex flex-col gap-4",
children:[e.jsxs("div",
{
className:"flex flex-col gap-1.5",
children:[e.jsxs("label",
{
className:"font-pixel text-xs text-rpg-paper/70 uppercase tracking-wider",
children:[a("rl.upload.name"),
" ",
e.jsx("span",
{
className:"text-red-500",
children:"*"}
)]}
),
e.jsx("input",
{
type:"text",
value:N,
onChange:S=>p(S.target.value),
placeholder:a("rl.upload.name_placeholder"),
className:ge,
disabled:$,
required:!0}
)]}
),
e.jsxs("div",
{
className:"flex flex-col gap-1.5",
children:[e.jsx("label",
{
className:"font-pixel text-xs text-rpg-paper/70 uppercase tracking-wider",
children:a("rl.upload.desc")}
),
e.jsx("textarea",
{
value:i,
onChange:S=>u(S.target.value),
placeholder:a("rl.upload.desc_placeholder"),
rows:3,
className:`${
ge}
 resize-none`,
disabled:$}
)]}
),
e.jsxs("div",
{
className:"flex flex-col gap-1.5",
children:[e.jsxs("label",
{
className:"font-pixel text-xs text-rpg-paper/70 uppercase tracking-wider",
children:["agent.py",
" ",
!O&&e.jsx("span",
{
className:"text-red-500",
children:"*"}
),
O&&e.jsx("span",
{
className:"text-gray-500 normal-case",
children:a("rl.upload.file_optional_update")}
)]}
),
e.jsx("input",
{
type:"file",
accept:".py",
onChange:S=>E(S.target.files?.[0]??null),
className:"font-pixel text-xs text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:border file:border-gray-600 file:bg-black/40 file:text-rpg-gold file:font-pixel file:text-xs file:cursor-pointer hover:file:border-rpg-gold focus:outline-none",
disabled:$}
),
w&&e.jsx("p",
{
className:"font-pixel text-xs text-rpg-grass",
children:a("rl.upload.selected_file",
{
name:w.name,
size:P(w.size)}
)}
)]}
),
e.jsxs("div",
{
className:"flex flex-col gap-1.5",
children:[e.jsxs("label",
{
className:"font-pixel text-xs text-rpg-paper/70 uppercase tracking-wider",
children:["model.py",
" ",
e.jsx("span",
{
className:"text-gray-500 normal-case",
children:a("rl.upload.model_file_desc")}
)]}
),
e.jsx("input",
{
type:"file",
accept:".py",
onChange:S=>b(S.target.files?.[0]??null),
className:"font-pixel text-xs text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:border file:border-gray-600 file:bg-black/40 file:text-rpg-gold file:font-pixel file:text-xs file:cursor-pointer hover:file:border-rpg-gold focus:outline-none",
disabled:$}
),
m&&e.jsx("p",
{
className:"font-pixel text-xs text-rpg-grass",
children:a("rl.upload.selected_file",
{
name:m.name,
size:P(m.size)}
)}
)]}
),
e.jsxs("div",
{
className:"flex flex-col gap-1.5",
children:[e.jsxs("label",
{
className:"font-pixel text-xs text-rpg-paper/70 uppercase tracking-wider",
children:[a("rl.upload.weights_file"),
" ",
e.jsx("span",
{
className:"text-gray-500 normal-case",
children:a("rl.upload.weights_file_desc")}
)]}
),
e.jsx("input",
{
type:"file",
accept:".pth,
.pkl,
.zip,
.h5,
.onnx,
.pt,
.joblib",
onChange:S=>B(S.target.files?.[0]??null),
className:"font-pixel text-xs text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:border file:border-gray-600 file:bg-black/40 file:text-rpg-gold file:font-pixel file:text-xs file:cursor-pointer hover:file:border-rpg-gold focus:outline-none",
disabled:$}
),
h&&e.jsxs("p",
{
className:"font-pixel text-xs text-rpg-grass",
children:[a("rl.upload.selected_file",
{
name:h.name,
size:P(h.size)}
),
Y&&e.jsx("span",
{
className:"text-purple-400 ml-2",
children:a("rl.upload.chunked_upload_hint")}
)]}
),
O&&r.weights_filename&&!h&&e.jsx("p",
{
className:"font-pixel text-xs text-gray-500",
children:a("rl.upload.current_file",
{
name:r.weights_filename}
)}
)]}
),
e.jsxs("details",
{
className:"border border-stone-850 bg-black/40 rounded-[2px] cursor-pointer group",
children:[e.jsxs("summary",
{
className:"font-pixel text-[11px] text-rpg-gold p-2.5 hover:text-rpg-gold/80 select-none flex items-center justify-between",
children:[e.jsxs("span",
{
children:["📖 ",
a("rl.guide.title",
"命令行 (CLI) 開發與環境部署指南")]}
),
e.jsx("span",
{
className:"text-[10px] text-gray-500 group-open:rotate-180 transition-transform",
children:"▼"}
)]}
),
e.jsxs("div",
{
className:"p-3.5 border-t border-stone-850 font-sans text-xs text-stone-300 space-y-4 max-h-[250px] overflow-y-auto bg-black/20 cursor-default",
onClick:S=>S.stopPropagation(),
children:[e.jsxs("div",
{
className:"space-y-2",
children:[e.jsx("h4",
{
className:"font-pixel text-[10px] text-rpg-gold uppercase tracking-wider",
children:a("rl.guide.tab_env")}
),
e.jsx("p",
{
className:"text-gray-400 text-[11px] leading-relaxed",
children:a("rl.guide.env.desc")}
),
e.jsxs("div",
{
className:"p-2 border border-stone-850 bg-stone-900/10 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-rpg-gold font-pixel text-[9px] uppercase tracking-wider block font-bold",
children:a("rl.guide.env.step1_title")}
),
e.jsx("p",
{
className:"text-gray-400 text-[10px] mt-0.5 mb-1.5",
children:a("rl.guide.env.step1_desc")}
),
e.jsxs("div",
{
className:"relative bg-black/80 p-2 rounded border border-stone-850 hover:border-stone-800 transition-colors font-mono text-[10.5px] text-amber-500/90 flex justify-between items-center group",
children:[e.jsx("pre",
{
className:"overflow-x-auto whitespace-pre-wrap select-all pr-4 font-mono",
children:"cd <path_to_extracted_folder>"}
),
e.jsx(L,
{
text:"cd <path_to_extracted_folder>"}
)]}
)]}
),
e.jsxs("div",
{
className:"p-2 border border-stone-850 bg-stone-900/10 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-rpg-gold font-pixel text-[9px] uppercase tracking-wider block font-bold",
children:a("rl.guide.env.step2_title")}
),
e.jsx("p",
{
className:"text-gray-400 text-[10px] mt-0.5 mb-1.5",
children:a("rl.guide.env.step2_desc")}
),
e.jsxs("div",
{
className:"relative bg-black/80 p-2 rounded border border-stone-850 hover:border-stone-800 transition-colors font-mono text-[10.5px] text-amber-500/90 flex justify-between items-center group",
children:[e.jsx("pre",
{
className:"overflow-x-auto whitespace-pre-wrap select-all pr-4 font-mono",
children:"conda env create -f environment.yml"}
),
e.jsx(L,
{
text:"conda env create -f environment.yml"}
)]}
)]}
),
e.jsxs("div",
{
className:"p-2 border border-stone-850 bg-stone-900/10 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-rpg-gold font-pixel text-[9px] uppercase tracking-wider block font-bold",
children:a("rl.guide.env.step3_title")}
),
e.jsx("p",
{
className:"text-gray-400 text-[10px] mt-0.5 mb-1.5",
children:a("rl.guide.env.step3_desc")}
),
e.jsxs("div",
{
className:"relative bg-black/80 p-2 rounded border border-stone-850 hover:border-stone-800 transition-colors font-mono text-[10.5px] text-amber-500/90 flex justify-between items-center group",
children:[e.jsxs("pre",
{
className:"overflow-x-auto whitespace-pre-wrap select-all pr-4 font-mono",
children:["conda activate ",
d]}
),
e.jsx(L,
{
text:`conda activate ${
d}
`}
)]}
)]}
),
e.jsxs("div",
{
className:"p-2 border border-stone-850 bg-stone-900/10 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-rpg-gold font-pixel text-[9px] uppercase tracking-wider block font-bold",
children:a("rl.guide.env.step4_title",
"步驟 4. 安裝依賴套件")}
),
e.jsx("p",
{
className:"text-gray-400 text-[10px] mt-0.5 mb-1.5",
children:a("rl.guide.env.step4_desc",
"在啟用的環境中，透過 pip 一鍵安裝所有必要的依賴庫：")}
),
e.jsxs("div",
{
className:"relative bg-black/80 p-2 rounded border border-stone-850 hover:border-stone-800 transition-colors font-mono text-[10.5px] text-amber-500/90 flex justify-between items-center group",
children:[e.jsx("pre",
{
className:"overflow-x-auto whitespace-pre-wrap select-all pr-4 font-mono",
children:"pip install -r requirements.txt"}
),
e.jsx(L,
{
text:"pip install -r requirements.txt"}
)]}
)]}
),
e.jsxs("details",
{
className:"border border-stone-850 rounded-[2px] bg-stone-950/20 hover:bg-stone-950/40 cursor-pointer group/spec",
children:[e.jsxs("summary",
{
className:"font-pixel text-[9px] text-stone-500 p-2 hover:text-stone-400 select-none flex items-center justify-between",
children:[e.jsx("span",
{
children:a("rl.guide.env.spec_summary")}
),
e.jsx("span",
{
className:"text-[8px] text-stone-600 group-open/spec:rotate-180 transition-transform",
children:"▼"}
)]}
),
e.jsxs("div",
{
className:"p-3 border-t border-stone-850 space-y-3 bg-stone-950/60 rounded-b-[2px]",
children:[e.jsxs("div",
{
children:[e.jsxs("div",
{
className:"flex justify-between items-center mb-1",
children:[e.jsx("span",
{
className:"text-[9px] text-rpg-gold font-pixel",
children:"environment.yml"}
),
e.jsx(L,
{
text:j}
)]}
),
e.jsx("pre",
{
className:"p-2 bg-black/40 border border-stone-850 font-mono text-[9.5px] text-stone-400 overflow-x-auto max-h-[120px] rounded select-all whitespace-pre",
children:j}
)]}
),
e.jsxs("div",
{
children:[e.jsxs("div",
{
className:"flex justify-between items-center mb-1",
children:[e.jsx("span",
{
className:"text-[9px] text-rpg-gold font-pixel",
children:"requirements.txt"}
),
e.jsx(L,
{
text:k}
)]}
),
e.jsx("pre",
{
className:"p-2 bg-black/40 border border-stone-850 font-mono text-[9.5px] text-stone-400 overflow-x-auto max-h-[120px] rounded select-all whitespace-pre",
children:k}
)]}
)]}
)]}
),
e.jsxs("div",
{
className:"p-2 border border-amber-700/50 bg-amber-950/20 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-amber-400 font-pixel text-[9px] uppercase tracking-wider block font-bold mb-1",
children:a("rl.guide.env.student_id_reminder_title")}
),
e.jsx("p",
{
className:"text-amber-200/70 text-[10px] leading-relaxed",
children:a("rl.guide.env.student_id_reminder_desc")}
),
e.jsxs("div",
{
className:"mt-1.5 bg-black/60 p-1.5 rounded border border-amber-700/30 font-mono text-[10px] text-amber-400/80",
children:[e.jsx("span",
{
className:"text-stone-500",
children:"run.py → "}
),
"STUDENT_ID = ",
e.jsx("span",
{
className:"text-red-400 font-bold",
children:'"YOUR_ID"'}
),
e.jsx("span",
{
className:"text-stone-500",
children:"  # ← 改為您的學號"}
)]}
)]}
)]}
),
e.jsxs("div",
{
className:"space-y-2 pt-2 border-t border-stone-850",
children:[e.jsx("h4",
{
className:"font-pixel text-[10px] text-rpg-gold uppercase tracking-wider",
children:a("rl.guide.tab_train")}
),
e.jsx("p",
{
className:"text-gray-400 text-[11px] leading-relaxed",
children:a("rl.guide.train.desc")}
),
e.jsxs("div",
{
className:"p-2 border border-stone-850 bg-stone-900/10 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-rpg-gold font-pixel text-[9px] uppercase tracking-wider block font-bold",
children:a("rl.guide.train.cmd_title")}
),
e.jsxs("div",
{
className:"relative bg-black/80 p-2 rounded border border-stone-850 hover:border-stone-800 transition-colors font-mono text-[10.5px] text-amber-500/90 flex justify-between items-center group mt-1",
children:[e.jsx("pre",
{
className:"overflow-x-auto whitespace-pre-wrap select-all pr-4 font-mono",
children:"python train.py"}
),
e.jsx(L,
{
text:"python train.py"}
)]}
),
e.jsx("p",
{
className:"text-stone-500 text-[9px] mt-1.5 italic",
children:a("rl.guide.train.cmd_note")}
)]}
)]}
),
e.jsxs("div",
{
className:"space-y-2 pt-2 border-t border-stone-850",
children:[e.jsx("h4",
{
className:"font-pixel text-[10px] text-rpg-gold uppercase tracking-wider",
children:a("rl.guide.tab_submit")}
),
e.jsx("p",
{
className:"text-gray-400 text-[11px] leading-relaxed",
children:a("rl.guide.submit.desc")}
),
e.jsxs("div",
{
className:"p-2 border border-amber-700/50 bg-amber-950/20 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-amber-400 font-pixel text-[9px] uppercase tracking-wider block font-bold",
children:a("rl.guide.submit.step1_title")}
),
e.jsx("p",
{
className:"text-gray-400 text-[10px] mt-0.5 mb-1.5",
children:a("rl.guide.submit.step1_desc")}
),
e.jsxs("div",
{
className:"relative bg-black/80 p-2 rounded border border-amber-700/40 font-mono text-[10.5px] text-amber-400/90 flex justify-between items-start group",
children:[e.jsx("pre",
{
className:"overflow-x-auto whitespace-pre select-all pr-4 font-mono leading-relaxed",
children:`STUDENT_ID     = "YOUR_ID"  # ← 請填入您的學號
COMPETITION_ID = ${
t}
  # 請勿修改`}
),
e.jsx(L,
{
text:`STUDENT_ID     = "YOUR_ID"  # 請填入您的學號
COMPETITION_ID = ${
t}
  # 請勿修改`}
)]}
)]}
),
e.jsxs("div",
{
className:"p-2 border border-stone-850 bg-stone-900/10 rounded-[2px]",
children:[e.jsx("span",
{
className:"text-rpg-gold font-pixel text-[9px] uppercase tracking-wider block font-bold",
children:a("rl.guide.submit.step2_title")}
),
e.jsx("p",
{
className:"text-gray-400 text-[10px] mt-0.5 mb-1.5",
children:a("rl.guide.submit.step2_desc")}
),
e.jsxs("div",
{
className:"relative bg-black/80 p-2 rounded border border-stone-850 hover:border-stone-800 transition-colors font-mono text-[10.5px] text-amber-500/90 flex justify-between items-center group",
children:[e.jsx("pre",
{
className:"overflow-x-auto whitespace-pre-wrap select-all pr-4 font-mono",
children:"python run.py"}
),
e.jsx(L,
{
text:"python run.py"}
)]}
),
e.jsx("p",
{
className:"text-stone-500 text-[9px] mt-1.5 italic",
children:a("rl.guide.submit.note")}
)]}
)]}
)]}
)]}
),
I!==null&&e.jsxs("div",
{
className:"flex flex-col gap-2 bg-black/30 border border-gray-800 p-3 rounded-[2px] shadow-inner",
children:[e.jsxs("div",
{
className:"flex items-center justify-between font-pixel text-[10px] text-rpg-paper/70",
children:[e.jsxs("span",
{
children:[a("rl.upload.progress_label",
{
defaultValue:"傳輸進度"}
),
": ",
I.percent,
"%"]}
),
e.jsx("span",
{
className:"text-rpg-gold animate-pulse text-[9px] font-mono",
children:I.speed}
)]}
),
e.jsx("div",
{
className:"w-full bg-black/50 border border-gray-700 h-2.5 p-0.5 overflow-hidden",
children:e.jsx("div",
{
className:"h-full bg-purple-500 transition-all duration-100 shadow-[inset_0_1px_0_rgba(255,
255,
255,
0.3)]",
style:{
width:`${
I.percent}
%`}
}
)}
),
e.jsxs("div",
{
className:"flex justify-between font-pixel text-[8px] text-gray-500",
children:[e.jsxs("span",
{
children:[I.loaded,
" / ",
I.total]}
),
I.percent<100?e.jsx("span",
{
children:"傳送門連線中..."}
):e.jsx("span",
{
className:"text-rpg-gold animate-bounce",
children:"法陣構築完畢，寫入槽位..."}
)]}
)]}
),
H&&e.jsx("p",
{
className:"font-pixel text-xs text-red-400 border border-red-800/50 bg-red-900/20 px-3 py-2",
children:H}
),
e.jsxs("div",
{
className:"flex items-center gap-4 pt-1",
children:[e.jsx("button",
{
type:"submit",
disabled:$,
className:"flex-1 bg-black/40 border border-rpg-gold text-rpg-gold font-pixel text-xs py-2 px-4 hover:bg-black/60 disabled:opacity-50 disabled:cursor-not-allowed transition-colors uppercase tracking-wider",
children:D}
),
e.jsx("button",
{
type:"button",
onClick:v,
disabled:$,
className:"font-pixel text-xs text-gray-500 hover:text-rpg-paper disabled:opacity-50 disabled:cursor-not-allowed transition-colors underline underline-offset-2",
children:a("rl.upload.cancel")}
)]}
)]}
)]}
)}
)}
,
mt=({
slot:t,
isSolo:x=!1,
onClose:r}
)=>{
const{
t:o}
=Q(),
[C,
v]=l.useState([]),
[a,
N]=l.useState(!0),
[p,
i]=l.useState(null);
return l.useEffect(()=>{
N(!0),
i(null),
Ce(t.competition_id,
t.slot_index).then(u=>{
v(u.stats)}
).catch(u=>{
console.error("Failed to load radar stats:",
u),
i(o("rl.stats.error_load",
{
defaultValue:"無法載入能力分析數據"}
))}
).finally(()=>{
N(!1)}
)}
,
[t,
o]),
Ue.createPortal(e.jsx("div",
{
className:"fixed inset-0 z-5000 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in",
children:e.jsxs("div",
{
className:"relative w-full max-w-md bg-[#161618] border border-amber-600/60 shadow-2xl p-5 rounded-[4px] text-stone-200 mc-panel-border",
onClick:u=>u.stopPropagation(),
children:[e.jsxs("div",
{
className:"flex justify-between items-center border-b border-stone-850 pb-3 mb-4",
children:[e.jsx("h3",
{
className:"font-epic text-xs text-amber-500 uppercase tracking-widest",
children:o("rl.stats.title",
{
defaultValue:"代理人能力分析"}
)}
),
e.jsx("button",
{
onClick:r,
className:"text-stone-500 hover:text-stone-300 font-pixel text-lg cursor-pointer active:scale-95",
"aria-label":"Close",
children:"×"}
)]}
),
e.jsxs("div",
{
className:"mb-4 text-center",
children:[e.jsx("h4",
{
className:"font-epic text-sm text-stone-300 font-bold truncate",
children:t.name}
),
e.jsxs("p",
{
className:"font-parchment text-[11px] text-stone-500 uppercase mt-1 tracking-wider font-bold",
children:[x?`${
o("rl.hub.player_best_score",
{
defaultValue:"最佳分數"}
)}
: ${
t.best_score!=null?t.best_score.toFixed(1):"—"}
`:`Elo: ${
Math.round(t.elo_rating)}
`,
" | ",
o("rl.slot.played_games",
{
count:t.elo_games_played}
)]}
)]}
),
e.jsx("div",
{
className:"h-64 w-full flex items-center justify-center my-3 bg-[#0d0d0e] border border-stone-900 rounded p-2 relative",
children:a?e.jsxs("div",
{
className:"flex flex-col items-center justify-center gap-2",
children:[e.jsx("div",
{
className:"w-8 h-8 rounded-full border-2 border-stone-800 border-t-amber-500 animate-spin"}
),
e.jsx("span",
{
className:"font-epic text-[10px] text-stone-500 uppercase tracking-wider",
children:o("rl.stats.loading",
{
defaultValue:"分析中..."}
)}
)]}
):p?e.jsx("span",
{
className:"font-epic text-xs text-red-400",
children:p}
):e.jsx(ve,
{
width:"100%",
height:"100%",
children:e.jsxs(ye,
{
cx:"50%",
cy:"50%",
outerRadius:"75%",
data:C,
children:[e.jsx(Ne,
{
stroke:"#2e2e33"}
),
e.jsx(we,
{
dataKey:"subject",
tick:{
fill:"#a8a29e",
fontSize:11,
fontFamily:"monospace",
fontWeight:"bold"}
}
),
e.jsx(We,
{
angle:30,
domain:[0,
100],
tick:{
fill:"#57534e",
fontSize:8}
,
axisLine:!1}
),
e.jsx(ke,
{
name:t.name,
dataKey:"value",
stroke:"#d97706",
fill:"#d97706",
fillOpacity:.35}
)]}
)}
)}
),
!a&&!p&&C.length>0&&e.jsxs(e.Fragment,
{
children:[C.every(u=>u.value===0)&&e.jsxs("div",
{
className:"text-[11px] font-mono text-[#f87171] bg-red-950/20 border border-red-900/30 p-2.5 text-center mb-3",
children:["⚠️ ",
x?o("rl.stats.no_games_hint_solo",
{
defaultValue:"尚未完成任何評測回合，屬性數據將在首場評測後統計。"}
):o("rl.stats.no_games_hint",
{
defaultValue:"尚未參與任何競技對戰，能力屬性將在對戰完成後統計並長出！"}
)]}
),
e.jsx("div",
{
className:"grid grid-cols-2 gap-x-4 gap-y-2 text-[11px] font-mono mt-4 pt-3 border-t border-stone-850",
children:C.map((u,
w)=>e.jsxs("div",
{
className:"flex justify-between border-b border-stone-900/50 pb-1",
children:[e.jsxs("span",
{
className:"text-stone-500 uppercase",
children:[u.subject,
":"]}
),
e.jsx("span",
{
className:"text-amber-500 font-bold",
children:Math.round(u.value)}
)]}
,
w))}
)]}
),
e.jsx("div",
{
className:"mt-5 flex justify-end",
children:e.jsx("button",
{
onClick:r,
className:"px-4 py-1.5 bg-stone-900 hover:bg-stone-800 text-stone-300 font-epic text-xs uppercase tracking-wider border border-stone-800 shadow-md cursor-pointer transition-colors active:translate-y-px",
children:o("rl.stats.close",
{
defaultValue:"關閉"}
)}
)}
)]}
)}
),
document.body)}
,
ut=({
status:t}
)=>{
const{
t:x}
=Q(),
r="font-epic text-[10px] px-2 py-0.5 border rounded-[2px] tracking-wider";
switch(t){
case"pending":return e.jsx("span",
{
className:`${
r}
 border-stone-600 text-stone-500 bg-stone-900/30`,
children:x("rl.result.status.pending")}
);
case"running":return e.jsx("span",
{
className:`${
r}
 border-amber-600 text-amber-500 bg-amber-900/20 animate-pulse`,
children:x("rl.result.status.running")}
);
case"completed":return e.jsx("span",
{
className:`${
r}
 border-emerald-700 text-emerald-700 bg-emerald-900/10 font-bold`,
children:x("rl.result.status.completed")}
);
case"failed":return e.jsx("span",
{
className:`${
r}
 border-red-800 text-red-800 bg-red-950/10`,
children:x("rl.result.status.failed")}
);
default:return null}
}
,
je=({
session:t,
currentUserId:x}
)=>{
const{
t:r,
i18n:o}
=Q(),
C=Se(),
v=t.participants.find(m=>m.user_id===x)??null,
[a,
N]=l.useState(!!v?.is_pinned),
[p,
i]=l.useState(!1);
l.useEffect(()=>{
N(!!v?.is_pinned)}
,
[v?.is_pinned]);
const u=async m=>{
if(m.stopPropagation(),
!!v){
i(!0);
try{
const b=a?await Ge(t.id):await Ye(t.id);
N(b.is_pinned)}
catch(b){
alert(oe(b,
r("rl.result.pinned_failed")))}
finally{
i(!1)}
}
}
,
w=r(`rl.result.types.${
t.session_type}
`)||t.session_type.toUpperCase(),
E=new Date(t.created_at).toLocaleDateString(o.language,
{
year:"numeric",
month:"short",
day:"numeric"}
);
return e.jsxs("div",
{
className:"rpg-parchment-card p-4 flex flex-col gap-3 hover:-translate-y-0.5 transition-transform duration-200 cursor-pointer rounded-[3px]",
onClick:()=>C(`/rl/battles/${
t.id}
`),
children:[e.jsxs("div",
{
className:"flex items-center justify-between gap-2 border-b border-[#78350F]/15 pb-2",
children:[e.jsx("span",
{
className:"font-epic text-[10px] px-2.5 py-0.5 border border-[#78350F]/30 text-[#78350F] bg-[#78350F]/5 rounded-[2px] tracking-wider",
children:w}
),
e.jsxs("div",
{
className:"flex items-center gap-2",
children:[t.status==="completed"&&v&&e.jsx("button",
{
onClick:u,
disabled:p,
className:`shrink-0 flex items-center justify-center w-5 h-5 border rounded-[2px] transition-colors ${
a?"border-amber-600 bg-amber-600/10 text-amber-700":"border-[#78350F]/30 text-[#78350F]/50 hover:text-amber-600 hover:border-amber-600"}
 disabled:opacity-40 cursor-pointer`,
title:r("rl.result.pin_highlight"),
children:e.jsx("svg",
{
className:"w-3.5 h-3.5",
fill:a?"currentColor":"none",
viewBox:"0 0 24 24",
stroke:"currentColor",
children:e.jsx("path",
{
strokeLinecap:"round",
strokeLinejoin:"round",
strokeWidth:2,
d:"M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.907c.961 0 1.36 1.242.588 1.81l-3.97 2.883a1 1 0 00-.364 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.971-2.883a1 1 0 00-1.17 0l-3.97 2.883c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.364-1.118L2.98 10.1c-.773-.568-.375-1.81.588-1.81h4.907a1 1 0 00.95-.69l1.519-4.674z"}
)}
)}
),
e.jsx(ut,
{
status:t.status}
)]}
)]}
),
e.jsx("div",
{
className:"flex flex-col gap-1.5 py-1",
children:t.participants.length===0?e.jsx("p",
{
className:"font-parchment text-xs text-[#5c3c1e]/50 italic",
children:r("rl.lobby.waiting")}
):t.participants.map(m=>{
const b=m.user_id===x;
return e.jsxs("div",
{
className:`flex items-center justify-between gap-2 ${
b?"text-amber-800 font-bold":"text-[#2B2017]/85"}
`,
children:[e.jsxs("div",
{
className:"flex items-center gap-1.5 min-w-0",
children:[b&&e.jsx("span",
{
className:"text-[10px] text-amber-700 bg-amber-100 border border-amber-600/30 px-1 rounded-[2px] scale-90",
children:r("rl.lobby.self")}
),
e.jsx("span",
{
className:"font-parchment text-sm truncate",
children:m.slot_name??`Agent #${
m.rl_slot_id}
`}
)]}
),
t.status==="completed"&&e.jsxs("div",
{
className:"flex items-center gap-1.5 shrink-0",
children:[m.final_score!==null&&e.jsx("span",
{
className:"font-mono text-xs font-bold text-[#2B2017]",
title:r("rl.result.score",
{
defaultValue:"得分"}
),
children:m.final_score.toLocaleString(void 0,
{
maximumFractionDigits:1}
)}
),
m.elo_delta!==null&&e.jsxs("span",
{
className:`font-mono text-[10px] font-bold ${
m.elo_delta>=0?"text-emerald-700":"text-rose-800"}
`,
children:[m.elo_delta>=0?"(▲ +":"(▼ ",
Math.abs(m.elo_delta).toFixed(1),
")"]}
)]}
)]}
,
m.id)}
)}
),
e.jsxs("div",
{
className:"flex items-center justify-between text-[#5c3c1e]/60 pt-2 border-t border-[#78350F]/15 font-pixel text-[10px]",
children:[e.jsx("span",
{
children:E}
),
e.jsx("span",
{
children:r("rl.index.players_count",
{
count:t.max_players}
)}
)]}
)]}
)}
,
bt=({
values:t}
)=>{
const x=U.useRef(null);
return U.useEffect(()=>{
const r=x.current;
if(!r||t.length<2)return;
const o=r.getContext("2d");
if(!o)return;
o.clearRect(0,
0,
r.width,
r.height);
const C=r.width,
v=r.height,
a=Math.min(...t),
N=Math.max(...t),
p=N-a===0?1:N-a;
o.beginPath(),
o.lineWidth=1.5;
const i=t[0],
u=t[t.length-1];
o.strokeStyle=u>=i?"#10b981":"#ef4444",
t.forEach((m,
b)=>{
const h=b/(t.length-1)*(C-4)+2,
B=v-(m-a)/p*(v-6)-3;
b===0?o.moveTo(h,
B):o.lineTo(h,
B)}
),
o.stroke();
const w=C-2,
E=v-(u-a)/p*(v-6)-3;
o.beginPath(),
o.arc(w,
E,
2,
0,
2*Math.PI),
o.fillStyle=u>=i?"#10b981":"#ef4444",
o.fill()}
,
[t]),
e.jsxs("div",
{
className:"relative group/sparkline",
children:[e.jsx("canvas",
{
ref:x,
width:60,
height:20,
className:"w-[60px] h-[20px] opacity-75 group-hover/sparkline:opacity-100 transition-opacity shrink-0"}
),
e.jsxs("div",
{
className:"absolute bottom-6 left-1/2 -translate-x-1/2 bg-stone-950 border border-stone-850 px-2 py-1 text-[9px] text-stone-300 rounded shadow-md pointer-events-none opacity-0 group-hover/sparkline:opacity-100 transition-opacity whitespace-nowrap font-epic z-50",
children:["歷史趨勢: ",
Math.round(t[0]),
" → ",
Math.round(t[t.length-1])]}
)]}
)}
,
ht=({
competitionId:t,
isSolo:x=!1}
)=>{
const{
t:r}
=Q(),
[o,
C]=l.useState([]),
v=l.useRef(null),
a=l.useRef({
}
);
l.useLayoutEffect(()=>{
if(!v.current)return;
const n=v.current.children,
f={
}
;
for(let g=0;
g<n.length;
g++){
const d=n[g],
y=d.dataset.flipId;
y&&(f[y]=d.getBoundingClientRect())}
a.current=f}
,
[o]),
l.useLayoutEffect(()=>{
if(!v.current)return;
const n=v.current.children;
for(let f=0;
f<n.length;
f++){
const g=n[f],
d=g.dataset.flipId;
if(!d)continue;
const y=a.current[d];
if(!y)continue;
const j=g.getBoundingClientRect(),
k=y.top-j.top,
F=y.left-j.left;
(F!==0||k!==0)&&(g.style.transform=`translate(${
F}
px,
 ${
k}
px)`,
g.style.transition="none",
requestAnimationFrame(()=>{
requestAnimationFrame(()=>{
g.style.transform="",
g.style.transition="transform 0.5s cubic-bezier(0.2,
 0.8,
 0.2,
 1),
 border-color 0.15s,
 background-color 0.15s"}
)}
))}
}
,
[o]);
const[N,
p]=l.useState({
}
),
[i,
u]=l.useState(null),
[w,
E]=l.useState(!1),
[m,
b]=l.useState(!0),
[h,
B]=l.useState(null),
[$]=l.useState(()=>localStorage.getItem("rl_particles")!=="false");
if(l.useEffect(()=>{
let n=!1;
return b(!0),
B(null),
Ee(t).then(f=>{
n||C(f)}
).catch(f=>{
n||B(f instanceof Error?f.message:r("rl.lobby.error_load"))}
).finally(()=>{
n||b(!1)}
),
Ze(t).then(f=>{
if(!n){
const g={
}
;
f.forEach(d=>{
d.history&&d.history.length>0&&(g[d.user_id]=d.history.map(y=>y.value))}
),
p(g)}
}
).catch(f=>console.error("[EloLeaderboard] ELO history load failed:",
f)),
x||Je(t).then(f=>{
n||u(f)}
).catch(f=>console.error("[EloLeaderboard] H2H matrix load failed:",
f)),
()=>{
n=!0}
}
,
[t,
x]),
m)return e.jsx("div",
{
className:"flex items-center justify-center py-12",
children:e.jsx("p",
{
className:"font-epic text-sm text-stone-500 animate-pulse tracking-widest",
children:r("rl.lobby.loading")}
)}
);
if(h)return e.jsx("div",
{
className:"font-epic text-xs border px-4 py-5 text-center text-red-400 border-red-950 bg-red-950/20 rounded-[3px]",
children:r("rl.lobby.error_load")}
);
if(o.length===0)return e.jsx("div",
{
className:"flex items-center justify-center py-12 border border-dashed border-stone-850 bg-stone-900/10 rounded-[3px]",
children:e.jsx("p",
{
className:"font-epic text-xs text-stone-500 tracking-wider",
children:r("rl.lobby.no_records")}
)}
);
const c=o.slice(0,
3);
return e.jsxs("div",
{
className:"flex flex-col gap-2",
children:[o.length>0&&($?e.jsxs("div",
{
className:"max-w-4xl mx-auto w-full mb-8",
children:[e.jsx(ot,
{
entries:o}
),
e.jsxs("div",
{
className:"grid grid-cols-3 gap-4 pt-4 border-b border-stone-850/60 px-2 w-full",
children:[c[1]&&e.jsxs("div",
{
className:"text-center pb-2 flex flex-col items-center",
children:[e.jsx("div",
{
className:"w-6 h-6 rounded-full border border-stone-400 bg-stone-950 flex items-center justify-center font-epic text-[10px] text-stone-300 shadow-md mb-1",
children:"II"}
),
e.jsx("span",
{
className:"font-epic text-xs text-stone-300 block truncate font-bold w-full",
children:c[1].nickname??c[1].username}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-stone-500 block truncate font-bold w-full",
children:c[1].slot_name}
),
e.jsx("div",
{
className:"scale-80 my-0.5",
children:e.jsx(K,
{
tier:c[1].tier}
)}
),
e.jsx("span",
{
className:"font-epic text-xs text-stone-300 font-bold",
children:x?c[1].best_score?.toFixed(1):Math.round(c[1].elo_rating)}
)]}
),
c[0]&&e.jsxs("div",
{
className:"text-center pb-2 flex flex-col items-center",
children:[e.jsx("div",
{
className:"w-8 h-8 rounded-full border border-amber-500 bg-stone-950 flex items-center justify-center font-epic text-xs text-amber-500 shadow-md mb-1",
children:"👑"}
),
e.jsx("span",
{
className:"font-epic text-sm text-amber-400 block truncate font-bold w-full",
children:c[0].nickname??c[0].username}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-amber-600/70 block truncate font-bold w-full",
children:c[0].slot_name}
),
e.jsx("div",
{
className:"scale-85 my-0.5",
children:e.jsx(K,
{
tier:c[0].tier}
)}
),
e.jsx("span",
{
className:"font-epic text-sm text-amber-400 font-black",
children:x?c[0].best_score?.toFixed(1):Math.round(c[0].elo_rating)}
)]}
),
c[2]&&e.jsxs("div",
{
className:"text-center pb-2 flex flex-col items-center",
children:[e.jsx("div",
{
className:"w-6 h-6 rounded-full border border-amber-800 bg-stone-950 flex items-center justify-center font-epic text-[10px] text-amber-700 shadow-md mb-1",
children:"III"}
),
e.jsx("span",
{
className:"font-epic text-xs text-amber-700 block truncate font-bold w-full",
children:c[2].nickname??c[2].username}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-stone-500 block truncate font-bold w-full",
children:c[2].slot_name}
),
e.jsx("div",
{
className:"scale-80 my-0.5",
children:e.jsx(K,
{
tier:c[2].tier}
)}
),
e.jsx("span",
{
className:"font-epic text-xs text-amber-700 font-bold",
children:x?c[2].best_score?.toFixed(1):Math.round(c[2].elo_rating)}
)]}
)]}
)]}
):e.jsxs("div",
{
className:"flex flex-col sm:grid sm:grid-cols-3 gap-4 items-center sm:items-end mb-8 pt-6 pb-4 max-w-4xl mx-auto border-b border-stone-850/60 w-full px-2",
children:[c[1]&&e.jsxs("div",
{
className:"flex flex-col items-center order-2 sm:order-none w-full max-w-[240px] sm:max-w-none",
children:[e.jsx("div",
{
className:"w-8 h-8 rounded-full border border-stone-400 bg-stone-950 flex items-center justify-center font-epic text-xs text-stone-300 shadow-md",
children:"II"}
),
e.jsxs("div",
{
className:"w-full bg-stone-900/50 border border-stone-500 p-3 mt-2 text-center rounded-[3px] shadow-lg flex flex-col items-center h-36 justify-between",
children:[e.jsxs("div",
{
className:"min-w-0 w-full",
children:[e.jsx("span",
{
className:"font-epic text-xs text-stone-300 block truncate font-bold",
children:c[1].nickname??c[1].username}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-stone-500 block truncate font-bold",
children:c[1].slot_name}
)]}
),
e.jsx("div",
{
className:"scale-90",
children:e.jsx(K,
{
tier:c[1].tier}
)}
),
e.jsx("span",
{
className:"font-epic text-sm text-stone-300 font-bold",
children:x?c[1].best_score?.toFixed(1):Math.round(c[1].elo_rating)}
)]}
),
e.jsx("div",
{
className:"h-4 w-full bg-stone-700 border-t-2 border-stone-500 rounded-b-[2px]"}
)]}
),
c[0]&&e.jsxs("div",
{
className:"flex flex-col items-center z-10 scale-105 order-1 sm:order-none w-full max-w-[240px] sm:max-w-none my-4 sm:my-0",
children:[e.jsx("div",
{
className:"w-10 h-10 rounded-full border-2 border-amber-500 bg-stone-950 flex items-center justify-center font-epic text-sm text-amber-500 shadow-[0_0_15px_rgba(217,
119,
6,
0.4)] animate-pulse",
children:"👑"}
),
e.jsxs("div",
{
className:"w-full bg-stone-900/70 border-2 border-amber-500 p-4 mt-2 text-center rounded-[4px] shadow-2xl flex flex-col items-center h-44 justify-between relative overflow-hidden",
children:[e.jsx("div",
{
className:"absolute inset-0 bg-gradient-to-t from-amber-600/5 to-transparent pointer-events-none"}
),
e.jsxs("div",
{
className:"min-w-0 w-full",
children:[e.jsx("span",
{
className:"font-epic text-sm text-amber-400 block truncate font-bold",
children:c[0].nickname??c[0].username}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-amber-600/70 block truncate font-bold",
children:c[0].slot_name}
)]}
),
e.jsx("div",
{
className:"scale-95",
children:e.jsx(K,
{
tier:c[0].tier}
)}
),
e.jsx("span",
{
className:"font-epic text-base text-amber-400 font-black",
children:x?c[0].best_score?.toFixed(1):Math.round(c[0].elo_rating)}
)]}
),
e.jsx("div",
{
className:"h-8 w-full bg-gradient-to-b from-amber-600 to-amber-800 border-t-2 border-amber-400 rounded-b-[4px]"}
)]}
),
c[2]&&e.jsxs("div",
{
className:"flex flex-col items-center order-3 sm:order-none w-full max-w-[240px] sm:max-w-none",
children:[e.jsx("div",
{
className:"w-8 h-8 rounded-full border border-amber-800 bg-stone-950 flex items-center justify-center font-epic text-xs text-amber-700 shadow-md",
children:"III"}
),
e.jsxs("div",
{
className:"w-full bg-stone-900/50 border border-amber-800 p-3 mt-2 text-center rounded-[3px] shadow-lg flex flex-col items-center h-32 justify-between",
children:[e.jsxs("div",
{
className:"min-w-0 w-full",
children:[e.jsx("span",
{
className:"font-epic text-xs text-amber-700 block truncate font-bold",
children:c[2].nickname??c[2].username}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-stone-500 block truncate font-bold",
children:c[2].slot_name}
)]}
),
e.jsx("div",
{
className:"scale-90",
children:e.jsx(K,
{
tier:c[2].tier}
)}
),
e.jsx("span",
{
className:"font-epic text-sm text-amber-700 font-bold",
children:x?c[2].best_score?.toFixed(1):Math.round(c[2].elo_rating)}
)]}
),
e.jsx("div",
{
className:"h-3 w-full bg-amber-900 border-t-2 border-amber-800 rounded-b-[2px]"}
)]}
)]}
)),
!x&&i&&i.players.length>0&&e.jsxs("div",
{
className:"mb-6 bg-stone-900/35 border border-stone-850 p-4 rounded-[4px] shadow-sm",
children:[e.jsxs("button",
{
onClick:()=>E(!w),
className:"flex items-center justify-between w-full font-epic text-xs text-amber-500 hover:text-amber-400 uppercase tracking-wider focus:outline-none",
children:[e.jsx("span",
{
children:w?"▼ 隱藏 Meta 克制關係熱圖 (H2H)":"▶ 顯示 Meta 克制關係熱圖 (H2H)"}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-stone-500 lowercase italic hidden sm:inline",
children:"展示前十名選手之間的兩兩對戰勝率，揭示策略克制生態"}
)]}
),
w&&e.jsx("div",
{
className:"mt-4 overflow-x-auto select-none",
children:e.jsx("div",
{
className:"min-w-[640px] p-2 bg-stone-950/20 rounded-[3px] border border-stone-900/40",
children:e.jsxs("div",
{
className:"grid gap-px bg-stone-900/40 p-1 rounded",
style:{
gridTemplateColumns:`110px repeat(${
i.players.length}
,
 1fr)`}
,
children:[e.jsx("div",
{
className:"h-8"}
),
i.players.map(n=>e.jsx("div",
{
className:"text-center font-epic text-[9px] text-stone-400 truncate px-1 self-center",
title:n.nickname||n.username,
children:n.nickname||n.username}
,
`header-col-${
n.user_id}
`)),
i.players.map((n,
f)=>e.jsxs(U.Fragment,
{
children:[e.jsx("div",
{
className:"h-8 flex items-center font-epic text-[9px] text-stone-400 truncate pr-2 font-bold self-center",
children:n.nickname||n.username}
),
i.matrix[f].map((g,
d)=>{
const y=i.players[d],
j=f===d;
let k="rgba(28,
 28,
 30,
 0.4)",
F="text-stone-600",
L="—",
H=`${
n.nickname||n.username}
 與自己的對決`;
if(!j)if(g===null)L="N/A",
k="rgba(20,
 20,
 22,
 0.5)",
F="text-stone-750",
H="無對戰數據";
else if(L=`${
(g*100).toFixed(0)}
%`,
F=g>=.5?"text-emerald-100":"text-rose-100",
H=`${
n.nickname||n.username}
 對陣 ${
y.nickname||y.username}
: 勝率 ${
(g*100).toFixed(1)}
%`,
g>=.5){
const T=(g-.5)*2;
k=`rgba(16,
 185,
 129,
 ${
Math.min(.85,
.12+T*.65)}
)`}
else{
const T=(.5-g)*2;
k=`rgba(239,
 68,
 68,
 ${
Math.min(.85,
.12+T*.65)}
)`}
return e.jsxs("div",
{
className:"h-8 flex items-center justify-center font-epic text-[10px] font-bold transition-transform hover:scale-105 relative group/cell cursor-help rounded-[1px]",
style:{
backgroundColor:j?"transparent":k}
,
title:H,
children:[e.jsx("span",
{
className:F,
children:L}
),
e.jsx("div",
{
className:"absolute bottom-9 left-1/2 -translate-x-1/2 bg-stone-950 border border-stone-850 px-2.5 py-1.5 text-[10px] text-stone-200 rounded shadow-2xl pointer-events-none opacity-0 group-hover/cell:opacity-100 transition-opacity whitespace-nowrap z-50 font-epic",
children:H}
)]}
,
`cell-${
n.user_id}
-${
y.user_id}
`)}
)]}
,
`row-frag-${
n.user_id}
`))]}
)}
)}
)]}
),
e.jsxs("div",
{
className:"flex items-center gap-3 px-3 pb-2 border-b border-stone-800 text-stone-500 font-epic text-[10px] uppercase tracking-wider",
children:[e.jsx("span",
{
className:"w-8 text-center",
children:r("rl.lobby.rank")}
),
e.jsx("span",
{
className:"w-16 text-center shrink-0",
children:r("rl.lobby.crest")}
),
e.jsx("div",
{
className:"w-8 shrink-0 hidden sm:block"}
),
e.jsx("span",
{
className:"flex-1",
children:r("rl.lobby.challenger")}
),
e.jsx("span",
{
className:"w-20 text-right",
children:r(x?"rl.lobby.best_score":"rl.lobby.elo")}
),
!x&&e.jsx("span",
{
className:"w-20 text-right hidden sm:block",
children:r("rl.lobby.record")}
)]}
),
e.jsx("div",
{
ref:v,
className:"flex flex-col gap-1.5",
children:o.slice(3).map((n,
f)=>{
const g=f+4,
d="text-stone-400",
y=n.nickname??n.username;
return e.jsxs("div",
{
"data-flip-id":n.user_id,
className:"flex items-center gap-3 px-3 py-3 rounded-[3px] border transition-all duration-150 bg-[#1a1a1c]/40 border-stone-850 hover:bg-[#1a1a1c] hover:border-amber-600/35 hover:-translate-x-0.5",
children:[e.jsx("span",
{
className:`font-epic text-xs w-8 text-center font-bold ${
d}
`,
children:g}
),
e.jsx("div",
{
className:"w-16 flex justify-center shrink-0",
children:e.jsx(K,
{
tier:n.tier}
)}
),
e.jsx("div",
{
className:`relative opacity-90 shrink-0 w-8 h-8 border rounded-full overflow-hidden bg-stone-950/60 ${
g===1?"border-amber-500 shadow-[0_0_8px_rgba(217,
119,
6,
0.3)]":"border-stone-800"}
 hidden sm:block`,
children:e.jsx(Xe,
{
seed:n.avatar_seed??n.username,
isPriority:f<10,
useBatch:!1}
)}
),
e.jsxs("div",
{
className:"flex flex-col flex-1 min-w-0",
children:[e.jsxs("div",
{
className:"flex items-center gap-1.5 flex-wrap",
children:[e.jsx("span",
{
className:`font-epic text-xs truncate font-bold ${
d}
`,
children:y}
),
n.team_name&&e.jsxs(e.Fragment,
{
children:[e.jsx("span",
{
className:"text-stone-700 text-[9px] shrink-0",
children:"·"}
),
e.jsx(ct,
{
seed:n.emblem_seed,
color:n.team_color,
size:14}
),
e.jsx("span",
{
className:"text-[9px] text-stone-500 font-serif whitespace-nowrap",
children:n.team_name}
)]}
)]}
),
e.jsx("span",
{
className:"font-parchment text-[10px] text-stone-500 truncate font-bold",
children:n.slot_name}
)]}
),
N[n.user_id]&&N[n.user_id].length>=2&&e.jsx("div",
{
className:"hidden sm:block mr-2",
title:"歷史趨勢",
children:e.jsx(bt,
{
values:N[n.user_id]}
)}
),
e.jsx("span",
{
className:`font-epic text-xs w-20 text-right font-black ${
d}
`,
children:x?n.best_score!=null?n.best_score.toFixed(1):"—":Math.round(n.elo_rating)}
),
!x&&e.jsx("span",
{
className:"font-parchment text-xs text-stone-500 w-20 text-right font-bold hidden sm:block",
children:r("rl.lobby.wins_losses",
{
wins:n.wins,
losses:n.losses}
)}
)]}
,
n.user_id)}
)}
)]}
)}
,
ft=({
competitionId:t,
attackerSlotId:x,
maxPlayers:r,
currentUserId:o,
onSuccess:C,
onCancel:v}
)=>{
const{
t:a}
=Q(),
[N,
p]=l.useState([]),
[i,
u]=l.useState(!0),
[w,
E]=l.useState(null),
[m,
b]=l.useState(new Set),
[h,
B]=l.useState(!1),
[$,
c]=l.useState(null),
n=r-1;
l.useEffect(()=>{
let j=!1;
return u(!0),
E(null),
Ee(t).then(k=>{
j||p(k.filter(F=>F.user_id!==o))}
).catch(k=>{
j||E(k instanceof Error?k.message:a("rl.challenge.error_load"))}
).finally(()=>{
j||u(!1)}
),
()=>{
j=!0}
}
,
[t,
o]);
const f=j=>{
b(k=>{
const F=new Set(k);
return F.has(j)?F.delete(j):F.size<n&&F.add(j),
F}
)}
,
g=async()=>{
if(m.size!==n)return;
c(null),
B(!0);
const j={
competition_id:t,
attacker_slot_id:x,
target_user_ids:Array.from(m)}
;
try{
const k=await et(j);
C(k)}
catch(k){
c(oe(k,
a("rl.challenge.error_submit")))}
finally{
B(!1)}
}
,
d=j=>{
j.target===j.currentTarget&&v()}
,
y=m.size===n&&!h;
return e.jsx("div",
{
className:"fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4",
onClick:d,
children:e.jsxs("div",
{
className:"bg-rpg-dark pixel-border w-full max-w-lg p-6 flex flex-col gap-5 max-h-[90vh]",
children:[e.jsxs("div",
{
className:"flex flex-col gap-1",
children:[e.jsx("h2",
{
className:"font-pixel text-sm text-rpg-gold uppercase tracking-wider",
children:a("rl.challenge.title")}
),
e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/50",
children:m.size>0?a("rl.challenge.subtitle_selected",
{
count:n,
selected:m.size,
total:n}
):a("rl.challenge.subtitle",
{
count:n}
)}
)]}
),
e.jsx("div",
{
className:"flex-1 overflow-y-auto flex flex-col gap-2 min-h-0",
children:i?e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/50 animate-pulse text-center py-6",
children:a("rl.challenge.loading_players")}
):w?e.jsx("p",
{
className:"font-pixel text-xs text-red-400 border border-red-800/50 bg-red-900/20 px-3 py-2",
children:w}
):N.length===0?e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/40 text-center py-6",
children:a("rl.challenge.empty")}
):N.map(j=>{
const k=m.has(j.user_id),
F=!k&&m.size>=n,
L=j.nickname??j.username;
return e.jsxs("button",
{
type:"button",
disabled:F||h,
onClick:()=>f(j.user_id),
className:["flex items-center gap-3 px-3 py-2 border text-left transition-colors w-full",
k?"border-rpg-gold bg-rpg-gold/10":F?"border-gray-700 bg-black/20 opacity-40 cursor-not-allowed":"border-gray-700 bg-black/20 hover:border-gray-500"].join(" "),
children:[e.jsx("div",
{
className:"w-8 h-8 shrink-0 flex items-center justify-center bg-black/40 pixel-border",
children:e.jsx("span",
{
className:"font-pixel text-xs text-rpg-paper",
children:L.charAt(0).toUpperCase()}
)}
),
e.jsxs("div",
{
className:"flex flex-col flex-1 min-w-0",
children:[e.jsx("span",
{
className:"font-pixel text-xs text-rpg-paper truncate",
children:L}
),
e.jsx("span",
{
className:"font-pixel text-xs text-rpg-paper/40 truncate",
children:j.slot_name}
)]}
),
e.jsx("span",
{
className:"font-pixel text-xs text-rpg-gold shrink-0",
children:Math.round(j.elo_rating)}
),
e.jsx("div",
{
className:["w-4 h-4 shrink-0 border flex items-center justify-center",
k?"border-rpg-gold bg-rpg-gold/20":"border-gray-600"].join(" "),
children:k&&e.jsx("span",
{
className:"font-pixel text-xs text-rpg-gold leading-none",
children:"✓"}
)}
)]}
,
j.user_id)}
)}
),
$&&e.jsx("p",
{
className:"font-pixel text-xs text-red-400 border border-red-800/50 bg-red-900/20 px-3 py-2",
children:$}
),
e.jsxs("div",
{
className:"flex items-center gap-4",
children:[e.jsx("button",
{
type:"button",
disabled:!y,
onClick:g,
className:"flex-1 bg-black/40 border border-rpg-gold text-rpg-gold font-pixel text-xs py-2 px-4 hover:bg-black/60 disabled:opacity-50 disabled:cursor-not-allowed transition-colors uppercase tracking-wider",
children:a(h?"rl.challenge.submitting":"rl.challenge.submit")}
),
e.jsx("button",
{
type:"button",
onClick:v,
disabled:h,
className:"font-pixel text-xs text-gray-500 hover:text-rpg-paper disabled:opacity-50 disabled:cursor-not-allowed transition-colors underline underline-offset-2",
children:a("rl.challenge.cancel")}
)]}
)]}
)}
)}
,
gt=({
waitSeconds:t}
)=>{
const x=U.useRef(null);
return U.useEffect(()=>{
const r=x.current;
if(!r)return;
const o=r.getContext("2d");
if(!o)return;
let C,
v=0;
const a=()=>{
r.parentElement&&(r.width=r.parentElement.clientWidth,
r.height=r.parentElement.clientHeight||240)}
;
a(),
window.addEventListener("resize",
a);
const N=()=>{
o.clearRect(0,
0,
r.width,
r.height);
const p=r.width,
i=r.height,
u=i/2,
w=Math.max(.1,
Math.exp(-t/60)),
E=i*.25*w;
v+=.04,
[{
frequency:.015,
speed:.05,
amplitudeMultiplier:1,
color:"rgba(245,
 158,
 11,
 0.3)",
lineWidth:2}
,
{
frequency:.025,
speed:-.04,
amplitudeMultiplier:.65,
color:"rgba(239,
 68,
 68,
 0.18)",
lineWidth:1.5}
,
{
frequency:.012,
speed:.08,
amplitudeMultiplier:.5,
color:"rgba(245,
 158,
 11,
 0.1)",
lineWidth:1}
].forEach(b=>{
o.beginPath(),
o.strokeStyle=b.color,
o.lineWidth=b.lineWidth;
for(let h=0;
h<p;
h++){
const B=v*b.speed,
$=Math.sin(h*.1+v*2)*Math.cos(h*.05-v)*4*w,
c=u+Math.sin(h*b.frequency+B)*E*b.amplitudeMultiplier+$;
h===0?o.moveTo(h,
c):o.lineTo(h,
c)}
o.stroke()}
),
o.beginPath(),
o.strokeStyle="rgba(245,
 158,
 11,
 0.06)",
o.setLineDash([8,
12]),
o.moveTo(0,
u),
o.lineTo(p,
u),
o.stroke(),
o.setLineDash([]),
C=requestAnimationFrame(N)}
;
return N(),
()=>{
cancelAnimationFrame(C),
window.removeEventListener("resize",
a)}
}
,
[t]),
e.jsx("canvas",
{
ref:x,
className:"w-full h-full block"}
)}
,
jt=[{
id:"roster",
label:"我的陣容"}
,
{
id:"lobby",
label:"對戰大廳"}
,
{
id:"leaderboard",
label:"排行榜"}
,
{
id:"tasks",
label:"任務"}
,
{
id:"history",
label:"對戰記錄（全部）"}
];
function _e({
active:t,
onClick:x,
children:r}
){
return e.jsx("button",
{
onClick:x,
className:`px-4 py-1.5 text-xs uppercase tracking-widest font-serif rounded-[2px] border transition-all duration-150 cursor-pointer ${
t?"bg-stone-900 border-amber-500 text-amber-400 shadow-[0_0_8px_rgba(245,
158,
11,
0.2),
inset_0_1px_0_rgba(245,
158,
11,
0.1)]":"bg-stone-900 border-stone-700 text-stone-400 hover:text-stone-200 hover:border-stone-600"}
`,
children:r}
)}
const Et=()=>{
const{
t}
=Q(),
{
competitionId:x}
=Oe(),
r=parseInt(x??"0"),
o=Se(),
C=U.useMemo(()=>[{
title:t("guide.web.roster_title",
"我的陣容 (My Roster) — 配置出戰 Agent"),
desc:t("guide.web.roster_desc_1",
"每個玩家最多可配置 3 個出戰槽位。"),
icon:"🛡️"}
,
{
title:t("guide.web.roster_title",
"我的陣容 (My Roster) — 配置出戰 Agent"),
desc:t("guide.web.roster_desc_2",
"點擊槽位卡片上的「配置 Agent」來上傳您的決策代碼（agent.py）與模型權重檔。"),
icon:"📁"}
,
{
title:t("guide.web.roster_title",
"我的陣容 (My Roster) — 配置出戰 Agent"),
desc:t("guide.web.roster_desc_3",
"對已上傳的 Agent，可以點擊「表現分析」查看其多維度戰力雷達圖。雷達圖數據會在該 Agent 參與一定數量對戰後解鎖生成。"),
icon:"📊"}
],
[t]),
v=U.useMemo(()=>[{
title:t("guide.web.lobby_title",
"對戰大廳 (Battle Lobby) — 發起匹配與決鬥"),
desc:t("guide.web.lobby_desc_1",
"選擇您要派出的出戰 Agent，即可啟動競技。"),
icon:"⚔️"}
,
{
title:t("guide.web.lobby_auto_title",
"系統自動週期排名賽 — 均衡所有人的場次"),
desc:t("guide.web.lobby_auto_desc",
"為確保每位同學都有公平的對戰機會，系統會定期自動為所有已上傳 Agent 的玩家安排對戰，無需手動觸發。自動對戰完全免費，不消耗體力，結果同樣計入 Elo 積分。"),
icon:"🤖"}
,
{
title:t("guide.web.lobby_auto_agent_title",
"自動出戰使用哪個 Agent？"),
desc:t("guide.web.lobby_auto_agent_desc",
"系統自動排程時，會使用您「最近一次上傳」的 Agent 槽位代表您出戰。若您已上傳改良版本，系統將自動切換為最新版本，無需額外設定。"),
icon:"🔁"}
,
{
title:t("guide.web.lobby_title",
"對戰大廳 (Battle Lobby) — 發起匹配與決鬥"),
desc:t("guide.web.lobby_desc_2",
"自動匹配 (PVP)：系統會在後台搜尋積分與您相近的對手進行沙箱模擬對決。匹配成功將自動跳轉至對戰現場。"),
icon:"🔄"}
,
{
title:t("guide.web.lobby_title",
"對戰大廳 (Battle Lobby) — 發起匹配與決鬥"),
desc:t("guide.web.lobby_desc_3",
"指定挑戰 (PVP)：點擊此按鈕，可直接挑選其他線上玩家的 Agent 進行直接對決與切磋（手動發起可能需要消耗體力，自動匹配則免費）。"),
icon:"🥊"}
,
{
title:t("guide.web.lobby_title",
"對戰大廳 (Battle Lobby) — 發起匹配與決鬥"),
desc:t("guide.web.lobby_desc_4",
"發起沙箱評測 (SOLO)：讓您的 Agent 獨自挑戰關卡，評估其最佳累積遊戲分數。"),
icon:"🎯"}
],
[t]),
a=U.useMemo(()=>[{
title:t("guide.web.leaderboard_title",
"排行榜 (Leaderboard) — 爭奪榮耀與積分"),
desc:t("guide.web.leaderboard_desc_1",
"PVP 競賽採用 Elo 評分機制，每次與其他玩家對戰（包含手動匹配與系統每日舉行的自動週期排名賽）後，將即時更新 Elo 分數與段位。"),
icon:"🏆"}
,
{
title:t("guide.web.leaderboard_title",
"排行榜 (Leaderboard) — 爭奪榮耀與積分"),
desc:t("guide.web.leaderboard_desc_2",
"SOLO 競賽則根據所有 Agent 跑出的平均「最佳累積得分」進行全服高低排行。"),
icon:"📈"}
],
[t]),
N=U.useMemo(()=>[{
title:t("guide.web.history_title",
"對戰記錄 (Battle Records) — 觀看重播與防清理"),
desc:t("guide.web.history_desc_1",
"在紀錄中點選任何一場已完成的對決，即可查看對戰結果詳情與對局統計（如步數、各回合得分等）。"),
icon:"🎬"}
,
{
title:t("guide.web.history_title",
"對戰記錄 (Battle Records) — 觀看重播與防清理"),
desc:t("guide.web.history_desc_2",
"詳情頁面內提供各局完整影片錄影，點擊即可重放觀看您 Agent 的實際對弈表現。"),
icon:"🎥"}
,
{
title:t("guide.web.history_title",
"對戰記錄 (Battle Records) — 觀看重播與防清理"),
desc:t("guide.web.history_desc_3",
"為了節省伺服器硬碟，影片會定期自動清理。您可以點選「釘選精彩」將高光表現永久保留！"),
icon:"📌"}
],
[t]),
[p,
i]=l.useState(null),
[u,
w]=l.useState(!!localStorage.getItem("token")),
[E,
m]=l.useState(0),
[b,
h]=l.useState([]),
[B,
$]=l.useState(!1),
[c,
n]=l.useState([]),
[f,
g]=l.useState(!1),
[d,
y]=l.useState("roster"),
[j,
k]=l.useState("players"),
[F,
L]=l.useState(null),
[H,
T]=l.useState(null),
[I,
W]=l.useState(null),
[O,
Y]=l.useState(!1),
[D,
ae]=l.useState(null),
[X,
S]=l.useState(!1),
R=async()=>{
const s=[`rl_roster_guide_${
r}
`,
`rl_lobby_guide_${
r}
`,
`rl_leaderboard_guide_${
r}
`,
`rl_history_guide_${
r}
`,
"world_map_3d",
"podium_leaderboard",
"character_console",
"achievements_fitting_room",
"camera_checkin"];
if(s.forEach(_=>{
localStorage.removeItem(`rl_guide_seen_guest_${
_}
`)}
),
u)try{
for(const _ of s)await J.post("/users/me/guides",
{
guide_key:_,
value:!1}
)}
catch(_){
console.error("[RLBattleHub] Failed to reset guides on backend:",
_)}
window.location.reload()}
,
[A,
M]=l.useState(null),
[G,
z]=l.useState(!1),
[ie,
ee]=l.useState(0),
[ce,
$e]=l.useState(()=>localStorage.getItem("rl_particles")!=="false"),
[de,
xe]=l.useState([]),
Fe=()=>{
$e(s=>{
const _=!s;
return localStorage.setItem("rl_particles",
String(_)),
_}
)}
;
l.useEffect(()=>{
const s=()=>{
w(!!localStorage.getItem("token"))}
;
return window.addEventListener("auth-change",
s),
()=>window.removeEventListener("auth-change",
s)}
,
[]),
l.useEffect(()=>{
r&&(J.get("/tavern/competitions/active").then(s=>{
const _=s.data.find(V=>V.id===r)??null;
i(_)}
).catch(s=>console.error("[RLBattleHub] competition fetch error:",
s)),
u?(J.get("/users/me").then(s=>m(s.data.id)).catch(s=>console.error("[RLBattleHub] user fetch error:",
s)),
$(!0),
tt(r).then(s=>h(s)).catch(s=>console.error("[RLBattleHub] slots fetch error:",
s)).finally(()=>$(!1)),
be(r).then(s=>M(s)).catch(()=>{
}
)):(m(0),
h([]),
$(!1),
M(null)),
g(!0),
he(r,
1,
20).then(s=>n(s)).catch(s=>console.error("[RLBattleHub] battles fetch error:",
s)).finally(()=>g(!1)))}
,
[r,
u]),
l.useEffect(()=>{
r&&J.get(`/tasks/competitions/${
r}
`).then(s=>xe(s.data)).catch(()=>xe([]))}
,
[r]);
const{
connect:le,
lastMessage:te}
=ne();
l.useEffect(()=>{
if(te&&typeof te=="object"){
const s=te;
s.type==="match-found"&&s.competition_id===r&&s.session_id&&(M(null),
ne.setState({
lastMessage:null}
),
o(`/rl/battles/${
s.session_id}
`))}
}
,
[te,
r,
o]),
l.useEffect(()=>{
u&&A?.in_queue&&le("/ws/notifications")}
,
[u,
A?.in_queue,
le]),
l.useEffect(()=>{
if(!r||!E||!A?.in_queue)return;
const s=setInterval(()=>{
be(r).then(_=>{
M(_),
_.status==="matched"&&_.matched_session_id&&(clearInterval(s),
M(null),
ne.setState({
lastMessage:null}
),
o(`/rl/battles/${
_.matched_session_id}
`))}
).catch(()=>{
}
)}
,
15e3);
return()=>clearInterval(s)}
,
[r,
E,
A?.in_queue,
o]),
l.useEffect(()=>{
if(!A?.in_queue){
ee(0);
return}
ee(A.wait_seconds??0);
const s=setInterval(()=>{
ee(_=>_+1)}
,
1e3);
return()=>clearInterval(s)}
,
[A?.in_queue,
A?.wait_seconds]);
const Le=s=>{
T(null),
L(s)}
,
Be=s=>{
L(null),
T(s)}
,
Me=async(s,
_)=>{
try{
await rt(r,
s),
h(V=>V.filter(q=>q.slot_index!==s))}
catch(V){
console.error("[RLBattleHub] delete slot error:",
V)}
}
,
Re=async s=>{
try{
const _=await st(r,
s.slot_index);
h(V=>V.map(q=>q.slot_index===_.slot_index?_:{
...q,
is_auto_battle:!1}
))}
catch(_){
console.error("[RLBattleHub] set auto battle error:",
_)}
}
,
ze=s=>{
h(_=>{
const V=_.findIndex(q=>q.slot_index===s.slot_index);
if(V!==-1){
const q=[..._];
return q[V]=s,
q}
return[..._,
s]}
),
L(null),
T(null)}
,
Te=async()=>{
if(D){
S(!0);
try{
const s=await nt(r,
D);
n(_=>[s,
..._]),
y("lobby")}
catch(s){
console.error("[RLBattleHub] solo trigger error:",
s)}
finally{
S(!1)}
}
}
,
pe=()=>{
g(!0),
he(r,
1,
20).then(s=>n(s)).catch(s=>console.error("[RLBattleHub] battles refresh error:",
s)).finally(()=>g(!1))}
,
De=async()=>{
if(D){
z(!0);
try{
le("/ws/notifications");
const s=await lt(r,
D);
M(s),
ee(0)}
catch(s){
console.error("[RLBattleHub] joinQueue error:",
s)}
finally{
z(!1)}
}
}
,
Ie=async()=>{
z(!0);
try{
await at(r),
M(null)}
catch(s){
console.error("[RLBattleHub] leaveQueue error:",
s)}
finally{
z(!1)}
}
,
Ae=p?.rl_max_slots??3,
He=new Map(b.map(s=>[s.slot_index,
s])),
se=c.filter(s=>s.participants.some(_=>_.user_id===E)),
Ve=b.length>0?b[0].player_tier??"UNRANKED":"UNRANKED",
qe=b.length>0?b[0].elo_rating:1e3,
Pe=b.length>0?b[0].elo_games_played:0,
me=b.length>0?b[0].best_score:null;
return e.jsxs("div",
{
className:`min-h-screen bg-[#141416] text-[#F3F4F6] p-4 sm:p-6 ${
ce?"ember-background":""}
`,
children:[e.jsxs("div",
{
className:"mb-6",
children:[e.jsx("button",
{
onClick:()=>o("/rl"),
className:"font-epic text-xs text-stone-500 hover:text-stone-300 mb-3 uppercase flex items-center gap-1 cursor-pointer",
children:t("rl.hub.back")}
),
e.jsxs("div",
{
className:"flex flex-col sm:flex-row sm:items-start justify-between gap-4",
children:[e.jsxs("div",
{
children:[e.jsx("h1",
{
className:"font-epic text-xl sm:text-2xl text-amber-500 uppercase tracking-wider",
children:p?.name??t("rl.hub.title")}
),
e.jsx("p",
{
className:"font-parchment text-xs text-stone-500 mt-1 uppercase font-bold tracking-widest",
children:p?.competition_type==="rl_pvp"?t("rl.hub.type_pvp"):t("rl.hub.type_solo")}
)]}
),
e.jsxs("div",
{
className:"flex flex-wrap items-center gap-2 sm:gap-3 shrink-0",
children:[e.jsxs("button",
{
onClick:R,
className:"font-epic text-[10px] text-amber-500 hover:text-amber-400 border border-amber-600/30 bg-stone-900/60 px-3 py-1.5 uppercase tracking-wider transition-colors cursor-pointer font-bold flex items-center gap-1",
children:[e.jsx("span",
{
children:"🔄"}
),
e.jsx("span",
{
children:t("rl.hub.reset_guide",
{
defaultValue:"重置指引"}
)}
)]}
),
e.jsx("button",
{
onClick:Fe,
className:"font-epic text-[10px] text-stone-400 hover:text-amber-500 border border-stone-850 bg-stone-900/60 px-3 py-1.5 uppercase tracking-wider transition-colors cursor-pointer",
children:t(ce?"rl.hub.disable_effects":"rl.hub.enable_effects")}
),
e.jsx("a",
{
href:`${
J.defaults.baseURL}
/rl/competitions/${
r}
/student-package`,
download:!0,
className:"font-epic text-[10px] text-stone-400 hover:text-amber-500 border border-stone-850 bg-stone-900/60 px-3 py-1.5 uppercase tracking-wider transition-colors",
children:t("rl.hub.download_starter")}
)]}
)]}
)]}
),
u&&e.jsxs("div",
{
className:"mb-6 rpg-stone-panel p-5 relative overflow-hidden flex flex-col md:flex-row items-center justify-between gap-6 border-2 border-[#3F3F46] rounded-[6px] shadow-2xl bg-gradient-to-r from-stone-900 via-stone-950 to-stone-900 group",
children:[e.jsx("div",
{
className:"absolute inset-0 bg-radial-gradient from-amber-950/15 via-transparent to-transparent pointer-events-none group-hover:scale-110 transition-transform duration-1000"}
),
e.jsxs("div",
{
className:"flex flex-col sm:flex-row items-center gap-5 z-10 w-full md:w-auto",
children:[e.jsxs("div",
{
className:"flex flex-col items-center gap-1.5 shrink-0",
children:[e.jsx("span",
{
className:"font-epic text-[9px] text-stone-500 uppercase tracking-widest font-bold",
children:t("rl.hub.current_tier_label",
{
defaultValue:"當前挑戰印記"}
)}
),
e.jsx(K,
{
tier:Ve,
size:"lg"}
)]}
),
e.jsx("div",
{
className:"hidden sm:block h-12 w-0.5 bg-stone-850"}
),
e.jsxs("div",
{
className:"text-center sm:text-left space-y-1",
children:[e.jsxs("div",
{
className:"flex items-center justify-center sm:justify-start gap-2",
children:[e.jsx("span",
{
className:"font-epic text-[11px] text-stone-400 uppercase tracking-wider",
children:t("rl.hub.challenger_status",
{
defaultValue:"挑戰者狀態："}
)}
),
e.jsx("span",
{
className:"font-pixel text-[10px] text-amber-500",
children:b.length>0?t("rl.slot.live_status",
{
defaultValue:"代理人配置中"}
):t("rl.hub.no_agent_configured")}
)]}
),
e.jsx("p",
{
className:"font-parchment text-xs text-stone-500 max-w-sm italic",
children:b.length>0?t("rl.hub.challenger_desc",
{
defaultValue:"代理人已註冊至戰陣中，隨時迎接全服之戰。"}
):t("rl.hub.challenger_empty_desc",
{
defaultValue:"尚未配置任何出戰代理人。請前往下方「我的陣容」進行上傳配置。"}
)}
)]}
)]}
),
e.jsxs("div",
{
className:"flex flex-wrap items-center justify-center md:justify-end gap-6 z-10 w-full md:w-auto border-t border-stone-800/60 md:border-t-0 pt-4 md:pt-0",
children:[p?.competition_type==="rl_solo"?e.jsxs("div",
{
className:"flex flex-col items-center md:items-end",
children:[e.jsx("span",
{
className:"font-epic text-[10px] text-stone-500 uppercase tracking-widest mb-0.5",
children:t("rl.hub.player_best_score",
{
defaultValue:"最佳分數"}
)}
),
e.jsx("span",
{
className:"font-pixel text-xl sm:text-2xl text-amber-400 font-bold text-shadow-glow",
children:me!=null?me.toFixed(1):"—"}
)]}
):e.jsxs("div",
{
className:"flex flex-col items-center md:items-end",
children:[e.jsx("span",
{
className:"font-epic text-[10px] text-stone-500 uppercase tracking-widest mb-0.5",
children:t("rl.hub.player_elo")}
),
e.jsx("span",
{
className:"font-pixel text-xl sm:text-2xl text-purple-400 font-bold text-shadow-glow",
children:Math.round(qe)}
)]}
),
e.jsx("div",
{
className:"h-8 w-0.5 bg-stone-850"}
),
e.jsxs("div",
{
className:"flex flex-col items-center md:items-end",
children:[e.jsx("span",
{
className:"font-epic text-[10px] text-stone-500 uppercase tracking-widest mb-0.5",
children:t("rl.hub.player_games")}
),
e.jsx("span",
{
className:"font-pixel text-xl sm:text-2xl text-stone-300 font-bold",
children:Pe}
)]}
),
p?.competition_type!=="rl_solo"&&e.jsx("div",
{
className:"hidden lg:block max-w-[120px] text-right",
children:e.jsx("p",
{
className:"font-parchment text-[9px] text-stone-600 uppercase tracking-wider leading-relaxed",
children:t("rl.hub.player_elo_note")}
)}
)]}
)]}
),
e.jsx("div",
{
className:"grid grid-cols-2 gap-2 sm:flex sm:flex-row sm:gap-1 border-b border-stone-800 pb-3 sm:pb-0 mb-6",
children:jt.map(s=>e.jsx("button",
{
onClick:()=>y(s.id),
className:`font-epic text-[11px] sm:text-xs px-3 py-2.5 sm:py-2 uppercase tracking-wider transition-colors cursor-pointer text-center rounded-[2px] shrink-0 ${
d===s.id?"text-amber-500 bg-stone-900/60 border border-amber-600/50 sm:border-0 sm:border-b-2 sm:border-amber-600 sm:bg-transparent -mb-px font-bold":"text-stone-500 bg-stone-950/40 border border-stone-850 sm:border-0 sm:bg-transparent hover:text-stone-300"}
`,
children:t(`rl.hub.tabs.${
s.id}
`)}
,
s.id))}
),
d==="roster"&&e.jsx("div",
{
children:u?B?e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/50 animate-pulse py-6 text-center",
children:t("rl.hub.loading_slots")}
):e.jsxs(e.Fragment,
{
children:[e.jsx(re,
{
guideKey:`rl_roster_guide_${
r}
`,
npcName:t("guide.web.roster_title",
"🛡️ 陣容軍師"),
steps:C,
variant:"card"}
),
e.jsx("div",
{
className:"grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4",
children:Array.from({
length:Ae}
,
(s,
_)=>_).map(s=>e.jsx(xt,
{
slot:He.get(s)??null,
slotIndex:s,
onUploadClick:Le,
onDeleteClick:Me,
onEditClick:Be,
onStatsClick:_=>W(_),
onSetAutoBattle:Re,
sandboxLimits:p?.rl_memory_mb!=null&&p?.rl_timeout_seconds!=null?{
memory_mb:p.rl_memory_mb,
timeout_sec:p.rl_timeout_seconds}
:null,
sandboxPackages:p?.rl_sandbox_packages??null}
,
s))}
),
b.length>0&&e.jsx("div",
{
className:"mt-4 text-center",
children:e.jsx("button",
{
onClick:()=>y("lobby"),
className:"font-pixel text-xs text-purple-400 hover:text-purple-300 uppercase",
children:t("rl.hub.go_to_lobby")}
)}
)]}
):e.jsx(fe,
{
mode:"inline",
title:t("game_lock.roster_title"),
message:t("game_lock.roster_message")}
)}
),
d==="lobby"&&e.jsx("div",
{
children:u?e.jsxs(e.Fragment,
{
children:[e.jsx(re,
{
guideKey:`rl_lobby_guide_${
r}
`,
npcName:t("guide.web.lobby_title",
"⚔️ 競技場官員"),
steps:v,
variant:"card"}
),
b.length===0?e.jsxs("div",
{
className:"bg-stone-900/30 p-6 mb-6 text-center border-2 border-dashed border-stone-850 rounded-[3px]",
children:[e.jsx("p",
{
className:"font-parchment text-sm text-stone-500 mb-3 font-bold",
children:t("rl.hub.no_agent_configured")}
),
e.jsx("button",
{
onClick:()=>y("roster"),
className:"font-epic text-xs text-amber-500 hover:underline uppercase cursor-pointer",
children:t("rl.hub.go_to_roster")}
)]}
):A?.in_queue?e.jsxs("div",
{
className:"flex flex-col items-center justify-center py-8 bg-stone-950/90 border border-stone-850 rounded-[4px] p-6 mb-6 w-full gap-4 shadow-inner relative overflow-hidden h-64",
children:[e.jsx("div",
{
className:"absolute inset-0 z-0 opacity-40 pointer-events-none",
children:e.jsx(gt,
{
waitSeconds:ie}
)}
),
e.jsxs("div",
{
className:"relative w-20 h-20 sm:w-24 sm:h-24 flex items-center justify-center z-10",
children:[e.jsx("div",
{
className:"absolute inset-0 border-4 border-double border-amber-600/30 rounded-full runic-circle-outer"}
),
e.jsx("div",
{
className:"absolute inset-2 border-2 border-dashed border-amber-600/40 rounded-full runic-circle-inner"}
),
e.jsx("div",
{
className:"w-8 h-8 rounded-full bg-gradient-to-tr from-amber-600 to-red-750 animate-ping absolute opacity-70"}
),
e.jsx("div",
{
className:"w-8 h-8 rounded-full bg-amber-600 flex items-center justify-center font-epic text-sm text-stone-950 font-bold z-10 shadow-lg border border-amber-700",
children:"⚔"}
)]}
),
e.jsxs("div",
{
className:"flex flex-col items-center gap-1 text-center px-4 z-10",
children:[e.jsxs("span",
{
className:"font-epic text-xs sm:text-sm text-amber-500 animate-pulse tracking-wider",
children:[t("rl.hub.finding_opponents"),
" ",
t("rl.hub.waiting_elapsed",
{
count:ie}
)]}
),
e.jsx("span",
{
className:"font-parchment text-[10px] sm:text-[11px] text-stone-500 italic",
children:t("rl.hub.finding_opponents")}
)]}
),
e.jsx("button",
{
onClick:Ie,
disabled:G,
className:"mt-2 bg-stone-900 border border-stone-800 text-stone-400 hover:text-red-400 hover:border-red-800/50 font-epic text-xs py-2 px-6 rounded-[2px] transition-all cursor-pointer z-10",
children:t("rl.hub.cancel_matchmaking")}
)]}
):e.jsxs("div",
{
className:"bg-stone-900/30 border border-stone-800 p-4 sm:p-5 mb-6 flex flex-col sm:flex-row items-start sm:items-center gap-4 rounded-[4px]",
children:[e.jsxs("div",
{
className:"flex flex-col gap-1 flex-1 min-w-0 w-full",
children:[e.jsx("span",
{
className:"font-epic text-[10px] text-stone-400 uppercase tracking-wide",
children:t("rl.hub.active_agent")}
),
e.jsxs("select",
{
value:D??"",
onChange:s=>ae(Number(s.target.value)),
className:"bg-stone-950 border border-stone-850 text-stone-200 px-3 py-2.5 font-parchment text-sm focus:outline-none focus:border-amber-650 rounded-[2px] w-full sm:max-w-xs cursor-pointer",
children:[e.jsx("option",
{
value:"",
children:t("rl.hub.select_agent")}
),
b.map(s=>e.jsx("option",
{
value:s.id,
children:s.name}
,
s.id))]}
)]}
),
p?.competition_type==="rl_pvp"?e.jsxs("div",
{
className:"flex gap-3 w-full sm:w-auto",
children:[e.jsx("button",
{
onClick:De,
disabled:!D||G,
className:"flex-1 sm:flex-none bg-gradient-to-b from-amber-500 to-amber-700 hover:from-amber-600 hover:to-amber-800 disabled:opacity-40 disabled:cursor-not-allowed text-stone-950 font-epic text-xs py-3.5 px-5 border border-amber-800 rounded-[2px] shadow-sm hover:shadow-md transition-all uppercase tracking-wider cursor-pointer font-bold",
children:G?"...":t("rl.hub.start_matchmaking")}
),
e.jsx("button",
{
onClick:()=>D&&Y(!0),
disabled:!D,
className:"shrink-0 bg-stone-950 border border-stone-850 hover:border-amber-600/50 text-stone-400 hover:text-amber-500 font-epic text-xs py-3.5 px-5 rounded-[2px] transition-all uppercase cursor-pointer",
children:t("rl.hub.direct_challenge")}
)]}
):e.jsx("button",
{
onClick:Te,
disabled:!D||X,
className:"w-full sm:w-auto bg-gradient-to-b from-amber-500 to-amber-700 hover:from-amber-600 hover:to-amber-800 disabled:opacity-40 disabled:cursor-not-allowed text-stone-950 font-epic text-xs py-3.5 px-6 border border-amber-800 rounded-[2px] transition-all uppercase tracking-wider cursor-pointer font-bold",
children:t(X?"rl.result.loading":"rl.hub.solo_challenge")}
)]}
),
e.jsxs("div",
{
className:"flex items-center justify-between mb-3",
children:[e.jsx("span",
{
className:"font-epic text-[10px] text-stone-400 uppercase tracking-wider",
children:t("rl.hub.my_recent_battles")}
),
e.jsx("button",
{
onClick:pe,
disabled:f,
className:"bg-stone-900 border border-stone-850 text-stone-400 font-epic text-xs py-1.5 px-3 hover:border-amber-600 hover:text-amber-500 disabled:opacity-40 transition-colors uppercase cursor-pointer rounded-[2px]",
children:t(f?"rl.result.loading":"rl.hub.refresh_battles")}
)]}
),
f?e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/50 animate-pulse py-6 text-center",
children:t("rl.result.loading")}
):se.length===0?e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/40 py-6 text-center",
children:t("rl.hub.no_battles")}
):e.jsxs("div",
{
className:"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
children:[se.slice(0,
10).map(s=>e.jsx(je,
{
session:s,
currentUserId:E}
,
s.id)),
se.length>10&&e.jsx("button",
{
onClick:()=>y("history"),
className:"font-pixel text-xs text-rpg-paper/40 hover:text-rpg-paper text-center py-2 uppercase",
children:t("rl.hub.view_all_battles",
{
count:se.length}
)}
)]}
)]}
):e.jsx(fe,
{
mode:"inline",
title:t("game_lock.lobby_title"),
message:t("game_lock.lobby_message")}
)}
),
d==="leaderboard"&&e.jsxs("div",
{
children:[e.jsx(re,
{
guideKey:`rl_leaderboard_guide_${
r}
`,
npcName:t("guide.web.leaderboard_title",
"🏆 榮譽記錄官"),
steps:a,
variant:"card"}
),
e.jsxs("div",
{
className:"flex gap-2 mb-2",
children:[e.jsx(_e,
{
active:j==="players",
onClick:()=>k("players"),
children:t("teams.playerRanking",
"個人排行")}
),
e.jsx(_e,
{
active:j==="teams",
onClick:()=>k("teams"),
children:t("teams.teamRanking",
"戰隊排行")}
)]}
),
j==="players"&&e.jsx(ht,
{
competitionId:r,
isSolo:p?.competition_type==="rl_solo"}
),
j==="teams"&&e.jsx(it,
{
competitionId:r}
)]}
),
d==="tasks"&&e.jsxs("div",
{
className:"space-y-3",
children:[de.length===0&&e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/40 py-6 text-center",
children:"尚無任務"}
),
de.map(s=>e.jsxs("div",
{
className:"rounded border border-gray-600 bg-black/40 p-3 flex items-center justify-between",
children:[e.jsxs("div",
{
children:[e.jsx("div",
{
className:"font-pixel text-sm text-rpg-paper",
children:s.task.title}
),
e.jsx("div",
{
className:"font-pixel text-xs text-rpg-paper/50 mt-0.5",
children:s.task.description}
)]}
),
e.jsx("span",
{
className:`font-pixel text-xs ml-4 shrink-0 ${
s.is_unlocked?"text-emerald-400":"text-rpg-paper/40"}
`,
children:s.is_unlocked?"已完成":`${
t(`tasks.${
s.task.condition_type}
`,
s.task.condition_type)}
 ≥ ${
s.task.required_value}
`}
)]}
,
s.task.id))]}
),
d==="history"&&e.jsxs("div",
{
children:[e.jsx(re,
{
guideKey:`rl_history_guide_${
r}
`,
npcName:t("guide.web.history_title",
"🎬 戰況轉播員"),
steps:N,
variant:"card"}
),
e.jsxs("div",
{
className:"flex items-center justify-between mb-3",
children:[e.jsx("span",
{
className:"font-pixel text-[10px] text-rpg-paper/40 uppercase",
children:t("rl.hub.all_battles_title")}
),
e.jsx("button",
{
onClick:pe,
disabled:f,
className:"bg-black/40 border border-gray-600 text-rpg-paper font-pixel text-xs py-1.5 px-3 hover:border-rpg-gold hover:text-rpg-gold disabled:opacity-40 transition-colors uppercase",
children:t(f?"rl.result.loading":"rl.hub.refresh")}
)]}
),
f?e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/50 animate-pulse py-6 text-center",
children:t("rl.history.loading")}
):c.length===0?e.jsx("p",
{
className:"font-pixel text-xs text-rpg-paper/40 py-6 text-center",
children:t("rl.history.empty")}
):e.jsx("div",
{
className:"grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
children:c.map(s=>e.jsx(je,
{
session:s,
currentUserId:E}
,
s.id))}
)]}
),
(F!==null||H!==null)&&e.jsx(pt,
{
competitionId:r,
slotIndex:F??H.slot_index,
existingSlot:H,
envName:p?.rl_env_name??"",
onSuccess:ze,
onCancel:()=>{
L(null),
T(null)}
}
),
O&&D!==null&&e.jsx(ft,
{
competitionId:r,
attackerSlotId:D,
maxPlayers:p?.rl_max_players_per_battle??2,
currentUserId:E,
onSuccess:s=>{
n(_=>[s,
..._]),
Y(!1),
y("lobby")}
,
onCancel:()=>Y(!1)}
),
I&&e.jsx(mt,
{
slot:I,
isSolo:p?.competition_type==="rl_solo",
onClose:()=>W(null)}
)]}
)}
;
export{
Et as default}
;

