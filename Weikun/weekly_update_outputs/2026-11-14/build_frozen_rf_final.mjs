import fs from "node:fs/promises";
import {Presentation,PresentationFile} from "file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1112-737-0_26.1112.737.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const dir="Weikun/weekly_update_outputs/2026-11-14";
const path="Weikun/random_forest_trajectory_outputs/frozen_rf_2020_test_2021_2023/metrics.csv";
const [header,...raw]=(await fs.readFile(path,"utf8")).trim().split(/\r?\n/).map(r=>r.split(","));
const rows=raw.map(r=>Object.fromEntries(header.map((k,i)=>[k,r[i]])));
const extra=JSON.parse(await fs.readFile(dir+"/frozen_rf_slide_metrics.json","utf8"));
const deck=Presentation.create({slideSize:{width:960,height:540}});
const navy="#15334F", bg="#EDF5FA", panel="#DBEBED", teal="#00847E", gray="#4D627A";
const pct=n=>(100*Number(n)).toFixed(1)+"%";
const dec=(n,k=3)=>Number(n).toFixed(k);
const count=n=>Number(n).toLocaleString("en-US");
function box(s,x,y,w,h,fill="none",geometry="rect"){
 return s.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:"none",width:0}});
}
function txt(s,v,x,y,w,h,size=18,color=navy,bold=false){
 const a=box(s,x,y,w,h,"none","textbox");a.text=v;
 a.text.style={typeface:"Arial",fontSize:size,color,bold,insets:{left:0,right:0,top:0,bottom:0},verticalAlignment:"middle"};
}
function page(title,subtitle){
 const s=deck.slides.add();s.background.fill=bg;box(s,48,38,864,49,navy);
 txt(s,title,55,38,850,49,30,"#FFFFFF",true);
 if(subtitle)txt(s,subtitle,55,98,850,34,19,gray);
 s.speakerNotes.text="Source: "+path+" and the corresponding protocol and prediction archives.";
 return s;
}
function foot(s,message,y=468){txt(s,message,55,y,850,   27,15,gray);}
function table(s,values,widths,y,h){
 const t=s.tables.add({rows:values.length,columns:widths.length,left:48,top:y,width:864,height:h,columnWidths:widths,values});
 t.borders.assign({style:"solid",fill:"#AAC6CF",width:.7});
 for(let r=0;r<values.length;r++)for(let c=0;c<widths.length;c++){
  const cell=t.getCell(r,c);cell.fill=r===1?"#CCE2E5":panel;
  cell.text.style={typeface:"Arial",fontSize:r===0?16:18,color:navy,bold:r===0||c===0};
 }
}
async function chart(s,name,y,h){
 s.images.add({blob:await fs.readFile(dir+"/"+name+".png"),contentType:"image/png",position:{left:48,top:y,width:864,height:h},alt:name.replaceAll("_"," ")});
}
let s=page("From 2020 Development to Frozen Testing","The final Random Forest checkpoint was fitted on Dec 23, 2020.");
for(const [i,label,date,detail] of [
 [0,"Initial training","Mar 1–Apr 29, 2020","First 60-day fitting window"],
 [1,"Rolling validation","Apr 30–Dec 28, 2020","Weekly refits and warning\nthreshold calibration"],
 [2,"Frozen testing","Jan 2021–Dec 2023","Daily inputs with fixed trees,\nevent rule and threshold"]
]){
 const x=48+i*294;box(s,x,170,276,176,panel);
 txt(s,label,x+14,183,250,32,22,teal,true);txt(s,date,x+14,225,250,29,19,navy,true);
 txt(s,detail,x+14,264,250,55,17);
}
txt(s,"585 NJ ZIPs",55,380,250,38,27,navy,true);
txt(s,"1,092 forecast origins",350,380,320,38,27,navy,true);
txt(s,"3-day horizon",680,380,220,38,27,navy,true);
foot(s,"The model predicts three future days at each origin. The warning score must exceed the fixed threshold of 0.");

s=page("The Frozen Model Detected 83% of Events","2021–2023 retrospective evaluation across 585 New Jersey ZIPs");
table(s,[["Test period","Event detection","Warning precision","Average\nprecision","Mean warning\nlead time"],...rows.slice(0,4).map((r,i)=>[
 i?r.period:"2021–2023 overall",pct(r.event_recall)+"\n"+count(r.detected)+" / "+count(r.events),pct(r.warning_precision)+"\n"+count(r.correct_warnings)+" / "+count(r.warnings),dec(r.average_precision),dec(r.mean_lead_days,2)+" days"])],[190,180,180,145,169],145,277);
foot(s,"Pooled AP uses all eligible ZIP-day scores. Median warning lead was one day in every year.",448);
foot(s,"Detection uses confirmation dates. Warning precision uses issue dates.",475);

s=page("Warning Precision Fell Across the Test Years","Event detection ranged from 81.9% to 84.5%.");
await chart(s,"frozen_rf_yearly_detection",144,297.6);
txt(s,"About 75 in 100 warnings were correct in 2021, compared with 55 in 100 in 2023.",55,451,850,42,19,teal,true);

s=page("False Warnings Peaked in 2022","False-warning counts, exposure-adjusted rates and event frequency");
table(s,[["Year","False\nwarnings","False warnings per\n1,000 eligible ZIP-days","Positive\nZIP-days","Average\nprecision"],...extra.years.map(r=>[
 r.period,count(r.false_alerts),dec(r.false_per_1000,2),(100*r.positive_origin_share).toFixed(2)+"%",dec(r.average_precision)])],[115,143,263,170,173],149,232);
txt(s,"2023 had the lowest warning precision and the lowest false-warning burden.",55,401,850,38,19,teal,true);
foot(s,"Positive ZIP-days had a rule-defined event confirmation within the next three days.",454);
foot(s,"Eligible ZIP-days are days with sufficient history and no active event at the forecast origin.",481);

s=page("Warnings Usually Gave One Day of Lead Time","Lead-time distribution as a share of all eligible events");
await chart(s,"frozen_rf_lead_distribution",148,288);
const leads=extra.lead_counts.flatMap(r=>r.slice(2)).reduce((a,b)=>a+b,0);
txt(s,count(leads)+" of "+count(rows[0].events)+" events ("+pct(leads/rows[0].events)+") were detected at least two days early.",55,444,850,35,20,teal,true);
foot(s,"Lead is measured to the date the case-surge rule confirms the event.",477);

s=page("Delta and Early Omicron Performance","The windows reflect calendar periods defined using national surveillance context.");
table(s,[["Calendar window","Event\ndetection","Warning\nprecision","AP","Mean lead","Residual Moran’s I\nDays 1 / 2 / 3"],...rows.slice(4,6).map((r,i)=>[
 i?"Early Omicron\nDec 1, 2021–Mar 19, 2022":"Delta\nJul 1–Sep 27, 2021",pct(r.event_recall),pct(r.warning_precision),dec(r.average_precision),dec(r.mean_lead_days,2)+" days",
 [r.moran_day_1,r.moran_day_2,r.moran_day_3].map(v=>dec(v)).join(" / ")])],[240,105,105,71,107,236],149,216);
txt(s,"Early Omicron had higher warning precision and stronger residual spatial clustering.",55,388,850,40,19,teal,true);
foot(s,"Moran’s I averages daily residual clustering across ZIPs using the original geographic KNN8 weights.",451);
s.speakerNotes.text+=" Early Omicron extends the project emergence window to the end of BA.1 predominance. CDC source https://www.cdc.gov/mmwr/volumes/71/wr/mm7134a3.htm";

s=page("A Successful Warning and a Missed Event","Two illustrative 2022 events from the same ZIP ("+extra.zip+")");
await chart(s,"frozen_rf_zip_examples",148,296);
foot(s,"The Apr 2 event triggered a warning on Mar 31. The Mar 22 event had no score above 0",447);
foot(s,"on any of the three eligible days before confirmation.",474);
s.speakerNotes.text+=" Illustrative pair selected by requiring the same ZIP and year, a two-day successful lead, and three eligible missed-event origins with scores at or below 0.";

s=page("What the Retrospective Test Supports","The frozen 2020 model continued to identify most rule-defined case surges.");
for(const [i,label,detail] of [
 [0,"Detection","The model detected 4,062 of 4,891 eligible events across the three test years."],
 [1,"Reliability and timing","Warning precision ranged from 55.4% to 74.7% by year. Typical lead was one day."],
 [2,"Validation before operational use","Replay using records as they became available to measure the effect of reporting delays."]
]){
 const y=155+i*102;
 box(s,48,y,864,88,panel);txt(s,label,62,y+8,830,29,21,teal,true);
 txt(s,detail,62,y+40,830,33,18);
}
foot(s,"This retrospective test uses onset-dated records and the project’s case-surge definition.",476);

await fs.mkdir(dir+"/.final_previews",{recursive:true});
for(const [i,slide] of deck.slides.items.entries()){
 const b=await deck.export({slide,format:"png",scale:1});
 await fs.writeFile(dir+"/.final_previews/slide"+(i+1)+".png",new Uint8Array(await b.arrayBuffer()));
}
await (await PresentationFile.exportPptx(deck)).save(dir+"/Frozen_RF_Final_Testing_Slide_Options.pptx");
