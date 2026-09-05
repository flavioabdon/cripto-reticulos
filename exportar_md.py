#!/usr/bin/env python3
"""
Script para consolidar y exportar todos los archivos .md del proyecto en un único archivo Markdown.
"""

from datetime import datetime
from pathlib import Path

# Directorio raíz del proyecto
ROOT_DIR = Path(__file__).resolve().parent

# Nombre del archivo de salida
OUTPUT_FILE = ROOT_DIR / "documentacion_consolidada.md"

# Orden preferente de los archivos para una lectura lógica
ORDER_PRIORITY = [
    "README.md",
    "plan.md",
    "prompt_desarrollo_protocolo_votacion_pqc.md",
    "docs/arquitectura.md",
    "docs/diagrama_flujo.md",
    "docs/reporte_tesis.md",
    "docs/estructura_proyecto.md",
    "analisis_estadistico/reporte_estadistico.md",
    "validacion/kat/reporte_kat.md",
    "tamarin/README.md",
]


def obtener_archivos_md():
    """Busca todos los .md excluyendo directorios virtuales, .git y el archivo de salida."""
    md_files = []
    for path in ROOT_DIR.rglob("*.md"):
        # Ignorar venv, directorios ocultos o el propio archivo de salida consolidado
        if any(part.startswith(".") or part in ("venv", "node_modules", "build") for part in path.parts):
            continue
        if path.resolve() == OUTPUT_FILE.resolve():
            continue
        md_files.append(path)

    # Ordenar según lista de prioridad y alfabéticamente el resto
    def sort_key(p: Path):
        rel = p.relative_to(ROOT_DIR).as_posix()
        if rel in ORDER_PRIORITY:
            return (0, ORDER_PRIORITY.index(rel))
        return (1, rel)

    return sorted(md_files, key=sort_key)


def consolidar_markdown():
    archivos = obtener_archivos_md()
    print(f"[*] Se encontraron {len(archivos)} archivos Markdown para consolidar.")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        # Portada / Encabezado principal
        out.write("# Documentación Consolidada del Proyecto\n\n")
        out.write(
            "> **Tesis:** Protocolo para la votación electrónica basado en criptografía post-cuántica de retículos\n"
        )
        out.write(f"> **Fecha de generación:** {timestamp}\n")
        out.write(f"> **Total de documentos incluidos:** {len(archivos)}\n\n")
        out.write("---\n\n")

        # Índice interactivo
        out.write("## Índice de Documentos\n\n")
        for idx, file_path in enumerate(archivos, 1):
            rel_path = file_path.relative_to(ROOT_DIR).as_posix()
            anchor = rel_path.replace("/", "-").replace(".", "-").replace("_", "-").lower()
            out.write(f"{idx}. [{rel_path}](#documento-{anchor})\n")
        out.write("\n---\n\n")

        # Contenido de cada archivo
        for idx, file_path in enumerate(archivos, 1):
            rel_path = file_path.relative_to(ROOT_DIR).as_posix()
            anchor = rel_path.replace("/", "-").replace(".", "-").replace("_", "-").lower()
            print(f"  -> Agregando [{idx}/{len(archivos)}]: {rel_path}")

            out.write(f'<a id="documento-{anchor}"></a>\n\n')
            out.write(f"# Documento {idx}: `{rel_path}`\n\n")
            out.write(f"> **Ruta original:** `{rel_path}`\n\n")

            try:
                content = file_path.read_text(encoding="utf-8")
                out.write(content.strip())
                out.write("\n\n---\n\n")
            except Exception as e:
                out.write(f"\n*Error al leer el archivo: {e}*\n\n---\n\n")

    print(f"\n[+] Consolidación completada con éxito.")
    print(f"[+] Archivo generado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    consolidar_markdown()
