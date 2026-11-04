
# Tech Challenge Fase 4 — Machine Learning Engineering

## Observabilidade, Data Drift e Governança de Modelos

Projeto desenvolvido para a Pós-Tech em Machine Learning
Engineering da FIAP.

### Contexto

Uma fintech utiliza um modelo de Credit Scoring para
avaliar o risco de inadimplência de seus clientes.

Mudanças no perfil dos clientes e nas condições econômicas
podem provocar degradação silenciosa no desempenho do modelo.

### Objetivo

Desenvolver uma solução de sustentação e confiabilidade
para modelos de Machine Learning, contemplando:

- Validação e qualidade de dados com Pandera.
- Simulação e detecção de Data Drift com Evidently.
- Monitoramento de pipelines, métricas e alertas.
- Governança, privacidade e conformidade com a LGPD.

O projeto utiliza o dataset Home Credit Default Risk
como base para o desenvolvimento e as simulações.

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


## Data Contracts — Home Credit

A validação dos dados é realizada com Pandera, utilizando
o dataset Home Credit Default Risk.

### Dataset

Fonte:
https://www.kaggle.com/competitions/home-credit-default-risk/data

Baixe o arquivo `application_train.csv` e coloque em:

`data/raw/application_train.csv`

Os dados originais não são versionados no Git.

### Executar a validação

```bash
uv sync --locked
uv run python -m scripts.validate_home_credit
```

### Demonstrar bloqueio de dados inválidos

```bash
uv run python -m scripts.demo_invalid_batch
```

O script cria uma cópia de um lote real, introduz erros
controlados e demonstra sua rejeição pelo Pandera.

### Testes automatizados

```bash
uv run pytest tests/unit/test_contracts.py -v
```

### Regras implementadas

- Identificador obrigatório e único.
- Renda e crédito maiores que zero.
- Validação de idade mínima aproximada de 18 anos.
- Quantidade de filhos não negativa.
- TARGET binário, obrigatório no treinamento.
- AMT_ANNUITY permite nulos nos dados brutos.
- Inferência não exige TARGET.

O contrato cobre inicialmente oito colunas selecionadas
das 122 disponíveis no dataset.

A integração com o modelo de Credit Scoring será realizada
quando o pipeline de treinamento e inferência estiver pronto.


### Limitações e próximos passos

O contrato atual valida oito colunas selecionadas
do Home Credit.

A coluna AMT_ANNUITY permite valores ausentes nos dados
brutos. O tratamento desses registros deverá ser definido
na etapa de pré-processamento do modelo.

O contrato de treinamento exige TARGET binário.
O contrato de inferência não exige essa coluna.

A validação é realizada antes do processamento, mas
a integração com o pipeline de inferência ainda está
pendente.

As próximas etapas incluem treinamento do baseline,
simulação de drift, observabilidade e governança.
