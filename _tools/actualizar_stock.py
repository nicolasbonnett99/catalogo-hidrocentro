#!/usr/bin/env python3
"""Actualiza el stock de precios.hidrocentrolima.com desde el inventario (CSV exportado de Google Sheets).
Uso: python3 _tools/actualizar_stock.py ruta/inventario.csv [--aplicar]
Sin --aplicar solo muestra los cambios. Con --aplicar reescribe index.html.
Reglas: columna TOTAL (índice 7) > 0 = En stock (1); 0 = Agotado (0).
Productos en 'Consultar' (2) no se tocan. DUDOSO se fuerza a Consultar.
Se aborta si hay más de 40 cambios o si se pierden productos (señal de CSV malo)."""
import csv, json, re, sys
HTML = __file__.rsplit('/_tools/', 1)[0] + '/index.html'
ALIAS={'XKP256':'WL-KP256','XKP356':'WL-KP356','XKP556':'WL-KP556','XKP756':'WL-KP756','XKP1106':'WL-KP1106','XKP1606':'WL-KP1606','XKP2206':'WL-KP2206',
'P-DG14':'P-DG350','P-DG16':'P-DG400','P-DG18':'P-DG450','P-DG21':'P-DG500','P-DG25':'P-DG650','P-DG28':'P-DG700',
'NBT16':'NBT400','NBT18':'NBT450','NBT20':'NBT500','NBT24':'NBT600','NBT30':'NBT750','NBT32':'NBT800','NBS36':'NBS900','NBS48':'NBS1200',
'CL200':'A6006BU','CL400':'A6007BU','CL600':'CL500','CS10':'SC10','CS20':'SC20','FL-1096':'SV-1096','SP2830':'SP1030','HT-1019':'SP-1019','SP-002':'SP-1022',
'NPL-11-25':'PL-S110-25','NPC-200':'NPC-400','A08S':'S08S','MB215':'MBS-215','MB315':'MBS-315','MB415':'MBS-415','ZN-PD-017':'ZN-PD-014'}
DUDOSO={'98004864','A08S'}
MAX_CAMBIOS=40
norm=lambda s:re.sub(r'[^A-Z0-9]','',s.upper())

def main():
    if len(sys.argv)<2: sys.exit(__doc__)
    aplicar='--aplicar' in sys.argv
    html=open(HTML,encoding='utf-8').read()
    m=re.search(r'const DATA=(\{.*?\});\n',html,re.S)
    if not m: sys.exit('ERROR: no encontré const DATA en index.html')
    D=json.loads(m.group(1)); P=D['P']; n0=len(P)
    inv=list(csv.reader(open(sys.argv[1],encoding='utf-8')))[1:]
    idx={}
    for r in inv:
        if len(r)<9: continue
        try: tot=float(r[7].strip().replace(',','') or 0)
        except ValueError: continue
        e=(tot,r[0].strip(),r[2][:70])
        if norm(r[0]): idx.setdefault(norm(r[0]),e)
        for mm in re.findall(r'MODELOS?\s+([A-Z0-9][A-Z0-9\-\./]+)',r[2].upper()): idx.setdefault(norm(mm),e)
    if len(idx)<200: sys.exit(f'ERROR: el inventario solo tiene {len(idx)} códigos; parece incompleto. No se cambia nada.')
    cambios=[];encontrados=0
    for p in P:
        keys=[norm(p['mod'])]
        if p['mod'] in ALIAS: keys.insert(0,norm(ALIAS[p['mod']]))
        e=next((idx[k] for k in keys if k in idx),None)
        if not e: continue
        encontrados+=1
        if p['mod'] in DUDOSO:
            if p['st']!=2: cambios.append((p,2,e)); 
            continue
        if p['st']==2: continue
        nuevo=1 if e[0]>0 else 0
        if nuevo!=p['st']: cambios.append((p,nuevo,e))
    et={0:'Agotado',1:'En stock',2:'Consultar'}
    print(f'Productos: {n0} · encontrados en inventario: {encontrados} · cambios: {len(cambios)}')
    for p,nv,e in cambios:
        print(f"  {p['mod']:<12} {p['nom'][:45]:<45} {et[p['st']]:>9} → {et[nv]:<9} (inv {e[1]}: {e[0]:g})")
    if encontrados<150: sys.exit('ERROR: muy pocos productos encontrados en el inventario. No se publica.')
    if len(cambios)>MAX_CAMBIOS: sys.exit(f'ERROR: {len(cambios)} cambios (> {MAX_CAMBIOS}). Revisión manual requerida. No se publica.')
    if not aplicar or not cambios: return
    for p,nv,e in cambios: p['st']=nv
    assert len(P)==n0
    nuevo=html[:m.start(1)]+json.dumps(D,ensure_ascii=False,separators=(',',':'))+html[m.end(1):]
    open(HTML,'w',encoding='utf-8').write(nuevo)
    print('index.html actualizado.')
main()
