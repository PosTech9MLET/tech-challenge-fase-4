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

~~~bash
cp .env.example .env
make install     # uv sync + pre-commit install
make check       # lint + testes + complexidade + notebooks
make run
~~~

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
