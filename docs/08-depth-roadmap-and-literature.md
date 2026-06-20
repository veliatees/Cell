# Cell — Derinlik Yol Haritası ve Literatür Temeli

> Amaç: motoru ~%3'lük bir iskeleden, gerçek bir hepatositi nicel olarak yansıtan
> bir sisteme taşımak. Bu dosya **(1)** yapılacakları ve **(2)** her biri için
> ciddi, kaynaklı bir literatür temelini içerir. Uygulama bundan sonra gelir
> (detoks/ölüm/doku işleri bu temel oturduktan sonra devam eder).
>
> İlke (değişmez): **doğruluk > anlaşılırlık.** Bir şeyi görselde anlaşılır
> yapmak doğruluktan ödün verdiriyorsa, görselde anlaşılır yapma — motor doğru
> kalsın, görsel sadece motorun durumunu göstersin.

---

## BÖLÜM 1 — Yapılacaklar (net hedefler)

1. **Kapsam: ~40-50 reaksiyondan yüzlerce reaksiyona.**
   Glikoliz/glukoneogenez, glikojen, TCA, OXPHOS, üre döngüsü, PPP, β-oksidasyon,
   de novo lipogenez, ketogenez, amino asit metabolizmasını tam topolojiyle kur.
   Hedef referans: iHepatocytes2322 / HEPATOKIN1 / Recon3D alt-ağları.

2. **Kaynaklı parametreler: sabitlerin TAMAMI literatürden.**
   Her enzim için Km/kcat/Vmax BRENDA + SABIO-RK'dan; her `placeholder` kalkacak,
   her sabit `source_id` + `assumption_level` taşıyacak.

3. **Validasyon: 5 hedeften onlarca-yüzlerce hedefe.**
   HMDB konsantrasyonları + 13C fluxomics + proteomik kopya sayıları ile geniş bir
   doğrulama paneli; her eklenen pathway kendi ölçülmüş hedefini kazanacak.

4. **Süreç çeşitliliği (hepsi "olması gerektiği" gibi, doğruluk öncelikli):**
   - Metabolizmayı tamamla (yukarıdaki kapsam).
   - Gen ifadesini/regülasyonunu gerçekçi yap (transkripsiyon faktörü, promoter
     durumu, hormonal kontrol).
   - **Sinyalleşme ağları** (insülin/glukagon/AMPK).
   - **Tam membran transportu** (NTCP, OATP, GLUT2, BSEP, MRP2, Na/K-ATPaz).
   - **Elektrofizyoloji / kalsiyum** (IP3R Ca osilasyonları, membran potansiyeli).
   - **Lipid metabolizması** (DNL, β-oksidasyon, VLDL sekresyonu).
   - **Sekresyon** (albumin: ER→Golgi→kan, konstitütif yol).
   - **DNA hasarı/tamiri** (NHEJ/HR + p53 karar ağı).

5. **Uzamsal: 1-B difüzyonu ana motora bağla** (ve 3-B'ye doğru: RDME).
   Voxel alanlarını gerçek reaksiyon ağıyla birleştir; ATP mikrodomainleri,
   Ca dalgaları, sinusoidal↔kanaliküler gradyanlar uzamsal olsun.

---

## BÖLÜM 2 — Literatür Temeli (alan alan, detaylı)

### A. Kapsam — hepatosit metabolik modelleri (referans alınacaklar)

Hepatosit, sistem biyolojisinde en çok modellenen insan hücresidir. Bizim
hedefimiz bu modellerin reaksiyon topolojisini ve kinetiklerini benimsemek.

- **iHepatocytes2322** (Mardinoglu et al., *Nat Commun* 2014). Hepatosite özgü
  genom-ölçekli model (GEM): **2322 gen**, HMR 2.0 veritabanı + Human Protein
  Atlas proteomiği üzerine kurulu, **kapsamlı lipid metabolizması** içerir.
  NAFLD'de serin eksikliğini öngördü. → Bizim için reaksiyon listesinin altın
  kaynağı; SBML olarak indirilebilir (BioModels MODEL1402200003).
- **HEPATOKIN1** (Berndt et al., *Nat Commun* 2018). Biyokimya-temelli **kinetik**
  çok-pathway hepatosit modeli: enerji, karbonhidrat, lipid, azot metabolizması;
  allosterik + hormon-bağımlı (reversibl fosforilasyon) regülasyon; her enzim için
  in-vitro deneylerden türetilmiş rate denklemleri; iç mitokondriyal membran
  elektrofizyolojisi (iyon transportu, membran potansiyeli, proton-motive force).
  Proteomikle ölçeklenmiş maksimal aktiviteler. → Bizim kinetik katmanımızın
  birebir referansı.
- **König et al.** (*PLoS Comput Biol* 2012), "Quantifying the Contribution of the
  Liver to Glucose Homeostasis." Glikoliz + glukoneogenez + glikojen
  metabolizmasının **hormonal kontrollü** (insülin/glukagon/epinefrin) ODE kinetik
  modeli; fosforile/defosforile enzim formları için ayrı rate yasaları. T2DM
  versiyonu hipoglisemi riskini öngördü.
- **Recon3D** (Brunk et al. 2018) ve **Human-GEM** (SysBioChalmers, GitHub):
  jenerik insan metabolik rekonstrüksiyonları (Recon3D ~10.000+ reaksiyon, ~13.000
  metabolik gen) — hepatosit alt-ağını bunlardan türetebiliriz.
- Diğer: **HepatoNet1**, iHepatocyte1154, redHUMAN (indirgenmiş GEM).

**Plan:** iHepatocytes2322'den çekirdek reaksiyon listesini al; kinetikleri
HEPATOKIN1 + König'den; bizim SSA/CLE motoruna `Reaction` olarak kodla.

### B. Kaynaklı parametreler — enzim kinetik veritabanları

- **BRENDA** (braunschweig). En kapsamlı enzim veritabanı: **~80.000 kcat**,
  **~169.000 Km** değeri; ayrıca Ki, IC50, spesifik aktivite, pH/sıcaklık. Organizma
  ve doku bilgisi var (insan/karaciğer filtrelenebilir).
- **SABIO-RK** (Wittig et al.). Elle-curate edilmiş, kalite-öncelikli: **>56.000 Km**,
  **>52.000 Vmax/kcat**; deney koşulları ve rate yasaları ayrı saklanır,
  **SBML export** eder → doğrudan modele aktarılabilir.
- Yeni yapısal-kinetik setler: IntEnzyDB, SKiD (structure-oriented).

**Plan:** her enzim için `EnzymeKinetics`'i (zaten glukokinaz/PFK/PK'da yaptığımız
gibi) BRENDA/SABIO-RK'dan doldur; insan + karaciğer + fizyolojik pH/sıcaklık
filtrele; `assumption_level="literature_derived"`; çoklu kayıt varsa aralık +
güven. Hedef: `placeholder` sayısını sıfıra indirmek.

### C. Validasyon — veri kaynakları ve yöntem

- **HMDB 5.0** (Wishart et al., *NAR* 2022). En kapsamlı insan metabolom
  veritabanı: yapılar, **fizyolojik konsantrasyonlar**, doku/biofluid lokasyonu,
  normal/anormal aralıklar, ilişkili enzim/transporter. → konsantrasyon
  doğrulama hedeflerinin ana kaynağı.
- **Fluxomics** (13C metabolik akış analizi + FBA): ölçülen alım/salgı hızlarından
  iç akışlar; bizim steady-state akışlarımızı bunlara karşı koyabiliriz.
- **Proteomik kopya sayıları** (Human Protein Atlas, PaxDb): enzim kopya sayıları →
  Vmax = kcat·[E] için doğrudan kullanılabilir (placeholder enzim konsantrasyonu
  yerine).
- Hepatotoksisite metabolomiği (örn. hidrazin/parasetamol biomarker setleri):
  pertürbasyon doğrulaması için.

**Plan:** `validation.py` panelini büyüt — her metabolit için HMDB aralığı,
her grounded enzim için fluks hedefi; "5/5" yerine onlarca hedefli bir skorkart,
emergent vs kalibre ayrımı korunarak.

### D. Süreç çeşitliliği

#### D1. Metabolizma (tam)
Yukarıdaki A + B. Eksik bloklar: PPP (NADPH üretimi — redoks modülümüzü besler),
TCA + OXPHOS (gerçek ATP üretimi; şu an "atp_regeneration" lump'ı bunu temsil
ediyor), ketogenez, amino asit katabolizması, glukoneogenez (üre döngüsüne
aspartat/fumarat bağlanır).

#### D2. Gen ifadesi / regülasyon
Şu an: tek gen, sabit hızlar, translational bursting (Thattai–van Oudenaarden).
Hedef: promoter durumları (on/off, two-state bursting — gerçek bursting
kaynağı), transkripsiyon-faktörü kontrolü, hormonal kontrol (örn. insülin → SREBP →
lipogenez genleri; glukagon → PEPCK/G6Pase). Ölçek: gerçek hepatositte ~10.000
ifade edilen gen; biz anahtar düzenleyici genlerle başlarız.

#### D3. Sinyalleşme ağları
- **İnsülin** (yemek sonrası): reseptör → PI3K/AKT → glikojen sentaz aktivasyonu,
  glukoneogenez baskılanması, lipogenez (SREBP-1c).
- **Glukagon** (açlık): GPCR → cAMP/PKA → glikojen fosforilaz, glukoneogenez,
  PEPCK/G6Pase indüksiyonu.
- **AMPK** (enerji sensörü): AMP/ATP oranına duyarlı; glikojen tükenmesi
  hepatositi katabolik sinyallere duyarlılaştırır (**AMPK/CRTC2** ekseni, *JCI*).
- İnsülin–glukagon ağı **bistabil** olabilir (metabolik homeostaz/hastalık).
- Araç: kural-tabanlı modelleme (**PySB / BioNetGen / Kappa**) — tüm reaksiyonları
  elle yazmadan reseptör/durum-ağırlıklı sinyalleşmeyi kurmak için. Bizim
  motorumuzda bunları `Reaction` setine derleyebiliriz.

#### D4. Tam membran transportu (hepatosit polaritesi)
Vektörel transport: sinüzoidal (bazolateral) alım → hücre → kanaliküler (apikal)
atım. Gerçek transporterlar:
- **Bazolateral:** Na⁺/K⁺-ATPaz (Na gradyanını ve membran potansiyelini kurar),
  **NTCP** (Na-bağımlı safra tuzu alımı), **OATP1B1/1B3** (Na-bağımsız organik
  anyon/safra tuzu/ilaç alımı), **GLUT2** (glukoz, çift yönlü).
- **Kanaliküler:** **BSEP** (safra tuzu atımı), **MRP2/cMOAT** (bilirubin
  glukuronidleri, GSH, sülfat/glukuronid konjugatları), **MDR3** (fosfolipid
  flippaz).
- Kinetik: Na/K-ATPaz, K⁺ kanalının kurduğu membran potansiyeline bağımlı; NTCP
  bu Na gradyanını kullanır. → elektrofizyoloji (D5) ile kuplaj.
Kaynak: *Physiology* (Molecular Mechanisms in Bile Formation), *J Hepatol*
(cholestasis transporter regülasyonu), DILI-transporter derlemeleri.

#### D5. Elektrofizyoloji / kalsiyum
Hepatosit **uyarılabilir değil** ama agonist-indüklü **Ca²⁺ osilasyonları** yapar:
- **IP3R** aracılı ER Ca salımı; PLC/G-protein geri besleme zamanlaması →
  pulsatil IP3 ve serbest Ca osilasyonları (frekans-kodlu sinyal).
- Stokastik IP3R modelleri (kanal kümeleri, açık/kapalı/inaktive Markov durumları).
- Membran potansiyeli: Na/K-ATPaz + K⁺ kanalı.
- Araç: **Brian2** (denklem-esnek ODE/SDE, C++ codegen) alt-modül olarak; ya da
  doğrudan bizim CLE motorunda Ca türlerini modelle.

#### D6. Lipid metabolizması
Denge: lipid arzı (DNL + dolaşımdan alım + adipoz lipoliz) vs kullanım
(β-oksidasyon + VLDL sekresyonu). Bileşenler:
- **De novo lipogenez:** asetil-CoA → malonil-CoA (ACC) → palmitat (FASN).
- **β-oksidasyon:** mitokondriyal + peroksizomal (VLCFA peroksizomda — bizde
  `very_long_chain_fatty_acids` havuzu zaten var).
- **VLDL biyogenezi/sekresyonu** (ApoB100, MTP). Steatoz = TG sentezi > VLDL
  sekresyonu (NAFLD mekanizması — doğrulanabilir patoloji).
- Ketogenez (β-oksidasyon fazlası → ketonlar).
Kaynak: iHepatocytes2322 (lipid odağı), MAFLD/NAFLD derlemeleri, *Circ Res* (VLDL).

#### D7. Sekresyon (albumin)
- Konstitütif yol: proalbumin → ER (folding) → Golgi (6-aa pro-peptid kesimi) →
  veziküllerle kana. Karaciğerde **depolanmaz**, hemen salgılanır.
- **Ölçülmüş hızlar** (pulse-chase, izole hepatosit): ER→Golgi t½ = **14-137 dk**
  (proteine göre seçici: albumin, transferrin, prealbumin, RBP farklı hızlarda),
  Golgi→ortam t½ ≈ **15 dk**, ortalama transit ≈ **30 dk**. → trafficking
  modülümüz için doğrudan grounded zaman sabitleri.
Kaynak: Lodish & Kong; *Am J Physiol Cell Physiol* (constitutive albumin secretion).

#### D8. DNA hasarı / tamiri
- DSB tamiri: **NHEJ** (D-NHEJ/B-NHEJ) ve **HR**; **p53/p21** sinyal ağı kader
  kararını verir (tamir → sağ kalım / senesans / apoptoz).
- Yöntem (Karr-vari hibrit): **intranükleer reaksiyonlar stokastik**, sitoplazmik
  reaksiyonlar deterministik. → bizim hibrit motorumuza birebir uyar.
- Bizim apoptoz/ölüm modülümüz (M045) p53/genotoksik girdiyle bu ağın çıktısını
  alabilir.
Kaynak: *PLoS Comput Biol* (NHEJ + p53/p21 senesans entegre stokastik model);
DSB-repair-throughout-cell-cycle modelleri.

### E. Uzamsal — RDME ve ana motora bağlama

Alanın altın standardı, bizim tam olarak izlememiz gereken şablon:

- **4D Whole-Cell Model (JCVI-syn3A)** (*Cell* 2026). Üç yöntemi tek bir hücre-
  döngüsü simülasyonunda birleştirir: **RDME** (Lattice Microbes) ile uzamsal
  stokastik gen ifadesi/difüzyon; **ODE** ile metabolizma; **Brownian Dynamics**
  (LAMMPS) ile kromozom polimer dinamiği. 10 nm kübik latis. **105 dk hücre
  döngüsünü ölçümle birebir** öngördü. → "metabolizma sürekli + gen ifadesi uzamsal
  stokastik" tam bizim seçtiğimiz hibrit.
- **RDME** = kimyasal master denkleminin uzamsal genellemesi; 3-B uzayı kübik
  latise böler, her voxelde reaksiyon + komşu voxellere difüzyon.
- **Lattice Microbes** (Roberts/Luthey-Schulten): GPU-hızlandırmalı RDME; iyi-
  karışmış için exact'tan 2 mertebe hızlı.
- **Smoldyn** (parçacık-temelli), **Virtual Cell (VCell)** (uzamsal PDE/stokastik,
  hazır platform), **MesoRD**.

**Plan (kademeli):**
1. Mevcut 1-B `spatial.py`'yi gerçek reaksiyon ağıyla birleştir: her voxelde
   ağ propensity'leri + türlere özgü difüzyon (D'ler literatürden: ATP ~150,
   küçük moleküller ~100-500 µm²/s).
2. 1-B → 3-B latis (voxel ızgarası), reflektif/akı sınırları.
3. Düşük-kopya türler için voxel-içi SSA (RDME ruhu), yüksek-kopya için voxel-içi
   CLE — bizim hibrit ayrımımızın uzamsal versiyonu.
4. Hepatosit geometrisi: sinüzoidal yüz (giriş) ↔ kanaliküler yüz (çıkış)
   gradyanları; mitokondri-yakını ATP mikrodomainleri.

---

## Uygulama sırası (öneri)

1. **B + C altyapısı**: kinetik-veri yükleyici (BRENDA/SABIO-RK formatı) + HMDB
   konsantrasyon hedef yükleyici. (Her şeyin grounded olmasının ön şartı.)
2. **D1 metabolizma tamamlama** (PPP, TCA/OXPHOS, glukoneogenez, lipid çekirdeği),
   her enzim grounded, her yeni türe validasyon hedefi.
3. **D3 sinyalleşme** (insülin/glukagon/AMPK) → metabolizmayı düzenlesin.
4. **D4 transport** (gerçek transporterlar) → polarite gerçek olsun.
5. **D5 Ca/elektrofizyoloji**, **D6 lipid**, **D7 sekresyon**, **D8 DNA tamiri**.
6. **E uzamsal** çekirdeği ana motora bağla; sonra 3-B RDME.

Her adım: **önce kaynaktan parametre → kodla → korunum/birim testi → validasyon
hedefi → ancak sonra görsel.** Görsel asla doğruluğu bükmeyecek.

---

## Sources

- iHepatocytes2322: Mardinoglu et al., Nat Commun 2014 — https://www.nature.com/articles/ncomms4083 ; model https://www.omicsdi.org/dataset/biomodels/MODEL1402200003
- HEPATOKIN1: Berndt et al., Nat Commun 2018 — https://www.nature.com/articles/s41467-018-04720-9
- Hepatic glucose homeostasis kinetic model: König et al., PLoS Comput Biol 2012 — https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1002577
- Human-GEM — https://github.com/SysBioChalmers/Human-GEM ; redHUMAN — https://www.nature.com/articles/s41467-020-16549-2
- BRENDA / SABIO-RK overview — https://pubmed.ncbi.nlm.nih.gov/22102587/ ; https://www.researchgate.net/publication/320806656_SABIO-RK_An_updated_resource_for_manually_curated_biochemical_reaction_kinetics
- HMDB 5.0: Wishart et al., NAR 2022 — https://academic.oup.com/nar/article/50/D1/D622/6431815
- Insulin–glucagon signalling (bistability) — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6814820/ ; AMPK/CRTC2 — https://www.jci.org/articles/view/188363
- Hepatocyte transporters / bile formation — https://journals.physiology.org/doi/full/10.1152/physiologyonline.2000.15.2.89 ; DILI transporters — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9866820/
- Hepatocyte Ca²⁺ / IP3R oscillations — https://link.springer.com/article/10.1007/s00249-013-0908-y ; IP3R kinetics (stochastic) — https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3629942/
- Lipid metabolism / NAFLD — https://pmc.ncbi.nlm.nih.gov/articles/PMC6105174/ ; VLDL — https://www.ahajournals.org/doi/10.1161/CIRCRESAHA.123.323284
- Albumin secretion rates (ER→Golgi t½ 14-137 min) — https://pubmed.ncbi.nlm.nih.gov/6538481/ ; constitutive secretion — https://journals.physiology.org/doi/full/10.1152/ajpcell.00019.2005
- DNA DSB repair + p53 stochastic model — https://journals.plos.org/ploscompbiol/article?id=10.1371/journal.pcbi.1004246
- 4D Whole-Cell Model (syn3A, RDME+ODE+BD) — https://www.cell.com/cell/fulltext/S0092-8674(26)00174-1 ; Lattice Microbes (RDME) — https://pmc.ncbi.nlm.nih.gov/articles/PMC3762454/ ; living minimal cell — https://www.cell.com/cell/fulltext/S0092-8674(21)01488-4
