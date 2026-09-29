"""Falha se algum notebook tiver células com outputs ou execution_count."""

import json
import sys
from pathlib import Path


def dirty_cells(path: Path) -> list[int]:
    """Retorna os índices das células de código não limpas.

    Args:
        path: Caminho do notebook (.ipynb).

    Returns:
        Lista com os índices das células que ainda têm output/execução.
    """
    nb = json.loads(path.read_text(encoding="utf-8"))
    return [
        i
        for i, cell in enumerate(nb.get("cells", []))
        if cell.get("cell_type") == "code"
        and (cell.get("outputs") or cell.get("execution_count") is not None)
    ]


def main(args: list[str]) -> int:
    """Verifica os notebooks recebidos (ou todos em notebooks/).

    Args:
        args: Caminhos dos notebooks; vazio = varre notebooks/.

    Returns:
        0 se todos estiverem limpos, 1 caso contrário.
    """
    paths = [Path(a) for a in args] or sorted(Path("notebooks").rglob("*.ipynb"))
    failed = False
    for path in paths:
        cells = dirty_cells(path)
        if cells:
            failed = True
            print(f"✗ {path}: células com output -> {cells}")
    if failed:
        print("\nLimpe antes de subir:  make nb-clean")
        return 1
    print(f"✓ {len(paths)} notebook(s) limpo(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
