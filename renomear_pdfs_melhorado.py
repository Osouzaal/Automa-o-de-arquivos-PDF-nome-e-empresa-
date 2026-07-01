# -*- coding: utf-8 -*-
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


PDFTOTEXT = Path(r"C:\poppler\poppler-24.08.0\Library\bin\pdftotext.exe")
PASTA = Path(r"C:\Users\Metal\Desktop\29999")


ARTE_SUCESSO = r"""
__________________1________________1
_________________11________________11
_______________111__________________111
_____________1111____________________1111
____________11111____________________11111
___________11111______________________11111
__________111111______________________111111
__________1111111__1111111111111111__1111111
__________1111111111111111111111111111111111
___________11111111111111111111111111111111
____________11111111____111111____11111111
___1________1111111______1111______1111111
___1_______11111111___1_11111__1__11111111
__111______111111111____111111____111111111
__111_____111111111111111111111111111111111
_11111____111111111111111111111111111111__11
_11111____111__11111111111111111111111__111
___11_____111__11111111111111111111111__111
___11______111_____111111111111111_____11
____11______11________1111111111_______11
_____11______111_______________________1
_____11________11____1111111111111____1
______11________111_____11111111111__1
_______11__________111_____111111111
_________11___________1111__111111111
____________________________1111111111
_____________________________111111111
______________________________1111111
"""


ARTE_ERRO = r"""
__________________________________________________
__________________________________________________
__________________10000000000011__________________
_______________10000000000000000001_______________
_____________00000000000000000000000______________
____________00000111000000001111100001____________
__________10001_______10001_______10001___________
_________1000__________11___________000___________
_________0001_____101_______11______1000__________
_________000______101_______11______1000__________
________10001___________1___________10001_________
________100001_________101_________100001_________
________10000001_____1000001_____10000001_________
_________0000000000000000000000000000000__________
_________1000000000001______100000000000__________
__________000000001____________100000001__________
___________0000001______________1000001___________
____________00000____10000001____00001____________
_____________0000__100000000000_1001____111_______
______1________0000000000000000001_____00000______
_____00000________11000000000001____1000000011____
_____00000001_____________________100000000000____
____0000000000001______________100000000000001____
____000000000000000011_____110000111______________
_________________0100000000000011__1______________
___________11_1100000001___1100000000000000001____
____0000000000000001___________110000000000000____
____00000000000011_________________110000000011___
_____000000001_________________________1000001____
_____100001_______________________________1001____
_______11_________________________________________
"""


def configurar_utf8() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    if os.name == "nt":
        os.system("chcp 65001 > nul")


def limpar_nome_arquivo(texto: str) -> str:
    invalidos = '<>:"/\\|?*'
    limpo = texto.strip()

    for char in invalidos:
        limpo = limpo.replace(char, "")

    limpo = re.sub(r"\s+", " ", limpo)
    return limpo.strip()


def obter_caminho_unico(diretorio: Path, nome_base: str) -> Path:
    candidato = diretorio / f"{nome_base}.pdf"
    contador = 2

    while candidato.exists():
        candidato = diretorio / f"{nome_base} ({contador}).pdf"
        contador += 1

    return candidato


def ler_texto_extraido(arquivo_txt: Path) -> str:
    try:
        return arquivo_txt.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return arquivo_txt.read_text(encoding="cp1252", errors="replace")


def extrair_campo(conteudo: str, campo: str) -> str | None:
    match = re.search(rf"^\s*{re.escape(campo)}:\s*(.+?)\s*$", conteudo, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None

    return match.group(1).strip()


def processar_arquivo(arquivo: Path) -> None:
    nome_base = arquivo.stem
    arquivo_txt = PASTA / f"{nome_base}.txt"
    temp_pdf_path = None

    try:
        with tempfile.NamedTemporaryFile(dir=PASTA, suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf_path = Path(temp_pdf.name)

        shutil.copy2(arquivo, temp_pdf_path)

        resultado = subprocess.run(
            [str(PDFTOTEXT), "-layout", "-enc", "UTF-8", str(temp_pdf_path), str(arquivo_txt)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        if resultado.returncode != 0:
            print(f"Não foi possível extrair texto de: {arquivo.name}")
            return

        if not arquivo_txt.exists():
            print(f"Não foi possível extrair texto de: {arquivo.name}")
            return

        conteudo = ler_texto_extraido(arquivo_txt)
        nome = extrair_campo(conteudo, "NOME")
        empresa = extrair_campo(conteudo, "EMPRESA")

        if not nome or not empresa:
            print(f"Padrão NOME e EMPRESA não encontrados em: {arquivo.name}. Pulando...")
            return

        nome = limpar_nome_arquivo(nome)
        empresa = limpar_nome_arquivo(empresa)

        if not nome or not empresa:
            print(f"Nome ou empresa vazios em: {arquivo.name}. Pulando...")
            return

        novo_nome_base = limpar_nome_arquivo(f"{nome} {empresa}")
        novo_caminho = obter_caminho_unico(PASTA, novo_nome_base)

        if os.path.normcase(os.path.abspath(arquivo)) == os.path.normcase(os.path.abspath(novo_caminho)):
            print(f"Arquivo já está com o nome correto: {arquivo.name}")
            return

        arquivo.rename(novo_caminho)
        print(f"Renomeado: {arquivo.name} -> {novo_caminho.name}")
    except Exception as erro:
        print(f"Falha ao processar '{arquivo.name}': {erro}")
    finally:
        if temp_pdf_path and temp_pdf_path.exists():
            temp_pdf_path.unlink(missing_ok=True)
        if arquivo_txt.exists():
            arquivo_txt.unlink(missing_ok=True)


def main() -> int:
    configurar_utf8()

    try:
        if not PDFTOTEXT.is_file():
            raise FileNotFoundError(f"pdftotext.exe não encontrado em: {PDFTOTEXT}")

        if not PASTA.is_dir():
            raise FileNotFoundError(f"Pasta não encontrada: {PASTA}")

        arquivos = [
            item
            for item in PASTA.iterdir()
            if item.is_file() and (item.suffix.lower() == ".pdf" or item.suffix == "")
        ]

        for arquivo in arquivos:
            processar_arquivo(arquivo)

        print("MUDANÇAS FEITAS COM SUCESSO!")
        print(ARTE_SUCESSO)
        return 0
    except Exception as erro:
        print(f"SCRIPT FALHOU: {erro}")
        print(ARTE_ERRO)
        return 1
    finally:
        input("Pressione ENTER para sair...")


if __name__ == "__main__":
    raise SystemExit(main())
