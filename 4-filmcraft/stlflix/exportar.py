"""Exportação de XML (FCP7) das sequências para o Drive, guardando as versões anteriores numa subpasta."""
import datetime
import os
import shutil
import tempfile


def xmls(fc, nomes_seq, destino):
    seqs = fc.sequencias()
    os.makedirs(destino, exist_ok=True)
    backup = os.path.join(destino, f"_XML anteriores ({datetime.datetime.now():%d-%m %Hh%M})")
    feitos = []
    for nome in nomes_seq:
        tmp = os.path.join(tempfile.gettempdir(), f"{nome}.xml")
        fc.run("file.exportInterchange", format="xml", path=tmp, sequence=seqs[nome])
        final = os.path.join(destino, f"{nome}.xml")
        if os.path.exists(final):                  # nunca sobrescreve: a versão anterior vai para o backup
            os.makedirs(backup, exist_ok=True)
            shutil.move(final, os.path.join(backup, f"{nome}.xml"))
        shutil.copyfile(tmp, final)                # grava local e copia: escrita direta no Drive é instável
        if os.path.getsize(final) != os.path.getsize(tmp):
            raise IOError(f"cópia incompleta: {final}")
        os.remove(tmp)
        feitos.append(final)
    return feitos
