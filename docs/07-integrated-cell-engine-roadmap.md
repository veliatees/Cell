# Integrated Cell Engine Roadmap

Last verified: 2026-06-19

Bu dosya projenin yeni ana yonunu tarif eder: tek ekranda guzel gorunen bir
hucre modeli degil, kaynakli, olculebilir, olasiliksal, cok-dilli ve
dogrulanabilir bir hepatocyte hucre motoru.

Hedef, "programlanmis animasyon" degil. Hedef, organellerin kendi islerini
yaptigi, birbirleriyle madde/enerji/sinyal alisverisi kurdugu, islerin her zaman
basarili olmadigi, basarisizliklarin da rastgele ama biyolojik duruma bagli
oldugu bir dijital hucre tanimi kurmak.

## 1. Non-negotiable kurallar

1. Gerceklik bozulmayacak.
   - Gorsel katman biyolojiyi uydurmayacak; sadece motorun durumunu
     gosterecek.
   - Her organel, her molekul havuzu, her akim ve her ariza icin birim,
     kaynak, belirsizlik ve varsayim seviyesi tutulacak.
   - "Random olsun" yeterli degil. Olasiliklar hucrenin durumuna bagli olacak.

2. Tipatip hedefi davranis seviyesinde tanimlanacak.
   - Atom atom tam hucre yapmak pratik degil.
   - Ama atomik/kimyasal gerceklik parametrelere, kinetiklere, enerji
     maliyetlerine, transport kurallarina ve hata olasiliklarina tasinacak.
   - Simulasyon "cizim olarak hucre" degil, "hucre gibi karar veren ve
     materyal isleyen motor" olacak.

3. Hucre tipi net: hepatocyte.
   - Bu proje genel "animal cell" olarak kalmayacak.
   - Baslangic referans hucre: insan hepatocyte.
   - Polarity zorunlu: sinusoidal taraf ve canalicular taraf farkli olacak.
   - Albumin sekresyonu, glikojen, glukoneogenez, ure cycle, bile acid/bilirubin
     transport, CYP detox, glutathione ve zonation sisteme girecek.

4. Her organel kendi dinamiklerine sahip olacak.
   - Organeller sabit dekor olmayacak.
   - Konum, yas, hasar, kapasite, enerji durumu, organeller arasi temaslar,
     cargo trafigi ve stres cevabi zamanla degisecek.
   - Her organel modulunun kendi cycle'i, input/outputlari, riskleri ve kalite
     kontrolu olacak.

5. Hata ve kayiplar acikca modellenecek.
   - Uretilen seyler otomatik olarak dogru yere gitmeyecek.
   - Protein yanlis katlanabilir, mRNA degrade olabilir, vesicle kaybolabilir,
     Golgi cargo'yu yanlis hedefe koyabilir, lysosome kapasitesi dolabilir,
     mitochondria ATP uretip lokal ihtiyaca yetistiremeyebilir.
   - Her cargo'nun kaderi izlenebilir olacak.

6. Simulasyon deterministic animasyon degil, hybrid stochastic engine olacak.
   - Yuksek kopya sayili metabolitler icin ODE/SDE/field.
   - Dusuk kopya sayili olaylar icin event/hazard/Gillespie benzeri sistem.
   - Cargo ve vesicle gibi nesneler icin packet/agent temsili.
   - Nadir ariza ve stressor olaylari icin state-conditioned hazard.

## 2. Nihai sistem hedefi

Hedef sistem birbiriyle bagli uc katmandan olusacak:

1. Scientific engine
   - Hucrenin "gercek" durumu burada tutulur.
   - Organeller, metabolit havuzlari, membran transportlari, cargo packet'lari,
     stress response, yaslanma, stochastic event'ler ve validasyon burada
     calisir.

2. Visualization client
   - TypeScript/Three.js tabani kalir.
   - Gorevi engine snapshot'larini goruntulemek, debug etmek, karsilastirmak ve
     kullanicinin hucreyle etkilesmesini saglamaktir.
   - Bilimsel kararlar burada alinmaz.

3. Experiment/ML layer
   - Parametre tarama, kalibrasyon, validation, virus/bakteri/stressor
     senaryolari, reinforcement learning ve optimizasyon burada calisir.
   - Bu katman hucreyi disaridan etkiler; hucre motorunun ic kurallarini
     uydurmaz.

## 3. Dil ve teknoloji bolusumu

| Katman | Dil/teknoloji | Sorumluluk | Neden |
| --- | --- | --- | --- |
| Web visualizer | TypeScript + Three.js | 3D goruntu, UI, zaman kontrolu, debug panelleri, snapshot replay | Mevcut repo burada. Interaktif 3D icin hizli, tarayicida calisir, kullaniciya direkt gosterilir. |
| Scientific orchestrator | Python | Ana hucre motoru, deney runner'i, validasyon, parametre fitting, veri IO | Systems biology, ML, bilimsel kutuphaneler ve hizli prototipleme icin en uygun merkez. |
| Biochemical network | SBML + libRoadRunner | ODE/SBML pathway simulasyonu, steady-state, sensitivity, metabolic/signaling subnetleri | SBML standart model degisim formati; libRoadRunner C/C++ core ve Python baglantilariyla hizli. |
| Rule-based biology | PySB + BioNetGen/Kappa | Protein-protein etkilesimleri, receptor signaling, state-heavy reaction rules | Tek tek tum reaksiyonlari elle yazmadan biyolojik rule set kurmak icin uygun. |
| Ion/Ca/electrical dynamics | Brian2 | Membran potansiyeli, calcium pulse, channel gating, electrophysiology-benzeri ODE/SDE alt sistemleri | Brian2 Python tabanli, denklemleri esnek tanimlar ve performans icin C++ codegen kullanabilir. Whole-cell core degil, alt modul. |
| High-performance packet/space engine | Rust veya C++ | Vesicle/cargo agent'lari, spatial indexing, cok sayida packet/organel hareketi | Python yavas kalirsa native cekirdek gerekir. Rust guvenli bellek yonetimi icin, C++ PhysiCell/libRoadRunner ekosistemi icin avantajli. |
| Multicell/tissue bridge | PhysiCell/C++ | Cok hucre, ECM, microenvironment, secretion/uptake, cell-cell davranislar | 100+ hucre ve doku seviyesine gecis icin hazir C++ cell-agent framework. |
| ML/optimization | PyTorch once, sonra JAX opsiyonel | Parameter fitting, surrogate model, RL/treatment policy search | PyTorch ekosistemi daha pratik; JAX differentiable scientific computing icin sonraki alternatif. |
| Data | JSON, HDF5/Zarr/Parquet, SQLite | UI snapshot, trajectory, experiment registry, parameter provenance | JSON UI icin; HDF5/Zarr/Parquet uzun trajectory icin; SQLite deney kaydi icin. |

Karar: TypeScript'i atmayacagiz. TypeScript goruntu ve deneyim katmani olacak.
Bilimsel otorite Python merkezli engine'e tasinacak. Native kod ancak performans
gercekten yetmediginde yazilacak.

## 4. Onerilen repo mimarisi

```text
src/
  main.ts                         # Three.js visualizer
  physics/                        # Mevcut TS modelleri; gecis ve gorsel debug icin korunur
  engineClient/                   # Python engine snapshotlarini okuyan client

engine/
  pyproject.toml
  cell_engine/
    core/
      cell_definition.py
      state.py
      units.py
      time.py
      random.py
      provenance.py
    organelles/
      nucleus.py
      mitochondria.py
      er.py
      golgi.py
      lysosome.py
      peroxisome.py
      ribosome.py
      proteasome.py
      membrane.py
      cytoskeleton.py
    processes/
      metabolism.py
      trafficking.py
      stress_response.py
      autophagy.py
      apoptosis.py
      senescence.py
      hepatocyte.py
    stochastic/
      hazard.py
      gillespie.py
      packet_fate.py
      uncertainty.py
    io/
      snapshots.py
      schema.py
      sbml.py
      trajectories.py
    validation/
      invariants.py
      reference_ranges.py
      experiments.py
    ml/
      calibration.py
      policy_env.py

models/
  sbml/
    hepatocyte_metabolism.xml
    calcium_signaling.xml
  pysb/
    receptor_signaling.py
    apoptosis_switch.py
  brian2/
    membrane_calcium.py

native/
  cargo_engine_rs/                # Opsiyonel Rust engine
  cargo_engine_cpp/               # Opsiyonel C++ engine, gerekiyorsa

physicell/
  hepatocyte_microenvironment/     # Cok hucre/doku bridge

docs/
  07-integrated-cell-engine-roadmap.md
  sources.md
```

Bu dosya yapisi entegrasyon sinirlarini simdiden sabitler: TS gorsel, Python
bilimsel, SBML/PySB/Brian2 alan modelleri, native performans, PhysiCell
multicell.

## 5. Hucre tanimi: CellDefinition

Engine'in merkezi nesnesi `CellDefinition` olacak. Bu tanim hucreyi "hangi
organeller var" diye degil, "hangi madde ve surecler hangi bolmelerden geciyor"
diye tarif edecek.

```text
CellDefinition
  species: human
  cell_type: hepatocyte
  zone: periportal | midlobular | pericentral | unknown
  geometry:
    radius_um
    polarity_axis
    sinusoidal_membrane_region
    canalicular_membrane_region
  compartments:
    cytosol
    nucleus
    rough_er
    smooth_er
    golgi
    mitochondria_pool
    lysosome_pool
    peroxisome_pool
    plasma_membrane
    bile_canalicular_face
    sinusoidal_face
  pools:
    ATP, ADP, AMP
    NADH, NAD+, NADPH, GSH, GSSG
    glucose, glycogen, lactate, pyruvate
    fatty_acids, acetyl_CoA
    ammonia, urea_cycle_intermediates
    bile_acids, bilirubin_conjugates
    amino_acids
    ROS
    Ca2+
    misfolded_protein
    damaged_organelle_mass
  organelles:
    nucleus module
    mitochondria modules
    ER modules
    Golgi modules
    lysosome modules
    peroxisome modules
    ribosome/proteasome modules
    membrane transporter modules
    cytoskeleton module
  processes:
    transcription
    splicing
    mRNA export
    translation
    protein folding
    ERAD/proteasome
    glycosylation
    vesicle trafficking
    metabolism
    detox
    bile export
    autophagy
    apoptosis
    senescence
  stochastic_policy:
    seed
    event_mode
    packet_mode
    hazard_models
    uncertainty_model
  validation_targets:
    source_id
    range
    units
    confidence
```

Bu tanimdan sonra gorsel sahne sadece bir "projection" olur. Engine icin hucre,
renkli nesneler degil; compartment'lar, flux'lar, cargo packet'lar, kalite
kontrol basamaklari ve stress response loop'laridir.

## 6. Olasilik modeli

Sistemdeki her ariza veya basari su mantikla tanimlanacak:

```text
P(event | state, organelle, cargo, environment, age, stress, source_confidence)
```

Sabit yuzde ile "her frame fault at" yapilmayacak. Olasilik, hucrenin ic
durumuna bagli hesaplanacak.

Temel hazard formu:

```text
hazard = base_rate
       * f(ATP)
       * f(ROS)
       * f(Ca2+)
       * f(pH)
       * f(crowding)
       * f(organelle_age)
       * f(organelle_damage)
       * f(substrate_saturation)
       * f(stress_response_state)
```

Kullanilacak stochastic yontemler:

| Olay tipi | Model | Ornek |
| --- | --- | --- |
| Yuksek kopya sayili metabolit | ODE veya SDE | ATP/ADP, ROS, lactate, NADH |
| Reaction network | SBML/libRoadRunner | Glycolysis, urea cycle, detox subnet |
| Nadir ayrik olay | Gillespie/hazard event | DNA damage, vesicle loss, mitophagy trigger |
| Cargo kaderi | Packet-level Bernoulli + route graph | ER -> Golgi -> membrane cargo |
| Channel/receptor state | Markov/Brian2/PySB | Open/closed/inactivated channel, receptor activation |
| Organellerin yaslanmasi | Hazard + repair/autophagy | Mitochondrial damage accumulation |
| Belirsiz literatur degeri | Parameter distribution | Base rate range, fitted prior |

Her olasilik icin `assumption_level` tutulacak:

| Seviye | Anlam |
| --- | --- |
| measured | Direkt olculmus referans aralik var. |
| literature_derived | Literaturden turetilmis veya uyarlanmis. |
| fitted | Veriye uydurulmus. |
| placeholder | Gecici; UI'da ve dokumanda acikca isaretlenir. |

Bu proje icin kabul edilemez olan durum: placeholder bir orani gercek biyoloji
gibi gostermek. Kabul edilebilir olan durum: placeholder'i kullanmak ama
"varsayim" diye kaydetmek ve kalibrasyon hedefi yapmak.

## 7. Cargo ve routing modeli

Uretilen her sey otomatik olarak hedefe ulasmayacak. Iki temsil seviyesi olacak:

1. Flux mode
   - Hizi yuksek, kalabalik surecler icin kullanilir.
   - "ER'den Golgi'ye su kadar protein flux'i gitti; su kadari retained, su
     kadari degraded, su kadari misrouted" diye aggregate hesaplar.

2. Packet mode
   - Gorsel ve mekanistik olarak onemli cargo'lar icin kullanilir.
   - Her packet ayri izlenir.

`CargoPacket` tanimi:

```text
CargoPacket
  id
  species
  origin_compartment
  target_compartment
  current_location
  route_plan
  quality_score
  folding_state
  glycosylation_state
  age_s
  energy_cost_atp
  motor_dependency
  membrane_side_target
  fate:
    in_transit | delivered | retained | degraded | misrouted | lost | recycled
```

Route graph ornegi:

```text
nucleus -> cytosol                  # mRNA export
cytosol -> rough_ER                 # signal peptide/SRP targeting
rough_ER -> ER_quality_control
ER_quality_control -> Golgi         # basarili folding
ER_quality_control -> ERAD          # misfolded/degrade
Golgi -> sinusoidal_membrane        # albumin sekresyonu
Golgi -> canalicular_membrane       # bile transporter/cargo
Golgi -> lysosome                   # lysosomal enzyme sorting
endosome -> lysosome                # endocytosed material
damaged_mitochondrion -> autophagosome -> lysosome
```

Her edge'in basari olasiligi sabit degil; ATP, cytoskeleton durumu, Golgi
kapasitesi, ER stress, cargo kalitesi ve crowding'e bagli olacak.

## 8. Organel fonksiyon matrisi

### 8.1 Plasma membrane

Ana gorevler:

- Hucre ici/disi ayrimi.
- Secici transport.
- Ion dengesi ve membran potansiyeli.
- Receptor signaling.
- Endocytosis/exocytosis.
- Hepatocyte polarity: sinusoidal uptake ve canalicular export ayrimi.

Hepatocyte icin kritik transporter/receptor kategorileri:

- Glucose ve amino acid uptake.
- Fatty acid uptake.
- Bile acid uptake/export.
- Organic anion/cation transporter mantigi.
- ABC transporter mantigi.
- Na/K pump ve Ca2+ handling.
- Glycoprotein receptor/endocytosis mantigi.

Failure modes:

- Leak.
- Transporter saturation.
- Wrong-side localization.
- Receptor desensitization.
- Channel inactivation.
- Pump ATP shortage.
- Membrane repair failure.

Model:

- Brian2: ion/channel state ve Ca2+ pulse icin.
- PySB: receptor signaling icin.
- Python stochastic engine: transporter flux, saturation, mislocalization.
- TS: membrane proteinlerini gercek boyut oranlariyla, ancak gorsel olarak
  secilebilir LOD ile gosterir.

### 8.2 Nucleus

Ana gorevler:

- Genome state.
- Transcription.
- RNA processing/splicing.
- mRNA export.
- DNA damage sensing.
- DNA repair.
- Cell-cycle, apoptosis ve senescence kararlarinin ust kontrolu.

Failure modes:

- DNA damage.
- Repair failure.
- Transcription error.
- Splicing defect.
- mRNA export failure.
- Nuclear envelope stress/rupture.
- Telomere/age signal accumulation.

Model:

- Stochastic gene-expression bursts.
- PySB/SBML ile p53, NF-kB, stress decision gibi subnetler.
- Packet mode ile mRNA export.
- Age/damage hazard ile senescence/apoptosis threshold.

### 8.3 Ribosomes

Ana gorevler:

- Translation initiation/elongation/termination.
- Cytosolic protein uretimi.
- ER-targeted protein uretimi.
- Ribosome quality control.

Failure modes:

- Mistranslation.
- Ribosome stall.
- Amino acid shortage.
- mRNA degradation.
- Mis-targeting to ER.
- Ribotoxic stress.

Model:

- Flux mode: genel protein uretim hizi.
- Packet mode: secili protein/cargo uretimi.
- Hazard: amino acid, ATP/GTP cost, mRNA quality, ER capacity.

### 8.4 Endoplasmic reticulum

Rough ER ana gorevler:

- Secretory/membrane protein synthesis.
- Folding.
- Disulfide bond/glycosylation basamaklari.
- ER quality control.
- ERAD/proteasome'a yonlendirme.

Smooth ER ana gorevler:

- Lipid synthesis.
- Ca2+ storage.
- Hepatocyte detox/CYP activity.
- Drug/xenobiotic metabolism.

Failure modes:

- Protein misfolding.
- ER retention.
- UPR activation.
- ER stress overload.
- Calcium leak.
- CYP kaynakli ROS artisi.
- ERAD/proteasome bottleneck.

Model:

- SBML/PySB: UPR, ERAD, folding stress subnetleri.
- Python stochastic: folding success, retention, degradation.
- Packet routing: ER -> Golgi veya ERAD.
- Brian2: Ca2+ storage/release dinamikleri.

### 8.5 Golgi apparatus

Ana gorevler:

- Protein/lipid modification.
- Glycosylation maturation.
- Sorting.
- Vesicle budding.
- Lysosomal enzyme routing.
- Secretory ve membrane cargo yonlendirme.

Failure modes:

- Glycosylation error.
- Misrouting.
- Vesicle loss.
- Stack fragmentation.
- Sorting saturation.
- Wrong membrane face delivery.

Model:

- Packet route graph.
- State-conditioned route probabilities.
- Capacity queue.
- Hepatocyte polarity icin sinusoidal/canalicular target ayrimi.

### 8.6 Mitochondria

Ana gorevler:

- TCA/OXPHOS.
- ATP production.
- NADH/NAD+ balance.
- Fatty acid oxidation ile coupling.
- ROS production/control.
- Apoptosis gate.
- Hepatocyte ure cycle'in mitochondrial basamaklari.

Failure modes:

- Membrane potential loss.
- ATP output collapse.
- ROS leak.
- mtDNA damage.
- Mitophagy trigger.
- Apoptosis sensitization.
- Substrate overload.

Model:

- SBML/libRoadRunner: OXPHOS/TCA alt aglari.
- Python hazard: membrane potential, ROS, age, damage.
- Packet/event: mitophagy, mitochondrial fission/fusion approximation.
- Visualization: mitochondria sabit obje degil; yavas hareket, fission/fusion
  ve hasar renk/state degisimi.

### 8.7 Lysosome/endosome system

Ana gorevler:

- Endocytosed cargo degradation.
- Autophagy cargo degradation.
- Organelle turnover.
- pH-dependent enzyme activity.
- Receptor recycling.
- Pathogen/cargo processing.

Failure modes:

- pH loss.
- Enzyme deficiency.
- Overload.
- Incomplete degradation.
- Autophagy backlog.
- Membrane permeabilization.

Model:

- Queue/capacity system.
- pH state.
- Autophagy packet inflow.
- Degradation probability based on pH, enzyme capacity, cargo type, ATP.

### 8.8 Peroxisome

Ana gorevler:

- Very-long-chain fatty acid oxidation.
- H2O2/catalase balance.
- Lipid metabolism.
- ROS buffering.

Failure modes:

- Catalase capacity saturation.
- H2O2 leak.
- Fatty acid processing bottleneck.
- Peroxisome biogenesis/turnover failure.

Model:

- ODE/flux for fatty acid and H2O2 pools.
- Hazard tied to ROS, lipid load, peroxisome age.
- Cross-talk with mitochondria and ER.

### 8.9 Proteasome

Ana gorevler:

- Misfolded/damaged protein degradation.
- ERAD cargo degradation.
- Regulatory protein turnover.
- Antigenic peptide production path can be added for infection/immunity models.

Failure modes:

- Saturation.
- ATP shortage.
- Misfolded protein accumulation.
- Stress response escalation.

Model:

- Capacity-limited degradation.
- Input from ERAD and cytosolic quality control.
- Output to amino acid pool and stress markers.

### 8.10 Cytoskeleton and motor system

Ana gorevler:

- Organelle positioning.
- Vesicle transport.
- Cell polarity.
- Mechanical integrity.
- Mitochondria/ER/Golgi spatial organization.

Failure modes:

- Motor stall.
- Track disruption.
- Polarity loss.
- Vesicle traffic congestion.
- Organelle mispositioning.

Model:

- Spatial graph for tracks.
- Cargo velocity and stall probability.
- Energy-dependent motor activity.
- Organelles move with constrained random motion, not arbitrary screen noise.

### 8.11 Cytosol and metabolic fields

Ana gorevler:

- Metabolite diffusion.
- pH/ionic environment.
- Glycolysis and shared metabolite pools.
- Molecular crowding.
- Signal propagation.

Failure modes:

- ATP local shortage.
- pH shift.
- Ion imbalance.
- ROS spread.
- Crowding/transport slowdown.

Model:

- Field or compartment concentration.
- Diffusion delays for selected species.
- Local availability: "ATP produced" does not mean "ATP instantly usable
  everywhere".

### 8.12 Cross-organelle processes

Bu surecler tek bir organelin icinde degil, tum hucre aginda calisir:

- Autophagy.
- Mitophagy.
- UPR.
- Oxidative stress response.
- Apoptosis.
- Senescence.
- Energy crisis response.
- Detox response.
- Membrane repair.
- Protein quality control.

Her biri ayri state machine + biochemical subnet olarak tanimlanacak.

## 9. Hepatocyte-specific program

Bu proje artik genel hucre degil, hepatocyte-first olacak.

Zorunlu hepatocyte yetenekleri:

1. Glucose/glycogen control
   - Glucose uptake/release.
   - Glycogen synthesis/breakdown.
   - Energy state'e bagli decision.

2. Gluconeogenesis/lactate handling
   - Lactate/pyruvate conversion.
   - Energy and substrate dependent flux.

3. Urea cycle/ammonia detox
   - Ammonia input.
   - Mitochondria + cytosol bolmeli cycle.
   - ATP cost.
   - Failure: ammonia accumulation.

4. Bile acid/bilirubin handling
   - Uptake, conjugation, canalicular export.
   - Wrong-side routing ve export failure riskleri.

5. Albumin and secretory protein production
   - Nucleus -> ribosome/ER -> Golgi -> sinusoidal secretion.
   - Folding/glycosylation/routing loss.

6. CYP450/xenobiotic detox
   - Smooth ER detox flux.
   - NADPH/GSH cost.
   - ROS side effect.

7. Lipid metabolism
   - Fatty acid uptake, beta oxidation, triglyceride/VLDL abstraction.
   - ER/mitochondria/peroxisome interaction.

8. Redox balance
   - GSH/GSSG.
   - ROS generation and clearance.
   - Mitochondria/peroxisome/ER cross-talk.

9. Zonation
   - Periportal/pericentral differences configuration olarak tanimlanacak.
   - Ilk engine "unknown/mixed hepatocyte" ile baslayabilir ama zone parametresi
     bastan var olacak.

## 10. Stress response davranislari

Hucre stress altinda tek bir sey yapmaz. Stresin turune gore asamali cevap verir.

| Stress | Ilk cevap | Orta cevap | Kritik cevap |
| --- | --- | --- | --- |
| Low ATP | Tuketimi azalt, AMPK-benzeri energy alarm, transport yavaslat | Autophagy/mitophagy artir, nonessential synthesis azalt | Energy crisis, membrane pump failure, death risk |
| High ROS | Antioxidant response, GSH kullanimi | Damaged protein/organelle temizligi | DNA/mitochondria damage, apoptosis risk |
| ER stress | Folding yavaslat, chaperone/UPR artir | ERAD/proteasome yukunu artir | UPR failure, apoptosis risk |
| Ca2+ imbalance | Pump/channel compensation | Mitochondria/ER cross-talk | Apoptosis sensitization, membrane dysfunction |
| Protein misfolding | Proteasome/ERAD | Autophagy | Aggregate toxicity/senescence/death |
| Membrane leak | Repair, pump compensation | ATP cost artar | Ion collapse/death |
| Lysosome overload | Autophagy flux ayari | Backlog artisi | Incomplete clearance, damage accumulation |

Stress response de random degil. Threshold + hysteresis + probabilistic failure
mantigiyla calisacak. Yani ayni stres iki hucrede birebir ayni sonucu
vermeyebilir, ama cevap biyolojik olarak tutarli kalir.

## 11. Organel hareketi ve yasam suresi

Organeller sabit olmayacak. Ama ekranda rastgele savrulmayacaklar.

Hareket kurallari:

- Mitochondria: cytoskeleton boyunca yavas hareket, lokal ATP ihtiyacina
  yonelme, hasar durumunda mitophagy yoluna girme.
- ER: ag gibi davranir; nucleus ile baglanti ve mitochondria/Golgi temaslari
  onemli.
- Golgi: hucre polaritesine bagli konumlanir, vesicle traffic merkezi gibi
  davranir.
- Lysosome/endosome: cargo ve autophagy yukune gore hareket/konum degistirir.
- Peroxisome: ER/mitochondria/lipid yukuyla etkilesir.
- Ribosome: cytosolic veya ER-bound olabilir.

Yasam suresi/turnover:

| Nesne | Model |
| --- | --- |
| Mitochondria | Age + damage + fusion/fission abstraction + mitophagy hazard |
| Lysosome | Capacity/enzymatic health + turnover hazard |
| Peroxisome | Biogenesis/degradation turnover |
| ER/Golgi | Network health, fragmentation/repair state |
| Protein | Half-life distribution + proteasome/autophagy routing |
| mRNA | Half-life + translation/degradation competition |
| Cargo vesicle | Transit age + delivery/loss/degradation fate |

Bu sistem "yas geldi, sil" gibi basit olmayacak. Yas, hasar ve stress birlesip
hazard uretir.

## 12. Validation stratejisi

Her milestone kabul kriteriyle bitecek.

Validation katmanlari:

1. Invariant tests
   - Negatif konsantrasyon yok.
   - Atom/madde/charge/energy muhasebesi tanimli sinirlar icinde.
   - ATP cost olmadan ATP-costly process calismaz.
   - Cargo iki yerde ayni anda bulunmaz.

2. Qualitative biology tests
   - ATP dusunce nonessential synthesis yavaslar.
   - ROS artinca antioxidant/protein quality control cevabi artar.
   - ER stress artinca folding throughput duser, ERAD/UPR artar.
   - Transporter saturation olunca uptake/export lineer devam etmez.

3. Quantitative reference tests
   - Literaturden gelen araliklar eklendikce flux ve concentration hedefleri
     test edilir.
   - Bu aralik yoksa test "assumption bounded" diye isaretlenir.

4. Visual truth tests
   - UI'da gorulen cargo, organel state ve readout engine snapshot'i ile ayni
     olacak.
   - Gorsel LOD bilimsel state'i saklayabilir ama degistiremez.

5. Regression experiments
   - Her bilinen senaryo snapshot/trajectory olarak kaydedilir.
   - Model degisikligi eski davranisi bozduysa bunun bilerek mi oldugu yazilir.

## 13. ML ve virus/bakteri icin hazir mimari

Virus/bakteri ve ML gereksinimi engine sinirina bastan girer. Pathogen
dinamikleri ayri detay seviyesinde modellenir, ama bugunden observation/action,
stressor, cargo, receptor, membrane ve immune-like hook alanlari tasarima dahil
edilir.

ML icin hucre API'si:

```text
observation:
  metabolite pools
  organelle health
  cargo backlog
  stress markers
  membrane transport state
  gene/signaling state
  pathogen load when present

action:
  external nutrient/stressor change
  drug/intervention dose
  transporter/channel modulation
  pathway modulation
  immune-like intervention hook

reward:
  viability
  pathogen suppression
  ATP stability
  low ROS
  preserved secretion/detox function
  low unrealistic intervention penalty
```

Ilk ML hedefi RL degil, calibration olacak:

1. Parameter fitting.
2. Sensitivity analysis.
3. Bayesian/black-box optimization.
4. Surrogate model.
5. Calibrated model uzerinde RL policy search.

Neden: Hucre motoru biyolojik olarak zayifken RL koymak sadece yanlis bir
simulator'u optimize eder. Once validasyon, sonra policy.

## 14. Implementation milestones

### M014 - Integrated roadmap and engine boundary

Scope:

- Bu dokuman.
- README dokuman haritasi guncellemesi.
- Kaynak defterine scientific stack eklenmesi.

Acceptance:

- Projenin dil bolusumu ve cell engine hedefi net.
- TS visualizer ile Python engine siniri tanimli.

### M015 - Python engine skeleton

Status: implemented in [Milestone 015](milestones/015-python-engine-skeleton.md).

Scope:

- `engine/pyproject.toml`.
- `cell_engine.core` modulleri.
- `CellDefinition`, `CellState`, `Compartment`, `Pool`, `OrganelleState`.
- JSON snapshot schema.

Acceptance:

- Python testleri calisir.
- Tek bir hepatocyte definition JSON olarak uretilir.
- TS tarafindan okunabilir minimal snapshot export edilir.

### M016 - Organelle module interface

Status: implemented in [Milestone 016](milestones/016-organelle-module-interface.md).

Scope:

- Her organel icin ortak interface:
  - `inputs()`
  - `outputs()`
  - `step(dt, state, rng)`
  - `events()`
  - `health()`
  - `provenance()`
- Nucleus, mitochondria, ER, Golgi, lysosome, peroxisome, membrane, cytoskeleton
  stub'lari.

Acceptance:

- Her organel kendi state'ini tasir.
- Sabit dekor yok; her modul zamanla state degistirir.
- Ariza olasiliklari state-conditioned hazard'dan gelir.

### M017 - Cargo packet and routing engine

Status: implemented in [Milestone 017](milestones/017-cargo-routing-engine.md).

Scope:

- `CargoPacket`.
- Route graph.
- ER -> Golgi -> membrane/lysosome route'lari.
- Packet fate: delivered, retained, degraded, misrouted, lost.

Acceptance:

- Uretilen cargo otomatik hedefe gitmez.
- Misrouting/loss/degradation olasiliklari ATP, stress, cargo quality ve
  cytoskeleton state'e baglidir.
- UI snapshot'inda packet hareketi ve fate gorulur.

### M018 - Hepatocyte metabolism v1

Scope:

- ATP/ADP/AMP.
- Glucose/glycogen abstraction.
- Lactate/pyruvate abstraction.
- Mitochondrial ATP and ROS.
- Urea cycle simplified subnet.
- Detox NADPH/GSH cost.

Acceptance:

- ATP uretimi/tuketimi ayrik organel ve process kaynaklarindan gelir.
- ATP "her yerde aninda kullanilir" varsayimi kaldirilir; local availability
  veya delay modele girer.
- High detox load ROS ve energy cost yaratir.

### M019 - SBML/libRoadRunner bridge

Scope:

- SBML model load/run wrapper.
- libRoadRunner Python baglantisi.
- Subnetwork state'i engine pool'larina baglama.

Acceptance:

- En az bir SBML subnet deterministic olarak calisir.
- Engine snapshot'i SBML sonucunu gosterir.
- Units/provenance zorunlu hale gelir.

### M020 - PySB rule-based signaling

Scope:

- Receptor signaling veya apoptosis switch icin PySB model.
- Rule-based state engine baglantisi.

Acceptance:

- Rule-based subnet engine state'i etkiler.
- Receptor activation -> downstream marker -> organelle response akisi test
  edilir.

### M021 - Brian2 membrane/Ca module

Scope:

- Membrane potential/Ca2+ pulse/channel state icin Brian2 alt modulu.
- Python engine'e state exchange.

Acceptance:

- Brian2 hucrenin tamamini simule etmeye calismaz.
- Ion/channel/Ca subsystem olarak calisir.
- Membrane pump ATP shortage davranisi engine'e yansir.

### M022 - TS external snapshot mode

Scope:

- TS visualizer engine snapshot okur.
- Local replay ve live WebSocket/HTTP modu.
- UI readout'lari engine verisinden gelir.

Acceptance:

- Gorsel sahne kendi biyolojisini uretmez.
- Snapshot yoksa acik diagnostic gorunur.
- Render blank kalmaz.

### M023 - Validation harness

Scope:

- Reference range registry.
- Assumption/provenance report.
- Scenario tests.

Acceptance:

- Her parametre kaynak veya assumption seviyesiyle listelenir.
- Placeholder oranlar raporda gorunur.
- Regression trajectory kaydi baslar.

### M024 - PhysiCell bridge

Scope:

- Single-cell engine state'i multicell agent abstraction'a baglama.
- Microenvironment fields: nutrient, oxygen, waste, cytokine-like signals.

Acceptance:

- 100 hucre hedefi icin arayuz hazir olur.
- Tek hucre engine'i cok hucre davranisinin icine gomulebilir.
- Gorselde tek hucre debug ve cok hucre overview ayrilir.

### M025 - ML calibration and policy environment

Scope:

- Gymnasium-like environment.
- Calibration runner.
- Intervention action space.
- Reward/safety constraints.

Acceptance:

- ML modeli hucre kurallarini degistirmez; sadece parametre/intervention dener.
- Unrealistic action penalty vardir.
- Calibration ve RL ayridir.

## 15. Ilk uygulanacak teknik kararlar

1. Python package eklenecek ama TS app korunacak.
2. Engine snapshot schema once JSON olacak.
3. Python test runner `pytest`, type check `pyright` veya `mypy` olabilir.
4. SBML/libRoadRunner entegrasyonu engine skeleton'dan sonra gelir.
5. Brian2 sadece membrane/Ca/electrical alt sistem icin kullanilir.
6. Rust/C++ packet engine interface simdiden tanimlanacak; implementasyon Python
   profilinden sonra Rust veya C++ olarak secilecek.
7. Her placeholder biyolojik oran dokumanda ve runtime debug panelinde
   isaretlenecek.
8. UI'da "fault" olayi gereksiz sik gorunmeyecek; fault hazard'i normal hucre
   davranis araliklariyla kalibre edilecek.

## 16. Kaynak standartlari

Kaynak sirasina gore tercih:

1. Primary paper veya resmi standard/tool dokumani.
2. Textbook/NCBI Bookshelf/Cell Biology by the Numbers.
3. Review paper.
4. Database/model repository.
5. Gecici varsayim.

Her model dosyasi sunu gosterecek:

```text
parameter_name
value
unit
source
source_type
confidence
assumption_level
date_verified
notes
```

Kaynak olmadan biyolojik iddia UI'da kesin bilgi gibi gosterilmeyecek.

## 17. Resmi toolchain referanslari

- Brian simulator: https://briansimulator.org/
  - Python tabanli spiking/neural dynamics simulator; equation-based modelleme
    ve C++ code generation yetenekleri nedeniyle channel/Ca alt sistemleri icin
    uygun.
- libRoadRunner: https://github.com/sys-bio/roadrunner
  - SBML simulation icin C/C++ core ve Python/Julia baglantilari olan systems
    biology kutuphanesi.
- PySB: https://pysb.org/
  - Biochemical systems icin Python DSL; rule-based pathway modelleme icin
    uygun.
- PhysiCell: https://physicell.org/
  - C++ multicellular/tissue simulation framework; 100+ hucre ve
    microenvironment katmani icin ana aday.
- SBML: https://sbml.org/
  - Systems Biology Markup Language; pathway/network modellerinin standart
    degisim formati.
- Project source ledger: [sources.md](sources.md)

## 18. Kisa karar ozeti

- Hucre tipi: hepatocyte-first.
- Ana engine: Python.
- Gorsel: TypeScript/Three.js.
- Biochemical ODE: SBML/libRoadRunner.
- Rule-based signaling: PySB.
- Ion/Ca/electrical alt sistem: Brian2.
- Cok hucre: PhysiCell/C++ bridge.
- ML: once calibration, sonra RL.
- Olasilik: sabit random degil, state-conditioned hazard.
- Cargo: flux + packet hybrid.
- Dogruluk: kaynak, unit, validation, assumption seviyesi olmadan "gercek" diye
  kabul edilmeyecek.
