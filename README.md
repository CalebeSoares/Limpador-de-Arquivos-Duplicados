Projeto desenvolvido por mim, com assistência de IA (Meta AI) na codificação.

# Limpador-de-Arquivos-Duplicados
Escreve Limpa arquivos duplicados comparando duas pastas, sem apagar a pasta segura.

# Limpador de Duplicados

Encontrei que meus HDs estavam cheios de arquivos duplicados. Criei esse programa para comparar duas pastas e apagar com segurança só os arquivos que já existem na outra pasta.

### Como funciona?

**Pasta A** = A que vai ser limpa (de onde apaga)
**Pasta B** = Referência segura (nunca apaga daqui)

O programa compara o conteúdo real dos arquivos (hash MD5), não só o nome. Se o arquivo da Pasta A for idêntico a um da Pasta B, ele aparece na lista para apagar.

### Recursos

- Interface gráfica com Tkinter + estilo Bootstrap
- Seletor de pastas com Zenity (janela nativa do Linux)
- Comparação por hash, rápida e segura
- Barra de progresso + botão Cancelar
- Trava de segurança: só apaga da Pasta A
- Aviso de confirmação antes de apagar
- Apaga pastas vazias que sobram depois da limpeza
- Paleta personalizada

### Paleta de cores

- `#02201D` - Fundo escuro
- `#03665C` - Verde escuro
- `#03A688` - Verde vivo
- `#81E8D4` - Verde claro
- `#E1F0ED` - Fundo
- `#6FBF9F` - Verde médio
- `#F6F0E0` - Creme

### Como usar

```bash
# Instalar o Zenity (Linux)
sudo apt install zenity

# Rodar o programa
python3 main.py
