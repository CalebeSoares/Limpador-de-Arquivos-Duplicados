import os
import hashlib
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from collections import defaultdict

# ============ PALETA ============
COR_FUNDO_ESCURO = "#02201D"
COR_VERDE_ESCURO = "#03665C"
COR_VERDE_VIVO   = "#03A688"
COR_VERDE_CLARO  = "#81E8D4"
COR_FUNDO        = "#E1F0ED"
COR_VERDE_MEDIO  = "#6FBF9F"
COR_CREME        = "#F6F0E0"
COR_BRANCO       = "#FFFFFF"
COR_TEXTO        = "#02201D"
COR_TEXTO_CINZA  = "#5A6B68"
COR_VERMELHO     = "#C0392B"

app = tk.Tk()
app.title("Limpador de Duplicados - Só apaga da PASTA A")
app.geometry("980x680")
app.minsize(850, 550)
app.configure(bg=COR_FUNDO)

pasta_a_var = tk.StringVar()
pasta_b_var = tk.StringVar()
duplicados = []
cancelar_evento = threading.Event()

def caminho_curto(caminho, limite=65):
    if len(caminho) <= limite:
        return caminho
    return "..." + caminho[-(limite-3):]

style = ttk.Style()
style.theme_use("clam")
style.configure("Barra.Horizontal.TProgressbar", thickness=18, troughcolor=COR_CREME, background=COR_VERDE_VIVO, borderwidth=0)
style.configure("Treeview", background=COR_BRANCO, fieldbackground=COR_BRANCO, foreground=COR_TEXTO, font=("Segoe UI", 9), rowheight=28, borderwidth=0)
style.configure("Treeview.Heading", background=COR_FUNDO_ESCURO, foreground="white", font=("Segoe UI", 9, "bold"), padding=8, borderwidth=0)
style.map("Treeview", background=[("selected", COR_VERDE_CLARO)], foreground=[("selected", COR_TEXTO)])
style.configure("Vertical.TScrollbar", background=COR_VERDE_MEDIO, troughcolor=COR_CREME, borderwidth=0, arrowcolor=COR_FUNDO_ESCURO)

header = tk.Frame(app, bg=COR_FUNDO_ESCURO, height=70)
header.pack(fill="x")
tk.Label(header, text="  LIMPADOR DE DUPLICADOS", bg=COR_FUNDO_ESCURO, fg="white", font=("Segoe UI", 16, "bold"), anchor="w").pack(side="left", padx=20, pady=15)
tk.Label(header, text="Só apaga da PASTA A  •  PASTA B é segura", bg=COR_FUNDO_ESCURO, fg=COR_VERDE_CLARO, font=("Segoe UI", 9), anchor="e").pack(side="right", padx=20)

def escolher_pasta_zenity(titulo):
    try:
        resultado = subprocess.run(["zenity", "--file-selection", "--directory", "--title", titulo], capture_output=True, text=True)
        if resultado.returncode == 0:
            pasta = resultado.stdout.strip()
            if pasta:
                return pasta
        return None
    except FileNotFoundError:
        messagebox.showwarning("Zenity não encontrado", "Instale o Zenity:\nsudo apt install zenity")
        return filedialog.askdirectory(title=titulo)

def escolher_pasta_a():
    pasta = escolher_pasta_zenity("Escolha a PASTA A - A QUE VAI SER LIMPA")
    if pasta:
        pasta_a_var.set(pasta)
        lbl_caminho_a.config(text=caminho_curto(pasta))

def escolher_pasta_b():
    pasta = escolher_pasta_zenity("Escolha a PASTA B - REFERÊNCIA SEGURA")
    if pasta:
        pasta_b_var.set(pasta)
        lbl_caminho_b.config(text=caminho_curto(pasta))

def listar_arquivos(pasta):
    lista = []
    for raiz, pastas, arquivos in os.walk(pasta):
        for nome in arquivos:
            lista.append(os.path.join(raiz, nome))
    return lista

def hash_arquivo(caminho, bloco=65536):
    h = hashlib.md5()
    try:
        with open(caminho, "rb") as f:
            while True:
                dados = f.read(bloco)
                if not dados:
                    break
                h.update(dados)
        return h.hexdigest()
    except:
        return None

def atualizar_progresso(atual, total, texto=""):
    if total > 0:
        pct = int((atual / total) * 100)
        progress["value"] = pct
        lbl_prog.config(text=f"{texto} - {pct}% ({atual} de {total} arquivos)")
    else:
        lbl_prog.config(text=texto)
    app.update_idletasks()

def processo_cancelado():
    btn_comparar.config(state="normal", text="COMPARAR AGORA")
    btn_cancelar.config(state="disabled")
    lbl_prog.config(text="Cancelado pelo usuário")
    lbl_status.config(text="Comparação cancelada. Escolha as pastas e compare de novo quando quiser.")
    progress["value"] = 0

def remover_pastas_vazias(pasta_base):
    pastas_apagadas = 0
    for raiz, pastas, arquivos in os.walk(pasta_base, topdown=False):
        if os.path.abspath(raiz) == os.path.abspath(pasta_base):
            continue
        try:
            if not os.listdir(raiz):
                os.rmdir(raiz)
                pastas_apagadas += 1
        except:
            pass
    return pastas_apagadas

# ======= CORREÇÃO: BOTÕES FIXOS EMBAIXO PRIMEIRO =======
# Tem que empacotar ele ANTES do frame_meio, senão o frame_meio engole ele
frame_acoes = tk.Frame(app, bg=COR_FUNDO_ESCURO, padx=15, pady=10)
frame_acoes.pack(fill="x", side="bottom")
btn_selecionar_tudo = tk.Button(frame_acoes, text="Selecionar Tudo", command=lambda: tree.selection_set(tree.get_children()), bg=COR_CREME, fg=COR_TEXTO, font=("Segoe UI", 10), relief="flat", padx=15, pady=8, cursor="hand2")
btn_selecionar_tudo.pack(side="left", padx=(0,8))
btn_apagar = tk.Button(frame_acoes, text="APAGAR SELECIONADOS (SÓ DA PASTA A)", command=lambda: apagar_selecionados(), bg=COR_VERMELHO, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2")
btn_apagar.pack(side="left", fill="x", expand=True)

# ======= ÁREA DO MEIO - AGORA VEM DEPOIS DOS BOTÕES =======
frame_meio = tk.Frame(app, bg=COR_FUNDO)
frame_meio.pack(fill="both", expand=True)

card_a = tk.Frame(frame_meio, bg=COR_BRANCO, highlightbackground=COR_VERDE_MEDIO, highlightthickness=1, padx=15, pady=12)
card_a.pack(fill="x", padx=15, pady=(15, 5))
tk.Label(card_a, text="PASTA A  —  A QUE VAI SER LIMPA", bg=COR_BRANCO, fg=COR_VERMELHO, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
tk.Label(card_a, text="De onde os arquivos duplicados serão apagados", bg=COR_BRANCO, fg=COR_TEXTO_CINZA, font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0,8))
btn_a = tk.Button(card_a, text="Escolher Pasta A", command=escolher_pasta_a, bg=COR_VERDE_ESCURO, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2", activebackground=COR_VERDE_VIVO, activeforeground="white")
btn_a.pack(fill="x")
lbl_caminho_a = tk.Label(card_a, text="Nenhuma pasta escolhida", bg=COR_BRANCO, fg=COR_TEXTO_CINZA, font=("Segoe UI", 9), anchor="w")
lbl_caminho_a.pack(fill="x", pady=(6,0))

card_b = tk.Frame(frame_meio, bg=COR_BRANCO, highlightbackground=COR_VERDE_MEDIO, highlightthickness=1, padx=15, pady=12)
card_b.pack(fill="x", padx=15, pady=5)
tk.Label(card_b, text="PASTA B  —  REFERÊNCIA SEGURA", bg=COR_BRANCO, fg=COR_VERDE_ESCURO, font=("Segoe UI", 10, "bold"), anchor="w").pack(fill="x")
tk.Label(card_b, text="Nunca apaga daqui. Só serve pra comparar", bg=COR_BRANCO, fg=COR_TEXTO_CINZA, font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0,8))
btn_b = tk.Button(card_b, text="Escolher Pasta B", command=escolher_pasta_b, bg=COR_VERDE_MEDIO, fg="white", font=("Segoe UI", 10, "bold"), relief="flat", padx=15, pady=8, cursor="hand2", activebackground=COR_VERDE_ESCURO, activeforeground="white")
btn_b.pack(fill="x")
lbl_caminho_b = tk.Label(card_b, text="Nenhuma pasta escolhida", bg=COR_BRANCO, fg=COR_TEXTO_CINZA, font=("Segoe UI", 9), anchor="w")
lbl_caminho_b.pack(fill="x", pady=(6,0))

frame_botoes = tk.Frame(frame_meio, bg=COR_FUNDO, padx=15)
frame_botoes.pack(fill="x", pady=12)
btn_comparar = tk.Button(frame_botoes, text="COMPARAR AGORA", command=lambda: comparar_thread(), bg=COR_VERDE_VIVO, fg="white", font=("Segoe UI", 12, "bold"), relief="flat", pady=10, cursor="hand2", activebackground=COR_VERDE_ESCURO, activeforeground="white")
btn_comparar.pack(side="left", fill="x", expand=True, padx=(0,6))
btn_cancelar = tk.Button(frame_botoes, text="CANCELAR", command=lambda: cancelar_evento.set(), bg=COR_FUNDO_ESCURO, fg="white", font=("Segoe UI", 12, "bold"), relief="flat", pady=10, state="disabled", cursor="hand2")
btn_cancelar.pack(side="left", fill="x", expand=True, padx=(6,0))

frame_prog = tk.Frame(frame_meio, bg=COR_FUNDO, padx=15)
frame_prog.pack(fill="x", pady=(0,5))
progress = ttk.Progressbar(frame_prog, orient="horizontal", length=100, mode="determinate", style="Barra.Horizontal.TProgressbar")
progress.pack(fill="x", ipady=4)
lbl_prog = tk.Label(frame_prog, text="Pronto para comparar", bg=COR_FUNDO, fg=COR_TEXTO_CINZA, font=("Segoe UI", 9))
lbl_prog.pack(anchor="w", pady=(4,0))
lbl_status = tk.Label(frame_meio, text="Escolha as 2 pastas e clique em COMPARAR", bg=COR_FUNDO, fg=COR_TEXTO, font=("Segoe UI", 10, "bold"), anchor="w", padx=15)
lbl_status.pack(fill="x", pady=(0,5))

# ======= TABELA COM SÓ BARRA VERTICAL - CORREÇÃO =======
frame_tabela = tk.Frame(frame_meio, bg=COR_FUNDO, padx=15)
frame_tabela.pack(fill="both", expand=True, pady=5)

colunas = ("origem", "nome", "tamanho", "original_em")
tree = ttk.Treeview(frame_tabela, columns=colunas, show="headings", height=11)
tree.heading("origem", text="De onde?")
tree.heading("nome", text="Nome do arquivo")
tree.heading("tamanho", text="Tamanho")
tree.heading("original_em", text="Já existe em (Pasta B - segura)")
tree.column("origem", width=90)
tree.column("nome", width=250)
tree.column("tamanho", width=100)
tree.column("original_em", width=440)

# SÓ vertical, sem horizontal
scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=tree.yview, style="Vertical.TScrollbar")
tree.configure(yscrollcommand=scroll_y.set)

tree.pack(side="left", fill="both", expand=True)
scroll_y.pack(side="right", fill="y")

def comparar_thread():
    pa = pasta_a_var.get()
    pb = pasta_b_var.get()
    if not pa or not pb:
        messagebox.showwarning("Ops", "Escolha a Pasta A e a Pasta B primeiro!")
        return
    if pa == pb:
        messagebox.showwarning("Ops", "A Pasta A e a Pasta B não podem ser a mesma!")
        return
    cancelar_evento.clear()
    btn_comparar.config(state="disabled", text="Comparando... aguarde")
    btn_cancelar.config(state="normal")
    lbl_status.config(text="Contando arquivos...")
    tree.delete(*tree.get_children())
    duplicados.clear()
    progress["value"] = 0
    lbl_prog.config(text="Contando arquivos...")
    def rodar():
        try:
            todos_arquivos = []
            for pasta in [pa, pb]:
                for arq in listar_arquivos(pasta):
                    if cancelar_evento.is_set():
                        app.after(0, lambda: processo_cancelado())
                        return
                    todos_arquivos.append(arq)
            total = len(todos_arquivos)
            app.after(0, lambda: lbl_status.config(text=f"Encontrado {total} arquivos, comparando..."))
            por_tamanho = defaultdict(list)
            for i, arq in enumerate(todos_arquivos):
                if cancelar_evento.is_set():
                    app.after(0, lambda: processo_cancelado())
                    return
                try:
                    tam = os.path.getsize(arq)
                    por_tamanho[tam].append(arq)
                except:
                    pass
                if i % 100 == 0:
                    app.after(0, lambda i=i: atualizar_progresso(i, total, "Lendo arquivos"))
            candidatos = [arq for lista in por_tamanho.values() if len(lista) >= 2 for arq in lista]
            total_candidatos = len(candidatos) if candidatos else 1
            por_hash = defaultdict(list)
            processados = 0
            for arq in candidatos:
                if cancelar_evento.is_set():
                    app.after(0, lambda: processo_cancelado())
                    return
                try:
                    tam = os.path.getsize(arq)
                    h = hash_arquivo(arq)
                    if h:
                        por_hash[(tam, h)].append(arq)
                except:
                    pass
                processados += 1
                if processados % 20 == 0:
                    app.after(0, lambda p=processados: atualizar_progresso(p, total_candidatos, "Comparando conteúdo"))
            achados = []
            for (tam, h), iguais in por_hash.items():
                if len(iguais) < 2:
                    continue
                da_A = [x for x in iguais if x.startswith(pa)]
                da_B = [x for x in iguais if x.startswith(pb)]
                if da_A and da_B:
                    for arq_a in da_A:
                        achados.append((arq_a, tam, h, da_B[0]))
            app.after(0, lambda: atualizar_progresso(total_candidatos, total_candidatos, "Concluído!"))
            app.after(0, lambda: mostrar_resultado(achados))
        except Exception as e:
            app.after(0, lambda: messagebox.showerror("Erro", str(e)))
    threading.Thread(target=rodar, daemon=True).start()

def mostrar_resultado(achados):
    btn_comparar.config(state="normal", text="COMPARAR AGORA")
    btn_cancelar.config(state="disabled")
    progress["value"] = 100
    tree.delete(*tree.get_children())
    duplicados.clear()
    total_liberar = sum(tam for _, tam, _, _ in achados)
    lbl_status.config(text=f"Encontrado {len(achados)} arquivos pra apagar SÓ DA PASTA A | Total: {total_liberar/1024/1024:.1f} MB que dá pra liberar")
    lbl_prog.config(text=f"Concluído! - 100% ({len(achados)} arquivos duplicados da A)")
    for arq_apagar, tam, h, arq_original in achados:
        nome = os.path.basename(arq_apagar)
        duplicados.append((arq_apagar, tam, h))
        tree.insert("", "end", values=("[A] APAGAR", nome, f"{tam/1024/1024:.2f} MB", f"Já existe em: {arq_original}"))

def apagar_selecionados():
    selecionados = tree.selection()
    if not selecionados:
        messagebox.showwarning("Ops", "Selecione os arquivos que quer apagar!")
        return
    total_mb = 0
    lista_apagar = []
    for item in selecionados:
        idx = tree.index(item)
        caminho_a, tam, h = duplicados[idx]
        lista_apagar.append(caminho_a)
        total_mb += tam / 1024 / 1024
    aviso = (
        f"ATENÇÃO! LEIA COM CALMA\n\n"
        f"Você vai apagar {len(lista_apagar)} arquivo(s) da PASTA A:\n"
        f"{pasta_a_var.get()}\n\n"
        f"Total a liberar: {total_mb:.1f} MB\n\n"
        f"Depois, as PASTAS VAZIAS que sobrarem dentro da Pasta A também serão apagadas.\n\n"
        f"NENHUM arquivo será apagado da PASTA B (referência segura):\n"
        f"{pasta_b_var.get()}\n\n"
        f"Essa ação NÃO pode ser desfeita!\n"
        f"Tem certeza que quer continuar?"
    )
    confirmar = messagebox.askyesno("CONFIRMAR EXCLUSÃO - SÓ DA PASTA A", aviso)
    if not confirmar:
        return
    apagados = 0
    for caminho in lista_apagar:
        if not caminho.startswith(pasta_a_var.get()):
            continue
        try:
            os.remove(caminho)
            apagados += 1
        except Exception as e:
            print(f"Erro ao apagar {caminho}: {e}")
    pastas_limpas = remover_pastas_vazias(pasta_a_var.get())
    if pastas_limpas > 0:
        messagebox.showinfo("Pronto", f"{apagados} arquivo(s) apagados SOMENTE da Pasta A!\n+ {pastas_limpas} pasta(s) vazia(s) também apagadas.")
    else:
        messagebox.showinfo("Pronto", f"{apagados} arquivo(s) apagados SOMENTE da Pasta A!")
    comparar_thread()

app.mainloop()