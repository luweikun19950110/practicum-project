import fs from "node:fs/promises";
import crypto from "node:crypto";
import path from "node:path";
import {pathToFileURL} from "node:url";
const skill="C:/Users/41240/.codex/plugins/cache/openai-primary-runtime/presentations/26.1118.11504/skills/presentations";
const runtime="C:/Program Files/WindowsApps/OpenAI.CodexPrimaryRuntime.v26-1118-904-0_26.1118.904.0_x64__3k8sg7r9htsxt/dependencies";
process.env.RUNTIME_NODE_MODULES=path.join(runtime,"node/node_modules");
const dir=path.resolve("Weikun/weekly_update_outputs/2026-11-20");
const referencePath=path.resolve("Weikun/weekly_update_outputs/2026-11-14/Frozen_RF_Final_Testing_Slide_Options.pptx");
const nativeLink=fs.link;
fs.link=async(source,target)=>{
 try { await nativeLink(source,target); }
 catch(error) {
  if(error.code!=="EPERM") throw error;
  const {constants}=await import("node:fs");
  await fs.copyFile(source,target,constants.COPYFILE_EXCL);
 }
};
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,"container_tools/artifact_tool_utils.mjs")).href);
const owners=[3,5,6,10,12];
const result=await finalizePresentation({
 workspaceDir:dir,candidatePath:path.join(dir,".build/SEIR_RF_Comparison_candidate_v5.pptx"),
 finalPath:path.join(dir,".delivery/SEIR_RF_Testing_Slide_Options_v2.pptx"),
 pythonExecutable:path.join(runtime,"python/python.exe"),
 integrityValidatorPath:path.join(skill,"container_tools/inspect_presentation_package_integrity.py"),
 layoutValidatorPath:path.join(skill,"container_tools/inspect_presentation_layout_geometry.py"),
 layoutArgs:["--expected-slide-size-emu","9144000,5143500","--validate-bullet-geometry","--validate-heading-fit",
 ...owners.flatMap(n=>["--require-native-table-slide",String(n)])],
 requiredNativeTableOwnerSlides:owners,verifyArtifactToolImport:true,
 fontPolicy:{basis:"reference",families:["Arial"],referencePath,referenceSha256:crypto.createHash("sha256").update(await fs.readFile(referencePath)).digest("hex")},
 receiptPath:path.join(dir,".build/validation_v2.json")
});
console.log(JSON.stringify(result));

await fs.copyFile(path.join(dir,".delivery/SEIR_RF_Testing_Slide_Options_v2.pptx"),path.join(dir,"SEIR_RF_Testing_Slide_Options.pptx"));
