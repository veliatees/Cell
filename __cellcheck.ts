import { LivingCell } from "./src/physics/cell";
const c = new LivingCell(undefined, 0.85, true);
let healthy = 0, total = 0;
for (let f = 0; f < 1200; f++) {
  const simDt = Math.min(0.08, Math.max(0.005, ((1/60)*5)/2));
  c.step(simDt, 2);
  const s = c.snapshot();
  total++; if (s.status === "healthy") healthy++;
  if (f % 300 === 0) console.log(`f=${f} status=${s.status} EC=${s.energyCharge.toFixed(2)}`);
}
console.log(`healthy fraction: ${(healthy/total*100).toFixed(0)}%`);
