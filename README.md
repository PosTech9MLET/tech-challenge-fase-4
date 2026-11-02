#

> Descrição curta do problema de negócio e da solução de ML.

## Estrutura

~~~
├── .github/workflows/   # CI/CD (GitHub Actions)
├── configs/             # arquivos de configuração (yaml/json)
├── data/                # raw → interim → processed → features (fora do Git)
├── docs/                # model card, arquitetura, ADRs
├── models/              # artefatos treinados (fora do Git)
├── notebooks/           # exploratory/ e reports/ (sempre sem outputs)
├── reports/figures/     # gráficos gerados
├── scripts/             # utilitários (check_notebooks.py, ...)
├── src/                 # código de produção
│   ├── data/  features/  models/  training/  pipelines/  api/  utils/
│   └── main.py
└── tests/               # unit/ e integration/
~~~

## Quick start

### Pré-requisitos

- Python 3.12
- Git
- uv

### Instalação

```bash
uv python install 3.12
uv sync --locked
```

Copie `.env.example` para `.env`.

No Git Bash:

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

### Execução

```bash
uv run python src/main.py
```

### Testes e qualidade

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format . --check
uv run python scripts/check_notebooks.py
```

### Pre-commit

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```


## Qualidade

| Ferramenta | Uso |
|---|---|
| ruff | lint + format (regras E, F, I, N, UP, D, B, SIM) |
| pytest + pytest-cov | testes e cobertura |
| radon / xenon | complexidade ciclomática e manutenibilidade |
| nbstripout + check_notebooks.py | notebooks sem outputs no Git |
| pre-commit | roda tudo antes de cada commit |

## Convenção de commits

feat · fix · docs · refactor · test · chore
