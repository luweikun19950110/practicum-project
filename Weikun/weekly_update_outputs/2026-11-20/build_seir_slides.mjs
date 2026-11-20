import fs from "node:fs/promises";
import path from "node:path";
import {pathToFileURL} from "node:url";
import {Presentation,PresentationFile} from "file:///C:/Program%20Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1118-904-0_26.1118.904.0_x64__3k8sg7r9htsxt/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs";
const dir=path.resolve("Weikun/weekly_update_outputs/2026-11-20");
const data=JSON.parse(await fs.readFile(path.join(dir,"slide_data.json"),"utf8"));
const deck=Presentation.create({slideSize:{width:960,height:540}});
const navy="#15334F",bg="#EDF5FA",panel="#DBEBED",teal="#00847E",gray="#4D627A";
const pct=v=>(Number(v)*100).toFixed(1)+"%";
const dec=(v,n=3)=>Number(v).toFixed(n);
const num=v=>Number(v).toLocaleString("en-US");
const rf=data.overall.find(r=>r.model==="Random Forest");
const seir=data.overall.find(r=>r.model==="SEIR");
const index=[];
function shape(s,x,y,w,h,fill="none",geometry="rect"){
 return s.shapes.add({geometry,position:{left:x,top:y,width:w,height:h},fill,line:{fill:"none",width:0}});
}
function text(s,v,x,y,w,h,size=18,color=navy,bold=false){
 const a=shape(s,x,y,w,h,"none","textbox");a.text=v;
 a.text.style={typeface:"Arial",fontSize:size,color,bold,insets:{left:0,right:0,top:0,bottom:0},verticalAlignment:"middle"};
}
function page(title,subtitle){
 const s=deck.slides.add();s.background.fill=bg;shape(s,48,38,864,49,navy);
 text(s,title,55,38,850,49,30,"#FFFFFF",true);
 if(subtitle)text(s,subtitle,55,99,850,34,19,gray);
 index.push(title);
 s.speakerNotes.text="Source: Weikun/seir_outputs/frozen_2020_test_2021_2023/metrics.csv and protocol.json; matched RF results from Weikun/random_forest_trajectory_outputs/frozen_rf_2020_test_2021_2023. SEIR is an exploratory incidence benchmark with causal daily state reconstruction. Illustrative latent/infectious durations 3/5 days. No parameter refits in testing.";
 return s;
}
function foot(s,v,y=470){text(s,v,55,y,850,30,15,gray);}
function callout(s,v,y=427){text(s,v,55,y,850,36,20,teal,true);}
function table(s,values,widths,y=150,height=240,font=18){
 const t=s.tables.add({rows:values.length,columns:widths.length,left:48,top:y,width:864,height,columnWidths:widths,values});
 t.borders.assign({style:"solid",fill:"#AAC6CF",width:.7});
 for(let r=0;r<values.length;r++)for(let c=0;c<widths.length;c++){
  const cell=t.getCell(r,c);cell.fill=r===1?"#CCE2E5":panel;
  cell.text.style={typeface:"Arial",fontSize:r===0?16:font,color:navy,bold:r===0||c===0};
 }
}
async function picture(s,name,y=145,h=305){
 s.images.add({blob:await fs.readFile(path.join(dir,"figures",name+".png")),contentType:"image/png",
  position:{left:48,top:y,width:864,height:h},alt:name.replaceAll("_"," ")});
}
function contentRows(s,items){
 items.forEach(([label,value],i)=>{
  const y=154+i*92;shape(s,48,y,864,80,panel);
  text(s,label,63,y+7,830,27,21,teal,true);
  text(s,value,63,y+35,830,37,18);
 });
}
let s=page("SEIR Adds a Mechanistic Forecast Benchmark","Predict daily new cases from transitions between epidemic states.");
["Susceptible","Exposed","Infectious","Removed"].forEach((name,i)=>{
 const x=48+i*221;shape(s,x,172,201,104,panel);
 text(s,["S","E","I","R"][i],x,181,201,46,36,teal,true);
 text(s,name,x+11,229,180,31,20);
 if(i<3)text(s,"→",x+201,194,20,40,16);
});
text(s,"Daily case prediction",55,317,850,34,25,teal,true);
text(s,"Integrate the E-to-I flow over each future day.",55,355,850,34,24,navy,true);
text(s,"Recorded onsets update the local state. The forecast then advances three days.",55,399,850,35,19);
foot(s,"State reconstruction assumes one recorded onset per modeled E-to-I transition.");
s.speakerNotes.text+=" Standard SEIR compartments are adapted here with a recorded-onset observation proxy. I is infectious prevalence. Daily forecast is integrated sigma E, not I.";

s=page("The Comparison Uses the Same Test Panel","585 NJ ZIPs, 1,092 daily origins and the same three-day prediction targets");
contentRows(s,[
 ["Fit in 2020","Estimate each ZIP’s beta from mature targets through Dec 23 in the final 60-day window."],
 ["Freeze for 2021–2023","Hold beta and the assumed 3-day latent / 5-day infectious durations fixed."],
 ["Update and score daily","Reconstruct state from recent observed cases. Apply the original event rule and threshold 0."]
]);
foot(s,"The SEIR zero threshold is shared with the existing RF protocol. No SEIR threshold optimization.");
s.speakerNotes.text+=" SEIR uses 43 shared mature three-horizon training origins per ZIP after 14 within-window warmup days. Daily local reconstruction uses trailing 60 days and a trailing three-day mean for E. RF remains the saved Dec 23, 2020 model.";

s=page("SEIR Detected More Events with Lower Precision","Matched 2021–2023 retrospective evaluation");
table(s,[["Model","Event detection","Warning precision","Average\nprecision","Mean lead"],...[rf,seir].map(r=>[
 r.model,pct(r.event_recall)+"\n"+num(r.detected)+" / "+num(r.events),
 pct(r.warning_precision)+"\n"+num(r.correct_warnings)+" / "+num(r.warnings),
 dec(r.average_precision),dec(r.mean_lead_days,2)+" days"])],[170,190,190,145,169],154,231);
callout(s,"SEIR detected 257 more events and generated 476 more false warnings.",409);
foot(s,"Median lead was one day for both models. Overall AP uses all eligible ZIP-day scores.");

s=page("Detection and Precision Across Test Years","SEIR detection was higher in each year, while warning precision was lower.");
await picture(s,"yearly_detection_precision",146,315);
foot(s,"Both models had lower precision in 2023. Recorded event frequency also fell.");

s=page("SEIR Produced More False Warnings","Compare total counts and rates per 1,000 eligible ZIP-days.");
const exp=data.exposure.filter(r=>r.period!=="2021–2023 overall");
table(s,[["Year","RF false\nwarnings","SEIR false\nwarnings","RF rate","SEIR rate"],...["2021","2022","2023"].map(y=>{
 const a=exp.find(r=>r.period===y&&r.model==="Random Forest");
 const b=exp.find(r=>r.period===y&&r.model==="SEIR");
 return [y,num(a.false_warnings),num(b.false_warnings),dec(a.false_per_1000,2),dec(b.false_per_1000,2)];
})],[135,185,185,179,180],154,230);
callout(s,"Pooled false-warning rate was 3.18 for RF and 3.99 for SEIR.",408);
foot(s,"Both models have identical eligible ZIP-days and a continuous seven-day warning cooldown.");

s=page("Average Precision Favored RF Overall","The score ranks whether a new event will confirm within the next three days.");
table(s,[["Test period","RF AP","SEIR AP","Positive ZIP-days"],...["2021","2022","2023"].map(y=>{
 const a=data.yearly.find(r=>r.period===y&&r.model==="Random Forest");
 const b=data.yearly.find(r=>r.period===y&&r.model==="SEIR");
 return ["Year "+y,dec(a.average_precision),dec(b.average_precision),(100*a.positive_origin_share).toFixed(2)+"%"];
})],[200,180,180,304],153,232);
callout(s,"Pooled AP was 0.487 for RF and 0.479 for SEIR.",410);
foot(s,"Event prevalence changes across years. AP comparisons use the same eligible origins for both models.");

s=page("Most Successful Warnings Came One Day Early","Lead-time shares use all 4,891 eligible events as the denominator.");
await picture(s,"lead_distribution",153,319);
foot(s,"At least two days early: RF 15.5% of all events, SEIR 17.2%. Confirmation follows the case-surge rule.",480);

s=page("SEIR Had Lower Case Forecast Error","ZIP-level errors pooled across all matched 2021–2023 forecasts");
await picture(s,"forecast_errors",148,310);
callout(s,"Trajectory MAE was 0.826 for RF and 0.730 for SEIR.",445);
foot(s,"Trajectory RMSE was 1.490 for RF and 1.460 for SEIR. These are descriptive point estimates.",480);

s=page("Both Forecasts Smoothed the Omicron Peak","Day 3 forecasts and actual recorded onsets across the same 585 ZIPs");
await picture(s,"omicron_paths",150,319);
foot(s,"Trailing seven-day means plotted by target date. Aggregate paths complement the ZIP-level scores.",480);
s.speakerNotes.text+=" Forecasts are made three days before the displayed target date. The trailing mean is for visualization only and is not used in warning scores.";

s=page("Delta and Early Omicron Show the Same Tradeoff","Fixed parameters and threshold throughout both calendar windows");
const variantRows=[];
for(const period of ["Delta","Early Omicron (emergence through BA.1)"]){
 for(const name of ["Random Forest","SEIR"]){
  const r=data.variants.find(r=>r.period===period&&r.model===name);
  variantRows.push([period==="Delta"?"Delta":"Early Omicron",name,pct(r.event_recall),pct(r.warning_precision),dec(r.average_precision),dec(r.mean_lead_days,2)]);
 }
}
table(s,[["Window","Model","Detection","Precision","AP","Mean lead\n(days)"],...variantRows],
 [155,170,140,140,115,144],153,257,17);
foot(s,"Delta: Jul 1–Sep 27, 2021. Early Omicron: Dec 1, 2021–Mar 19, 2022.",437);
foot(s,"These windows provide national variant context. ZIP-level variant labels are unavailable.",472);

s=page("SEIR Had Less Residual Spatial Clustering","Mean daily global Moran’s I across the 585 ZIP residuals");
await picture(s,"residual_moran",145,300);
foot(s,"Original geographic KNN8 weights, row-standardized after symmetrizing. Descriptive means.",455);
foot(s,"Positive values indicate clustering of similar forecast errors under the selected weights.",482);

s=page("The Pattern Persisted Across Duration Assumptions","Each SEIR scenario fits beta using 2020 data and then freezes its parameters.");
table(s,[["Latent / infectious\ndurations","Event detection","Warning precision","AP","Trajectory\nMAE"],...data.sensitivity.map((r,i)=>[
 ["2 days / 4 days","3 days / 5 days","5 days / 7 days"][i],
 pct(r.event_recall),pct(r.warning_precision),dec(r.average_precision),dec(r.trajectory_mae)])],
 [230,170,180,124,160],154,234,18);
callout(s,"Detection stayed near 88.3%. Precision ranged from 63.9% to 65.6%.",409);
foot(s,"These illustrative durations assess sensitivity. They do not estimate biological disease durations.");

s=page("Sparse Training Histories Limited Parameter Fits","Diagnostics from the 585 ZIP-specific beta estimates");
await picture(s,"transmission_parameters",145,290);
callout(s,"74 ZIPs fitted beta = 0, including 10 with no E or I signal in the fit origins.",438);
foot(s,"Median beta was "+dec(data.beta_median)+" per day. Local surveillance states make beta a benchmark parameter.",480);
s.speakerNotes.text+=" Beta is bounded [0,2]. Of 585 ZIPs, 575 had a fitted optimization and 10 had no exposed/infectious state over training origins. Reported beta is not presented as an identified biological reproduction number.";

s=page("How to Interpret This SEIR Benchmark","An exploratory short-horizon comparison using retrospective onset records");
contentRows(s,[
 ["Observation assumption","Recorded onsets proxy the E-to-I flow. Under-ascertainment and reporting delays are unmodeled."],
 ["Daily state approximation","Reconstruct local states from 60 days of records. This resets earlier removals outside the forecast."],
 ["Scope of the comparison","No explicit vaccination, reinfection or commuting model. Prior test inspection limits confirmatory claims."]
]);
foot(s,"The fixed 3-day / 5-day durations and unit reporting assumption are baseline modeling choices.");

s=page("SEIR Adds a Different Detection–Precision Tradeoff","The benchmark supports a comparison across monitoring priorities.");
contentRows(s,[
 ["More events detected","SEIR reached 88.3% detection with 65.0% warning precision."],
 ["Higher warning reliability","RF reached 83.1% detection with 68.7% precision and slightly higher AP."],
 ["Similar retrospective lead time","Both had a median one-day lead. Reporting-time replay is needed to assess usable warning time."]
]);
foot(s,"These findings compare the implemented frozen models and shared warning rule.");

await fs.mkdir(path.join(dir,"previews"),{recursive:true});
for(const [i,slide] of deck.slides.items.entries()){
 const b=await deck.export({slide,format:"png",scale:1});
 await fs.writeFile(path.join(dir,"previews","slide_"+String(i+1).padStart(2,"0")+".png"),new Uint8Array(await b.arrayBuffer()));
}
const candidate=path.join(dir,".build","SEIR_RF_Comparison_candidate_v5.pptx");
await (await PresentationFile.exportPptx(deck)).save(candidate);
await fs.writeFile(path.join(dir,"slide_index.txt"),index.map((s,i)=>(i+1)+". "+s).join("\n"),"utf8");
console.log("Rendered slides:",index.length);
