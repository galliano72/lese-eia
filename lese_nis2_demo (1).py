"""
LESE-EIA — Demo NIS2 Structural Coherence Analysis v2
Scenario realistico: 500 asset, inventario NIS2
Galliano Brigo, Milano — 10 Giugno 2026
"""

import numpy as np
import random

W_STAR = np.exp(-1)   # 0.36788
W_HALF = W_STAR / 2   # 0.18394
kappa  = 1.5

random.seed(42)
np.random.seed(42)

SERVIZI   = ['Email','ERP','VPN','Firewall','SIEM',
             'Backup','DNS','AD','CRM','FileServer']
ASSET     = ['Server','Switch','Router','Workstation',
             'Database','Storage','Cloud','IoT','Printer']
FORNITORI = ['Microsoft','Cisco','AWS','IBM',
             'Oracle','VMware','PaloAlto','Fortinet']
OWNER     = ['IT','Finance','HR','Legal',
             'Operations','Security','Management']

# Genera nodi
nodi = []
for i in range(200):
    nodi.append({'id':i,'tipo':'asset',
        'nome':f"{random.choice(ASSET)}_{i:03d}",
        'owner':random.choice(OWNER),
        'criticita':random.choice(['alta','media','bassa'])})
for i in range(200,350):
    nodi.append({'id':i,'tipo':'servizio',
        'nome':f"{random.choice(SERVIZI)}_{i:03d}",
        'owner':random.choice(OWNER),
        'criticita':random.choice(['alta','media','bassa'])})
for i in range(350,500):
    nodi.append({'id':i,'tipo':'fornitore',
        'nome':f"{random.choice(FORNITORI)}_{i:03d}",
        'owner':random.choice(OWNER),
        'criticita':random.choice(['alta','media','bassa'])})

# Genera archi con W realistici
# W base = 0.65 (sistema sano), degradi specifici
archi = []
for _ in range(1997):
    src = random.randint(0,499)
    dst = random.randint(0,499)
    if src == dst: continue
    ns = nodi[src]; nd = nodi[dst]

    w = 0.65 + random.uniform(-0.1, 0.25)

    # Degrado per owner diversi
    if ns['owner'] != nd['owner']:
        w -= random.uniform(0, 0.12)

    # Degrado per criticità non allineata
    if ns['criticita'] != nd['criticita']:
        w -= random.uniform(0, 0.08)

    # ANOMALIA 1: fornitore → asset critico senza owner IT
    if (ns['tipo']=='fornitore' and
        nd['criticita']=='alta' and
        nd['owner']!='IT'):
        w -= random.uniform(0.20, 0.35)

    # ANOMALIA 2: servizi critici non documentati (10%)
    if (ns['tipo']=='servizio' and
        ns['criticita']=='alta' and
        random.random() < 0.10):
        w -= random.uniform(0.25, 0.40)

    # ANOMALIA 3: asset critici con owner non tecnico
    if (ns['tipo']=='asset' and
        ns['criticita']=='alta' and
        ns['owner'] in ['HR','Legal','Finance'] and
        random.random() < 0.15):
        w -= random.uniform(0.15, 0.30)

    w = max(0.05, min(1.0, w))
    archi.append({'src':src,'dst':dst,'w':w,
                  'tipo':f"{ns['tipo']}-{nd['tipo']}"})

# Calcola W per nodo = media pesata archi (non min)
# più realistico: media degli archi pesata per criticità
w_nodi = {}
for n in nodi:
    archi_n = [a['w'] for a in archi
               if a['src']==n['id'] or a['dst']==n['id']]
    if archi_n:
        # Usa percentile 20 — rileva il lato debole
        w_nodi[n['id']] = np.percentile(archi_n, 20)
    else:
        w_nodi[n['id']] = 0.0

stabili   = [(i,w) for i,w in w_nodi.items() if w >= W_STAR]
degradati = [(i,w) for i,w in w_nodi.items() if W_HALF<=w<W_STAR]
collasso  = [(i,w) for i,w in w_nodi.items() if w < W_HALF]
isolati   = [(i,w) for i,w in w_nodi.items() if w == 0.0]
w_globale = np.mean(list(w_nodi.values()))

print("=" * 65)
print("LESE-EIA — NIS2 Structural Coherence Analysis")
print("Scenario: Inventario aziendale 500 nodi, 1997 relazioni")
print(f"W* = {W_STAR:.5f} (soglia coerenza strutturale)")
print("=" * 65)

print(f"\nRISULTATI GLOBALI:")
print(f"  W_medio globale:  {w_globale:.4f}  "
      f"{'✅ STABILE' if w_globale>=W_STAR else '⚠️  DEGRADATO'}")
print(f"  Nodi STABILI:     {len(stabili):>4} ({len(stabili)/5:.1f}%)")
print(f"  Nodi DEGRADATI:   {len(degradati):>4} ({len(degradati)/5:.1f}%)")
print(f"  Nodi COLLASSO:    {len(collasso):>4} ({len(collasso)/5:.1f}%)")
print(f"  Nodi ISOLATI:     {len(isolati):>4} ({len(isolati)/5:.1f}%)")

print(f"\n{'='*65}")
print("TOP 10 ANOMALIE STRUTTURALI")
print(f"{'='*65}")
print(f"{'Nodo':<28} {'Tipo':<10} {'Owner':<12} {'Crit':<7} {'W':>7}")
print("-"*66)
critici = sorted([(i,w) for i,w in w_nodi.items()
                  if w < W_STAR], key=lambda x:x[1])
for nid,w in critici[:10]:
    n = nodi[nid]
    flag = " ⚠️" if w < W_HALF else ""
    print(f"{n['nome']:<28} {n['tipo']:<10} {n['owner']:<12} "
          f"{n['criticita']:<7} {w:>7.4f}{flag}")

print(f"\n{'='*65}")
print("COERENZA PER OWNER")
print(f"{'='*65}")
print(f"{'Owner':<14} {'Nodi':>5} {'Stabili%':>9} "
      f"{'Critici':>8} {'W_medio':>8}")
print("-"*48)
for owner in OWNER:
    nids = [n['id'] for n in nodi if n['owner']==owner]
    if not nids: continue
    ws = [w_nodi[i] for i in nids]
    pct = sum(1 for w in ws if w>=W_STAR)/len(ws)*100
    crit = sum(1 for w in ws if w<W_STAR)
    flag = " ⚠️" if pct < 40 else ""
    print(f"{owner:<14} {len(nids):>5} {pct:>8.1f}% "
          f"{crit:>8} {np.mean(ws):>8.4f}{flag}")

# Anomalie specifiche NIS2
a1 = [(nodi[a['src']]['nome'], nodi[a['dst']]['nome'],
       nodi[a['dst']]['owner'], a['w'])
      for a in archi
      if nodi[a['src']]['tipo']=='fornitore' and
         nodi[a['dst']]['criticita']=='alta' and
         nodi[a['dst']]['owner']!='IT' and
         a['w'] < W_STAR]

sc = [(nodi[i]['nome'],w) for i,w in w_nodi.items()
      if nodi[i]['tipo']=='servizio' and
         nodi[i]['criticita']=='alta' and w < W_STAR]

print(f"\n{'='*65}")
print("ANOMALIE SPECIFICHE NIS2")
print(f"{'='*65}")
print(f"\n1. Fornitori → asset critici non-IT sotto W*:")
print(f"   {len(a1)} relazioni anomale")
for f,a,o,w in sorted(a1,key=lambda x:x[3])[:5]:
    print(f"   {f} → {a} (owner:{o}) W={w:.4f}")

print(f"\n2. Servizi critici strutturalmente degradati:")
print(f"   {len(sc)} servizi")
for nome,w in sorted(sc,key=lambda x:x[1])[:5]:
    print(f"   {nome}: W={w:.4f}")

print(f"\n{'='*65}")
print("SOMMARIO ESECUTIVO PER CYTRIX / MARCO ZONTA")
print(f"{'='*65}")
print(f"""
Inventario: {len(nodi)} nodi | {len(archi)} relazioni documentate

W_medio globale: {w_globale:.4f}
  {'✅ Sistema strutturalmente stabile' if w_globale>=W_STAR 
    else '⚠️  Sistema strutturalmente degradato'}

Nodi formalmente corretti ma strutturalmente anomali:
  → {len(critici)} nodi sotto soglia W* ({len(critici)/5:.1f}%)
  → {len(a1)} relazioni fornitore-asset anomale
  → {len(sc)} servizi critici degradati

COSA LESE VEDE CHE UN WORKFLOW NON VEDE:
  Un asset catalogato come NIS2-compliant può essere
  strutturalmente disconnesso dal sistema reale.
  LESE misura W senza pattern storici né calibrazione.
  Rileva la degradazione prima che emerga l'incidente.

DOMANDA CHIAVE PER CYTRIX:
  Avete clienti con inventari formalmente corretti
  che hanno poi subito incidenti su asset "documentati"?
  Quella è la firma dell'incoerenza strutturale.
  LESE la avrebbe rilevata prima.
""")
