"""
OP-COSMO1 — Confronto EGESB-G₂ con dataset SPARC
Rotmod_LTG: 180 galassie late-type con curve di rotazione

Formula LESE (Assioma B12):
  a₀_LESE = κ × c × H₀ × W* / √12
  v⁴_pred = v⁴_bar + v²_bar × a₀ × r  [forma RAR]

Autore: Galliano Brigo, Milano — 10 Giugno 2026
"""

import numpy as np
import os
import glob
from scipy.stats import pearsonr

# ============================================================
# COSTANTI EGESB-G₂
# ============================================================
kappa  = 1.5                          # κ = 3/2 (da G₂)
W_star = np.exp(-1)                   # W* = e⁻¹
W0     = np.exp(-2/3)                 # W₀ = e^(-2/3) cosmologico
c      = 3e8                          # m/s
H0_km  = 69.7                         # km/s/Mpc (predetto EGESB-G₂)
H0     = H0_km * 1e3 / 3.0857e22     # s⁻¹
G      = 6.674e-11                    # m³/(kg s²)
M_sun  = 1.989e30                     # kg
kpc    = 3.0857e19                    # m
sqrt12 = np.sqrt(12)

# Accelerazione fondamentale LESE (Assioma B12)
a0_LESE = kappa * c * H0 * W_star / sqrt12
a0_MOND = 1.2e-10  # m/s² (valore empirico MOND)

print("=" * 60)
print("EGESB-G₂ — OP-COSMO1 — Analisi SPARC")
print("=" * 60)
print(f"\nCostanti EGESB-G₂:")
print(f"  κ    = {kappa}")
print(f"  W*   = {W_star:.5f} = e⁻¹")
print(f"  W₀   = {W0:.5f} = e^(-2/3)")
print(f"  H₀   = {H0_km} km/s/Mpc (predetto)")
print(f"  √12  = {sqrt12:.5f} (Assioma B12)")
print(f"\nAccelerazione fondamentale:")
print(f"  a₀_LESE = {a0_LESE:.4e} m/s²")
print(f"  a₀_MOND = {a0_MOND:.4e} m/s²")
print(f"  Rapporto a₀_LESE/a₀_MOND = {a0_LESE/a0_MOND:.4f}")
print(f"  Errore: {abs(a0_LESE-a0_MOND)/a0_MOND*100:.2f}%")

# ============================================================
# FORMULA RAR LESE
# ============================================================
def v_bary(vgas, vdisk, vbul):
    """Velocità barionica totale (quadrature)"""
    return np.sqrt(vgas**2 + vdisk**2 + vbul**2)

def v_LESE_RAR(v_bar_ms, a0=a0_LESE):
    """
    Radial Acceleration Relation LESE
    g_tot = g_bar / (1 - exp(-sqrt(g_bar/a₀)))
    v_pred = sqrt(g_tot × r) — ma usiamo direttamente:
    v⁴_pred = v⁴_bar + v²_bar × a₀_LESE × r
    
    In forma RAR (senza r esplicito):
    g_tot = g_bar + sqrt(g_bar × a₀)
    v_pred = sqrt(g_tot × r) = sqrt((g_bar + sqrt(g_bar×a₀)) × r)
    """
    # Approssimazione MOND-like:
    # v²_pred = v²_bar + sqrt(v²_bar × a₀ × r)
    # Usiamo la forma diretta con accelerazioni
    return v_bar_ms  # placeholder — vedi sotto

def g_total_LESE(g_bar, a0=a0_LESE):
    """
    Formula RAR LESE:
    g_tot = g_bar × [1 + sqrt(a₀/g_bar)]
    Equivalente a: g_tot = g_bar + sqrt(g_bar × a₀)
    """
    return g_bar + np.sqrt(g_bar * a0)

def v_pred_LESE(v_bar_kms, r_kpc, a0=a0_LESE):
    """
    Velocità predetta LESE in km/s
    v_bar in km/s, r in kpc
    """
    v_bar = v_bar_kms * 1e3      # m/s
    r     = r_kpc * kpc          # m
    
    # Accelerazione barionica
    g_bar = v_bar**2 / r  if r > 0 else 0
    if g_bar <= 0:
        return 0.0
    
    # Correzione LESE
    g_tot = g_total_LESE(g_bar, a0)
    
    # Velocità predetta
    v_pred = np.sqrt(g_tot * r)
    return v_pred / 1e3  # km/s

# ============================================================
# ANALISI DATASET SPARC
# ============================================================
data_dir = '/home/claude/Rotmod_LTG/'
files = sorted(glob.glob(data_dir + '*_rotmod.dat'))

print(f"\n{'='*60}")
print(f"Analisi {len(files)} galassie SPARC")
print(f"{'='*60}\n")

results = []
all_vobs = []
all_vpred = []
all_vbar = []
chi2_list = []
n_points_total = 0

for fpath in files:
    gname = os.path.basename(fpath).replace('_rotmod.dat', '')
    
    try:
        # Leggi dati
        data = []
        with open(fpath) as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                vals = line.split()
                if len(vals) >= 6:
                    data.append([float(v) for v in vals[:6]])
        
        if len(data) < 3:
            continue
            
        data = np.array(data)
        r_kpc   = data[:, 0]
        v_obs   = data[:, 1]
        err_v   = data[:, 2]
        v_gas   = data[:, 3]
        v_disk  = data[:, 4]
        v_bul   = data[:, 5]
        
        # Velocità barionica
        v_bar = v_bary(v_gas, v_disk, v_bul)
        
        # Velocità predetta LESE
        v_pred = np.array([
            v_pred_LESE(v_bar[i], r_kpc[i])
            for i in range(len(r_kpc))
        ])
        
        # Filtra punti validi
        mask = (v_obs > 0) & (err_v > 0) & (v_bar > 0) & (v_pred > 0) & (r_kpc > 0)
        if mask.sum() < 3:
            continue
        
        vo = v_obs[mask]
        vp = v_pred[mask]
        vb = v_bar[mask]
        ev = err_v[mask]
        
        # Chi² ridotto
        chi2 = np.sum(((vo - vp) / ev)**2) / len(vo)
        
        # Residuo medio
        residuo = np.mean((vp - vo) / vo) * 100
        
        results.append({
            'name': gname,
            'n': len(vo),
            'chi2': chi2,
            'residuo_pct': residuo,
            'v_max_obs': vo.max(),
            'v_max_pred': vp.max(),
        })
        
        all_vobs.extend(vo.tolist())
        all_vpred.extend(vp.tolist())
        all_vbar.extend(vb.tolist())
        chi2_list.append(chi2)
        n_points_total += len(vo)
        
    except Exception as e:
        pass

# ============================================================
# STATISTICHE GLOBALI
# ============================================================
all_vobs  = np.array(all_vobs)
all_vpred = np.array(all_vpred)
all_vbar  = np.array(all_vbar)

print(f"Galassie analizzate: {len(results)}")
print(f"Punti totali:        {n_points_total}")

# Correlazione globale
r_corr, p_val = pearsonr(all_vobs, all_vpred)
print(f"\nCorrelazione v_obs vs v_LESE: r = {r_corr:.4f} (p = {p_val:.2e})")

# Residuo globale
residui = (all_vpred - all_vobs) / all_vobs * 100
print(f"Residuo medio:       {np.mean(residui):.2f}%")
print(f"Residuo mediano:     {np.median(residui):.2f}%")
print(f"Scatter (σ):         {np.std(residui):.2f}%")

# Chi² mediano
chi2_arr = np.array(chi2_list)
print(f"\nχ² ridotto mediano:  {np.median(chi2_arr):.3f}")
print(f"χ² ridotto medio:    {np.mean(chi2_arr):.3f}")
print(f"Galassie χ² < 3:     {(chi2_arr < 3).sum()} ({(chi2_arr<3).mean()*100:.1f}%)")
print(f"Galassie χ² < 5:     {(chi2_arr < 5).sum()} ({(chi2_arr<5).mean()*100:.1f}%)")

# ============================================================
# TOP 10 MIGLIORI FIT
# ============================================================
print(f"\n{'='*60}")
print("Top 10 galassie — miglior fit LESE:")
print(f"{'='*60}")
results_sorted = sorted(results, key=lambda x: x['chi2'])
print(f"{'Galassia':<20} {'N':>4} {'χ²':>7} {'Residuo%':>10} {'Vmax_obs':>10} {'Vmax_pred':>10}")
print("-" * 65)
for r in results_sorted[:10]:
    print(f"{r['name']:<20} {r['n']:>4} {r['chi2']:>7.3f} "
          f"{r['residuo_pct']:>9.1f}% {r['v_max_obs']:>9.1f} {r['v_max_pred']:>9.1f}")

# ============================================================
# STIMA FATTORE OTTIMALE a₀
# ============================================================
print(f"\n{'='*60}")
print("Ottimizzazione a₀:")
print(f"{'='*60}")

# Trova a₀ che minimizza il residuo quadratico medio
from scipy.optimize import minimize_scalar

def rms_residuo(log_a0_factor):
    a0_test = a0_LESE * 10**log_a0_factor
    v_pred_test = []
    for i, fpath in enumerate(files):
        try:
            data = []
            with open(fpath) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    vals = line.split()
                    if len(vals) >= 6:
                        data.append([float(v) for v in vals[:6]])
            if len(data) < 3:
                continue
            data = np.array(data)
            r_kpc = data[:, 0]
            v_obs_g = data[:, 1]
            v_gas = data[:, 3]
            v_disk = data[:, 4]
            v_bul = data[:, 5]
            v_bar_g = v_bary(v_gas, v_disk, v_bul)
            mask = (v_obs_g > 0) & (v_bar_g > 0) & (r_kpc > 0)
            if mask.sum() < 3:
                continue
            vp = np.array([v_pred_LESE(v_bar_g[j], r_kpc[j], a0_test)
                          for j in range(len(r_kpc)) if mask[j]])
            vo = v_obs_g[mask]
            v_pred_test.extend(((vp - vo)/vo).tolist())
        except:
            pass
    if not v_pred_test:
        return 1e10
    return np.sqrt(np.mean(np.array(v_pred_test)**2))

result_opt = minimize_scalar(rms_residuo, bounds=(-0.5, 0.5), method='bounded')
a0_opt = a0_LESE * 10**result_opt.x
factor_opt = 10**result_opt.x

print(f"a₀_LESE (B12):    {a0_LESE:.4e} m/s²")
print(f"a₀_ottimale:      {a0_opt:.4e} m/s²")
print(f"a₀_MOND:          {a0_MOND:.4e} m/s²")
print(f"Fattore correz.:  {factor_opt:.4f}")
print(f"Errore vs MOND:   {abs(a0_opt-a0_MOND)/a0_MOND*100:.2f}%")
print(f"Errore LESE B12 vs MOND: {abs(a0_LESE-a0_MOND)/a0_MOND*100:.2f}%")

# ============================================================
# SOMMARIO FINALE
# ============================================================
print(f"\n{'='*60}")
print("SOMMARIO OP-COSMO1")
print(f"{'='*60}")
print(f"Formula: a₀ = κcH₀W*/√12")
print(f"         = {kappa} × {c:.0e} × {H0:.3e} × {W_star:.5f} / {sqrt12:.4f}")
print(f"         = {a0_LESE:.4e} m/s²")
print(f"")
print(f"Correlazione v_obs/v_LESE: {r_corr:.4f}")
print(f"Residuo medio:             {np.mean(residui):.1f}%")
print(f"Scatter:                   {np.std(residui):.1f}%")
print(f"χ² < 3 (buon fit):        {(chi2_arr<3).mean()*100:.0f}% delle galassie")
print(f"")
print(f"Confronto a₀:")
print(f"  LESE (B12):   {a0_LESE:.4e} (errore {abs(a0_LESE-a0_MOND)/a0_MOND*100:.1f}% vs MOND)")
print(f"  Ottimale:     {a0_opt:.4e} (errore {abs(a0_opt-a0_MOND)/a0_MOND*100:.1f}% vs MOND)")
print(f"  MOND:         {a0_MOND:.4e}")
print(f"")
print(f"{'='*60}")
print(f"Previsione EGESB-G₂: a₀ = κcH₀W*/√12 — ZERO parametri liberi")
print(f"{'='*60}")
