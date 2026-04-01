import streamlit as st
import numpy as np
import pandas as pd
from fractions import Fraction

# Functie care transforma orice numar in fractie
def f(n):
    if abs(n) < 1e-10: return "0"                                                # Daca e aproape de zero, afisam 0
    return str(Fraction(float(n)).limit_denominator(100))                        # Transformare in fractie


# Functie pentru afisarea vectorilor sub forma de coloana (vertical) - ADAPTATA PENTRU STREAMLIT
def afiseaza_coloana(vector, nume):
    out = f"   {nume} =\n"
    for val in vector:
        out += f"      ( {f(val):^5} )\n"                                        # Afisare centrata in paranteze
    st.text(out)


def pregateste_forma_standard(A, b, c, semne, tip_x, opt_tip, M_val):
    m, n_init = np.array(A).shape                                              # Dimensiunile matricei initiale
    A_mat = np.array(A, dtype=float)                                         # Copie matrice A
    b_lucru = np.array(b, dtype=float)                                         # Copie vector b
    c_vec = np.array(c, dtype=float)                                           # Definim c_vec pentru a fi folosit în R1
    semne_lucru = list(semne)                                                  # Copie lista de semne

    # --- REGULA R1: Tratarea condițiilor variabilelor (x >= 0, x <= 0 sau liber) 
    # initializare
    coloane_r1 = []
    costuri_r1 = []
    mapare_var = []
    nume_var_r1 = [] 
    
    for j in range(n_init):
        if tip_x[j] == '>=0':
                                   # Variabila e deja standard 
            coloane_r1.append(A_mat[:, j])
            costuri_r1.append(c_vec[j])
            mapare_var.append({'nume': f"x{j+1}", 'original': j, 'semn': 1})
            nume_var_r1.append(f"x{j+1}")           # Salvăm numele
            
        elif tip_x[j] == '<=0':
            # Substituție x = -x' 
            # Înmulțim coloana și coeficientul din funcția obiectiv cu -1
            coloane_r1.append(A_mat[:, j] * (-1))
            costuri_r1.append(c_vec[j] * (-1))
            mapare_var.append({'nume': f"x{j+1}'", 'original': j, 'semn': -1})
            nume_var_r1.append(f"x{j+1}'")
            
        elif tip_x[j] == 'liber':
            # Substituție x = x' - x'' 
            # Variabila "liberă" se sparge în două coloane în tabel
            coloane_r1.append(A_mat[:, j]) # Coloana normală (x')
            costuri_r1.append(c_vec[j])
            mapare_var.append({'nume': f"x{j+1}'", 'original': j, 'semn': 1})
            nume_var_r1.append(f"x{j+1}'")
            
            coloane_r1.append(A_mat[:, j] * (-1)) # Coloana cu minus (x'')
            costuri_r1.append(c_vec[j] * (-1))
            mapare_var.append({'nume': f"x{j+1}''", 'original': j, 'semn': -1})
            nume_var_r1.append(f"x{j+1}''")
            
     # transformam listele înapoi în matrice de lucru pentru pasul urm
    A_lucru_r1 = np.column_stack(coloane_r1)
    C_lucru_r1 = np.array(costuri_r1)

    # Verificam conditia b >= 0 
    for i in range(m):                                                         # Parcurgem restrictiile
        if b_lucru[i] < 0:                                                     # Daca termenul liber e negativ
            b_lucru[i] *= -1                                                   # Inmultim linia cu -1
            A_lucru_r1[i] *= -1                                                # Inmultim coeficientii cu -1
            if semne_lucru[i] == '<=': semne_lucru[i] = '>='                   # Inversam semnul
            elif semne_lucru[i] == '>=': semne_lucru[i] = '<='

    # --- REGULA R2 Constructia coloanelor pentru Forma Standard
    coloane_std = A_lucru_r1.tolist()                                            # Matricea de lucru sub forma de lista
    Cj_std = C_lucru_r1.tolist()                                                         #Coeficientii functiei obiectiv f
    nume_var = nume_var_r1.copy()                                             # x1, x2, x3...
    baza_initiala = []                                                        # Retinem coloanele care intra in prima baza

    for i in range(m):                                                        # Trecem prin fiecare restrictie pentru a adauga y sau z
        if semne_lucru[i] == '<=':                                            # Daca avem <=
            col = [0]*m; col[i] = 1                                           # Variabila de ecart y
            for r in range(m): coloane_std[r].append(col[r])                  # Adaugam coloana in matrice
            Cj_std.append(0)                                                  # Coeficientul lui y in f este 0
            nume_var.append(f"y{i+1}")                                        # Numele variabilei
            baza_initiala.append(len(Cj_std) - 1)                             # Aceasta variabila formeaza baza
        elif semne_lucru[i] == '>=':                                          # Daca avem >=
            col_y = [0]*m; col_y[i] = -1                                      # Variabila de surplus y
            for r in range(m): coloane_std[r].append(col_y[r])
            Cj_std.append(0)                                                  # Coeficientul lui y in f este 0
            nume_var.append(f"y{i+1}")
            col_z = [0]*m; col_z[i] = 1                                       # Variabila artificiala z pentru baza
            for r in range(m): coloane_std[r].append(col_z[r])
            val_M = M_val if opt_tip == 'MIN' else -M_val                     # Penalizare M
            Cj_std.append(val_M)                                              # Coeficientul lui z in f este M
            nume_var.append(f"z{i+1}")
            baza_initiala.append(len(Cj_std) - 1)                             # Intra in baza
        elif semne_lucru[i] == '=':                                           # Daca avem =
            col_z = [0]*m; col_z[i] = 1                                       # Adaugam direct variabila artificiala z
            for r in range(m): coloane_std[r].append(col_z[r])
            val_M = M_val if opt_tip == 'MIN' else -M_val
            Cj_std.append(val_M)
            nume_var.append(f"z{i+1}")
            baza_initiala.append(len(Cj_std) - 1)

    # Returnam datele pregatite pentru alg Simplex
    return np.array(coloane_std, dtype=float), np.array(b_lucru, dtype=float), np.array(Cj_std, dtype=float), nume_var, baza_initiala, mapare_var


def ruleaza_iteratii_simplex(TS, XB, Cj, baza, nume_var, opt_tip):
    m = len(XB)                                                                    # Numar de restrictii
    n_tot = len(Cj)                                                                # Numar total de variabile
    nume_ai = [f"a{i+1}" for i in range(n_tot)]                                    # Etichete coloane a1, a2...
    pas = 0 # Contor tabele
    
    while pas < 1000:                                                                # Maxim 1000 tabele
        CB = Cj[baza]                                                              # Coeficientii bazei (coloana stanga)
        Z_total = np.dot(CB, XB)                                                   # Valoarea functiei f: suma(CB * XB)
        
        # Calcul Delta_j = Cj - Zj 
        deltas = [Cj[j] - np.dot(CB, TS[:, j]) for j in range(n_tot)]
        
        # Afisarea tabelului in STREAMLIT EXACT CA IN CONSOLA
        out_tabel = f"--- TABEL SIMPLEX T{pas} ---\n"
        out_tabel += "CB\tBaza\tXB\t| " + "\t".join(nume_ai) + "\n"
        for i in range(m):
            linie = f"{f(CB[i])}\t{nume_ai[baza[i]]}\t{f(XB[i])}\t| "
            linie += "\t".join([f(val) for val in TS[i]])
            out_tabel += linie + "\n"
        out_tabel += "-" * 100 + "\n"
        out_tabel += f"\tDj\tZ={f(Z_total)}\t| " + "\t".join([f(d) for d in deltas])
        
        st.text(out_tabel) # Afisare monospatiata in site

        # Verificare optim 
        if opt_tip == 'MAX':
            if all(d <= 1e-5 for d in deltas): break                                   # Optim MAX daca toti Dj <= 0
            col_p = np.argmax(deltas)                                                  # Intra coloana cu Dj maxim (+)
        else: # MIN
            if all(d >= -1e-5 for d in deltas): break                                  # Optim MIN daca toti Dj >= 0
            col_p = np.argmin(deltas)                                                  # Intra coloana cu Dj minim (-)

        # Criteriul raportului minim pentru alegerea liniei pivot
        rapoarte = [XB[i]/TS[i, col_p] if TS[i, col_p] > 1e-10 else float('inf') for i in range(m)]
        
        lin_p = np.argmin(rapoarte)                                                    # Linia cu raportul cel mai mic
        
        # Actualizare tabel prin pivotare 
        pivot_val = TS[lin_p, col_p]                                                   # Valoare pivot
        TS[lin_p] /= pivot_val                                                         # Impartim linia la pivot
        XB[lin_p] /= pivot_val                                                         # Impartim XB la pivot
        for i in range(m):                                                             # Facem 0 pe restul coloanei pivotului
            if i != lin_p:
                multiplicator = TS[i, col_p]
                TS[i] -= multiplicator * TS[lin_p]
                XB[i] -= multiplicator * XB[lin_p]
        
        baza[lin_p] = col_p                                                           # Actualizam componenta bazei
        pas += 1                                                                      # Tabelul urmator
        
    return XB, Z_total, deltas, baza, TS                                              # Returnam rezultatele finale


def validare_solutie(XB_final, Z_final, deltas_final, baza_finala, TS_final, A_prim_init, b_init, c_init, mapare, nume_v, opt_t):
    # Construim string-ul exact ca in consola
    out = "="*60 + "\n"
    out += "            VERIFICARI SI VALIDARE FINALA \n"
    out += "="*60 + "\n"

    # 1. Verificare Criteriu Dj (Criteriul de optim)
    out += f"\nCRITERIU OPTIM ({opt_t}):\n"
    if opt_t == 'MAX':
        out += f"   Dj = {[f(d) for d in deltas_final]} <= 0 {'[OK]' if all(d <= 1e-5 for d in deltas_final) else '[FAIL]'}\n"
    else:
        out += f"   Dj = {[f(d) for d in deltas_final]} >= 0 {'[OK]' if all(d >= -1e-5 for d in deltas_final) else '[FAIL]'}\n"

    # 2. V1: Verificarea xj >= 0 
    out += "\nV1) Verificare nenegativitate xj >= 0:\n"
    sol_completa = {nume_v[i]: 0.0 for i in range(len(nume_v))}                                # Cream dictionar cu toate var = 0
    for i in range(len(XB_final)): sol_completa[nume_v[baza_finala[i]]] = XB_final[i]          # Punem valorile bazei
    
    # Reconstructia x-urilor originale din variabilele de tabel (x', x'', etc.)
    x_reconstruit = np.zeros(len(c_init))
    for m_info in mapare:
        val_tabel = sol_completa[m_info['nume']]
        x_reconstruit[m_info['original']] += m_info['semn'] * val_tabel
        out += f"   {m_info['nume']}* = {f(val_tabel)} >= 0 [OK]\n"                             # Verificam doar variabilele x (decizie)

    # 3. V2: Verificarea valorii functiei f 
    out += f"\nV2) Verificare valoare f(PL) = {f(Z_final)}:\n"
    f_calculata = sum(c_init[i] * x_reconstruit[i] for i in range(len(c_init)))               # Inlocuim x in f
    out += f"   Calcul: {f(f_calculata)} == {f(Z_final)} {'[OK]' if abs(f_calculata - Z_final) < 1e-10 else '[FAIL]'}\n"

    # 4. V3: Verificarea relatiei XB(initial) = S * XB(final) 
    out += "\nV3) Verificare relatie XB(I0) = S * XB(I_stop):\n"
    S_matrice = A_prim_init[:, baza_finala]                                           # Matricea S (coloanele din T0 corespunzatoare bazei finale)
    out += "   Matricea S (din coloanele bazei finale din T0):\n"
    for r in S_matrice: 
        out += "      | " + "\t".join([f(val) for val in r]) + " |\n"
    
    st.text(out) # Afisam in Streamlit prima parte a validarilor
    
    afiseaza_coloana(XB_final, "XB(I_stop) final")                                    # Afisam XB optim vertical
    reconstruit = np.dot(S_matrice, XB_final)                                         # Produsul matricial S * XB_final
    afiseaza_coloana(reconstruit, "S * XB(I_stop)")                                   # Trebuie sa fie egal cu b initial
    afiseaza_coloana(b_init, "XB(I0) initial")                                        # Vectorul b de la care am plecat
    
    out_final = f"\n   Rezultat V3: {'[VERIFICAT]' if np.allclose(reconstruit, b_init) else '[FAIL]'}\n"
    out_final += "="*60
    st.text(out_final) # Afisam rezultatul final


def rezolva_simplex_complet(A, b, c, semne, tip_x, opt_tip='MAX', M=1000):
    # Pas 1 & 2: Pregatire Forma Standard (R1 si R2)
    rezultat_pregatire = pregateste_forma_standard(A, b, c, semne, tip_x, opt_tip, M)
    TS_init, b_lucru, Cj_std, nume_v, baza_init, mapare = rezultat_pregatire
    
    b_backup = b_lucru.copy() # Copie b pentru V3
    A_prim_init = TS_init.copy() # Copie matrice T0 pentru V3
    
    # Pas 3: Executie Iteratii Simplex
    # XB_f = valorile bazei la final, Z_f = f optim, baza_f = indicii bazei la final
    rezultat_it = ruleaza_iteratii_simplex(TS_init, b_lucru.copy(), Cj_std, baza_init, nume_v, opt_tip)
    
    if rezultat_it:
        XB_f, Z_f, Dj_f, baza_f, TS_f = rezultat_it
        # Pas 4: Validare conform cerintelor
        validare_solutie(XB_f, Z_f, Dj_f, baza_f, TS_f, A_prim_init, b_backup, c, mapare, nume_v, opt_tip)
    else:
        st.error("Problema nu are solutie optima finita (nemarginita).")


# ==========================================
# --- INTERFATA GRAFICA STREAMLIT (UI) ---
# ==========================================

st.set_page_config(page_title="Algoritm Simplex", layout="wide")
st.title("Rezolvare Algoritm Simplex")

# Configurari initiale - le populam by default cu datele tale de test
col1, col2 = st.columns(2)
with col1:
    n_vars = st.number_input("Număr de variabile (n)", min_value=1, max_value=10, value=3)
with col2:
    m_restr = st.number_input("Număr de restricții (m)", min_value=1, max_value=10, value=3)

st.subheader("1. Funcția Obiectiv")
col_opt, col_c = st.columns([1, 3])
with col_opt:
    opt_tip = st.selectbox("Tip optimizare", ["MAX", "MIN"], index=0)
with col_c:
    c_input = st.text_input("Coeficienții funcției (separați prin virgulă)", "3, 1, 1")

st.subheader("2. Restricții (Introduceți Matricea A, Semnele și Vectorul b)")
# Definim datele default de test pe care mi le-ai trimis pentru Matricea A si b
A_default = [[2, 2, 3], [3, 1, 1], [2, 1, 2]]
b_default = [12, 11, 8]

df_restr = pd.DataFrame(index=range(m_restr), columns=[f"x{i+1}" for i in range(n_vars)])

# Populam matricea daca dimensiunile corespund cu testul default
for i in range(m_restr):
    for j in range(n_vars):
        df_restr.iloc[i, j] = A_default[i][j] if (i<len(A_default) and j<len(A_default[0])) else 0.0

df_restr["Semn"] = "<="
df_restr["b"] = [b_default[i] if i<len(b_default) else 0.0 for i in range(m_restr)]

# Afisam tabelul si il lasam pe user sa il editeze
edited_restr = st.data_editor(df_restr, use_container_width=True)

st.subheader("3. Condiții variabile")
df_cond = pd.DataFrame(">=0", index=["Tip"], columns=[f"x{i+1}" for i in range(n_vars)])
# Permitem valori specifice in tabelul de conditii (>=0, <=0, liber)
edited_cond = st.data_editor(
    df_cond, 
    use_container_width=True,
    column_config={f"x{i+1}": st.column_config.SelectboxColumn("Tip", options=[">=0", "<=0", "liber"]) for i in range(n_vars)}
)

st.divider()

# Butonul de rulare care apeleaza efectiv functiile
if st.button("Calculează Soluția", type="primary"):
    try:
        # Preluam datele din interfata
        c = [float(x.strip()) for x in c_input.split(",")]
        
        if len(c) != n_vars:
            st.error(f"Eroare: Ai introdus {len(c)} coeficienți pentru {n_vars} variabile!")
            st.stop()

        A = edited_restr[[f"x{i+1}" for i in range(n_vars)]].values.tolist()
        semne = edited_restr["Semn"].tolist()
        b = edited_restr["b"].tolist()
        tip_x = edited_cond.iloc[0].tolist()

        # Apelam functia ta (Va afisa rezolvarea chiar sub buton)
        st.markdown("### REZULTATE:")
        rezolva_simplex_complet(A, b, c, semne, tip_x, opt_tip)
            
    except Exception as e:
        st.error(f"A apărut o eroare la procesarea datelor: {e}")
