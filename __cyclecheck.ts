import { LivingCell } from "./src/physics/cell";
const CC = { g1s:2.0, g2m:3.5, sDur:16, mDur:5, abscissionDelayS:2, growthPerSimS:0.06 };
const c = { biomass:1.0, phase:"G1", phaseTime:0, abscissionPending:false, abscissionAge:0 };
let resolved = false;
const cell = new LivingCell(undefined, 0.85, true);
let lastEC = 0.85;
for (let f=0; f<3000 && !resolved; f++) {
  const simDt = Math.min(0.08, Math.max(0.005,((1/60)*5)/2));
  cell.step(simDt, 2); const s = cell.snapshot();
  const healthy = s.status==="healthy"; const energyCharge = lastEC; lastEC = s.energyCharge;
  const simSeconds = (1/60)*5;
  const permitted = true /*fallback*/ && energyCharge>0 && true /*regen*/ && healthy;
  if (c.abscissionPending) { c.phaseTime=Math.min(c.phaseTime,CC.mDur); c.abscissionAge+=simSeconds; }
  else if (permitted) c.biomass += CC.growthPerSimS*simSeconds*Math.min(1,energyCharge);
  if (!c.abscissionPending) {
    if (permitted) c.phaseTime+=simSeconds; else if (c.phase==="G1") c.phaseTime=0;
    if (c.phase==="G1"){ if(c.biomass>=CC.g1s&&permitted){c.phase="S";c.phaseTime=0;} }
    else if (c.phase==="S"){ if(c.phaseTime>=CC.sDur){c.phase="G2";c.phaseTime=0;} }
    else if (c.phase==="G2"){ if(c.biomass>=CC.g2m&&permitted){c.phase="M";c.phaseTime=0;} }
    else if (c.phaseTime>=CC.mDur){ c.abscissionPending=true; c.abscissionAge=0; c.phaseTime=CC.mDur; }
  } else if (c.abscissionAge>=CC.abscissionDelayS){ resolved=true; console.log(`DIVIDED at frame ${f} (~${(f/60).toFixed(1)}s), biomass ${c.biomass.toFixed(2)}`); }
  if (f%300===0) console.log(`f=${f} phase=${c.phase} biomass=${c.biomass.toFixed(2)} pt=${c.phaseTime.toFixed(1)} absc=${c.abscissionPending}`);
}
if(!resolved) console.log("NEVER DIVIDED in 50s");
