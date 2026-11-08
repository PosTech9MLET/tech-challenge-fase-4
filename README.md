# Tech Challenge Fase 4 - Machine Learning Engineering

## Observabilidade, Data Drift e Governança de Modelos

Projeto desenvolvido para a Pós-Tech em Machine Learning Engineering da FIAP.

## Contexto

Uma fintech utiliza um modelo de *Credit Scoring* para estimar o risco de inadimplência de seus clientes. Mudanças no perfil da população atendida ou nas condições econômicas podem alterar as distribuições dos dados e afetar o comportamento das previsões.

Além de treinar um modelo, é necessário validar os dados de entrada, identificar possíveis mudanças de distribuição, acompanhar indicadores operacionais e documentar limitações e riscos.

## Objetivo

Desenvolver uma solução de sustentação e confiabilidade para modelos de Machine Learning, contemplando:

- Qualidade de dados e contratos de validação com Pandera.
- Baseline de Credit Scoring com XGBoost e rastreamento de experimentos no MLflow.
- Simulação e detecção de Data Drift com Evidently.
- Análise do impacto do drift nas predições do modelo.
- Evolução para monitoramento operacional, métricas e alertas.
- Documentação de governança, privacidade, LGPD e limitações do modelo.

O projeto utiliza o dataset **Home Credit Default Risk** como base para o desenvolvimento e as simulações.

## Estrutura do projeto

```text
├── .github/workflows/    # Automação e verificações de CI
├── configs/              # Arquivos de configuração
├── data/                 # Dados raw, interim, processed e features
├── docs/                 # Documentação técnica e governança
├── models/               # Modelos e métricas salvos localmente
├── notebooks/            # Análises exploratórias, sem outputs no Git
├── reports/              # Relatórios e indicadores de monitoramento
│   └── figures/          # Figuras geradas
├── scripts/              # Scripts de execução e demonstração
├── src/
│   ├── data/             # Carga, contratos e simulação de drift
│   ├── features/         # Engenharia de atributos
│   ├── models/           # Pipeline e persistência do baseline
│   ├── training/         # Treinamento e avaliação
│   ├── pipelines/        # Preparação e monitoramento
│   ├── api/              # Componentes de API
│   └── utils/            # Configurações e utilitários
├── tests/                # Testes automatizados
├── pyproject.toml        # Dependências e configurações
└── uv.lock               # Versões resolvidas das dependências
```

Os dados brutos, os datasets processados e os modelos treinados são artefatos locais e **não devem ser enviados ao GitHub**.

## Quick start

### Pré-requisitos

- Python 3.12.
- Git.
- [uv](https://docs.astral.sh/uv/).

### Instalação

```bash
uv python install 3.12
uv sync --locked
```

Copie `.env.example` para `.env`, quando necessário para a configuração local.

No Git Bash:

```bash
cp .env.example .env
```

No PowerShell:

```powershell
Copy-Item .env.example .env
```

### Dataset

Fonte: [Home Credit Default Risk no Kaggle](https://www.kaggle.com/competitions/home-credit-default-risk/data).

Baixe o arquivo `application_train.csv` e coloque-o em:

```text
data/raw/application_train.csv
```

O dataset não é versionado neste repositório.

### Executar o fluxo completo

Os comandos abaixo devem ser executados na raiz do projeto, nesta ordem:

```bash
# 1. Validar os dados de entrada
uv run python -m scripts.validate_home_credit

# 2. Gerar as bases de referência e produção
uv run python -m src.pipelines.prepare_data

# 3. Treinar e registrar o baseline
uv run python -m src.training.train

# 4. Simular alterações nos dados de produção
uv run python -m scripts.simulate_home_credit_drift

# 5. Detectar drift e gerar relatórios/alertas
uv run python -m scripts.run_drift

# 6. Comparar as predições antes e depois do drift
uv run python -m scripts.analyze_score_impact
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

## Qualidade de código

| Ferramenta | Finalidade |
|---|---|
| Ruff | Lint e formatação do código Python |
| Pytest e pytest-cov | Testes automatizados e medição de cobertura |
| Pre-commit | Verificações antes dos commits |
| nbstripout e check_notebooks.py | Evitar outputs de notebooks versionados |
| Radon e Xenon | Apoio à análise de complexidade e manutenibilidade, quando utilizados |

**Convenção de commits:** `feat`, `fix`, `docs`, `refactor`, `test` e `chore`.

## Data Contracts - Home Credit

A validação é realizada com **Pandera**, utilizando colunas selecionadas do Home Credit Default Risk.

### Regras implementadas

- `SK_ID_CURR`: identificador obrigatório e único.
- `AMT_INCOME_TOTAL` e `AMT_CREDIT`: valores maiores que zero.
- `DAYS_BIRTH`: idade mínima aproximada de 18 anos, considerando a codificação negativa em dias.
- `CNT_CHILDREN`: quantidade de filhos não negativa.
- `TARGET`: valor binário e obrigatório para treinamento.
- `AMT_ANNUITY`: permite valores ausentes nos dados brutos; quando presente, deve ser positivo.
- `NAME_INCOME_TYPE`: categoria obrigatória.
- Na inferência, o contrato não exige a coluna `TARGET`.

O contrato valida inicialmente **oito colunas das 122 disponíveis** no arquivo de treinamento. As demais colunas utilizadas pelo modelo não estão todas cobertas por essas regras.

### Executar a validação

```bash
uv run python -m scripts.validate_home_credit
```

Na execução com o dataset completo, o contrato aprovou **307.511 registros**.

### Demonstrar rejeição de lote inválido

```bash
uv run python -m scripts.demo_invalid_batch
```

O script introduz erros controlados em uma cópia de um lote real, como identificador duplicado, renda negativa, crédito igual a zero, idade inválida e `TARGET` fora do domínio aceito. O Pandera rejeita o lote inválido.

### Testes dos contratos

```bash
uv run pytest tests/unit/test_contracts.py -v
```

### Integração e limitações

Os contratos estão integrados ao pipeline de preparação e à validação dos dados de treinamento. Antes de gerar as bases de referência e produção, a entrada é validada e um lote inválido bloqueia a execução.

O contrato de treinamento exige `TARGET` binário, enquanto o contrato de inferência não exige essa coluna. A função de scoring já existe, mas **não executa automaticamente a validação Pandera em cada chamada**; essa integração deve ser considerada na futura interface operacional de inferência.

`AMT_ANNUITY` aceita valores ausentes nos dados brutos. O XGBoost utilizado no baseline é capaz de lidar com valores numéricos ausentes, sem exigir que o contrato rejeite esses registros.

## Baseline de Credit Scoring com XGBoost e MLflow

O baseline utiliza **XGBoost** em um pipeline do **Scikit-Learn** para estimar a probabilidade de inadimplência. O **MLflow** registra parâmetros, métricas e artefatos do experimento.

### Preparação e engenharia de atributos

O pipeline:

1. Carrega as colunas necessárias de `application_train.csv`.
2. Valida os dados com Pandera.
3. Divide os registros de forma estratificada em **referência (70%)** e **produção simulada (30%)**.
4. Separa 20% da referência para validação do modelo.
5. Aplica engenharia de atributos e codificação das variáveis categóricas.

As variáveis derivadas incluem:

- `AGE_YEARS`.
- `CREDIT_INCOME_RATIO`.
- `ANNUITY_INCOME_RATIO`.
- `CREDIT_TERM`.
- `EMPLOYED_RATIO`.

O valor sentinela `365243` de `DAYS_EMPLOYED` é tratado como ausente. A variável `CODE_GENDER` **não integra os atributos do modelo** e é utilizada apenas na análise de métricas por grupo.

### Executar preparação e treinamento

```bash
uv run python -m src.pipelines.prepare_data
uv run python -m src.training.train
```

Arquivos locais gerados:

```text
data/processed/reference.parquet
data/processed/production_base.parquet
models/baseline.joblib
models/baseline_metrics.json
```

O treinamento também registra o experimento `credit-scoring-baseline` no MLflow, conforme a configuração local.

### Resultados do baseline

Resultados reproduzidos na validação, com 20% da base de referência:

| Métrica | Valor |
|---|---:|
| ROC-AUC | 0,7657 |
| KS | 0,4007 |
| PR-AUC (Average Precision) | 0,2410 |
| F1-score | 0,3092 |
| Limiar de classificação | 0,1432 |

O baseline apresenta capacidade de discriminação, mas ainda exige acompanhamento e validação em outros cenários.

**Limitação metodológica:** o limiar foi escolhido para maximizar o F1 no mesmo conjunto de validação usado para reportá-lo. É recomendável avaliá-lo também em dados independentes, evitando uma interpretação excessivamente otimista do F1.

### Análise inicial por grupos

O treinamento calcula ROC-AUC por gênero e faixa etária, como verificação exploratória de possíveis diferenças no comportamento do modelo.

| Grupo | ROC-AUC |
|---|---:|
| Feminino | 0,7671 |
| Masculino | 0,7515 |
| Menos de 30 anos | 0,7505 |
| 30 a 44 anos | 0,7653 |
| 45 a 59 anos | 0,7627 |
| 60 anos ou mais | 0,7290 |

Diferenças entre os grupos **não comprovam, isoladamente, discriminação**. Uma investigação mais completa requer análise das taxas de erro, tamanhos amostrais, representatividade e possíveis variáveis correlacionadas com atributos sensíveis.

## Monitoramento de Data Drift com Evidently

O monitoramento utiliza **Evidently** para comparar distribuições de dados e identificar mudanças em duas variáveis financeiras, além de analisar seus efeitos nas predições do XGBoost.

### Desenho do experimento

A base histórica foi dividida aleatoriamente em:

- **Referência:** 215.257 registros.
- **Produção simulada:** 92.254 registros.

Não há sobreposição de `SK_ID_CURR` entre essas bases. Essa separação é útil para o experimento, mas **não equivale a uma comparação temporal real** entre períodos de produção.

São executados dois cenários:

1. **Original:** referência versus produção sem alterações artificiais.
2. **Simulado:** referência versus produção com mudanças controladas.

### Simulação de Data Drift

A função `simulate_income_credit_drift` modifica **80% dos registros de produção**, selecionados com semente aleatória `42`:

- `AMT_INCOME_TOTAL`: aumento de 80% nos registros selecionados (`× 1,80`).
- `AMT_CREDIT`: aumento de 70% nos registros selecionados (`× 1,70`).

As médias gerais da base de produção aumentaram **64,01% para renda** e **56,01% para crédito**. Os registros originais são preservados em outro arquivo, e os dados simulados continuam passando no contrato Pandera.

Esse é um **cenário artificial de estresse**, não uma alteração econômica observada no mercado de crédito.

### Detecção estatística com Evidently

O Evidently utiliza **PSI (Population Stability Index)**, com limiar experimental de **0,20**, em amostras reproduzíveis de **5.000 registros por base**.

| Variável | PSI original | PSI simulado | Resultado simulado |
|---|---:|---:|---|
| `AMT_INCOME_TOTAL` | 0,0020 | 0,6733 | Drift detectado |
| `AMT_CREDIT` | 0,0076 | 0,4521 | Drift detectado |

No cenário original, nenhuma variável ultrapassou o limiar. No cenário simulado, **as duas variáveis geraram alerta**, resultando em `2/2` colunas sinalizadas.

O limiar de PSI foi adotado para fins demonstrativos e deve ser calibrado conforme o contexto e o volume de dados em aplicações reais.

### Alertas estruturados

O pipeline extrai os resultados do Evidently e registra, para cada variável:

- Valor de PSI.
- Limiar utilizado.
- Indicador de alerta (`true` ou `false`).

Os indicadores são armazenados em `reports/drift_alerts.json`. **Ainda não há envio automático de notificações nem agendamento contínuo do monitoramento.**

### Impacto nas predições do XGBoost

O mesmo modelo treinado avalia os **92.254 clientes** antes e depois da simulação, com alinhamento por `SK_ID_CURR` e limiar de decisão fixo em aproximadamente `0,1432`.

| Métrica | Produção original | Produção simulada |
|---|---:|---:|
| Score médio | 0,0806 | 0,0746 |
| Proporção acima do limiar | 15,01% | 13,21% |

| Indicador de impacto | Resultado |
|---|---:|
| Mudança absoluta média dos scores | 0,0164 |
| Classificações alteradas | 4.277 |
| Percentual de classificações alteradas | 4,64% |

Os resultados mostram que a simulação afetou os scores e as decisões produzidas pelo modelo. **Isso não prova queda na qualidade preditiva, nem estabelece uma relação causal sobre o risco real de inadimplência.**

### Executar o monitoramento

Após preparar as bases e treinar o baseline:

```bash
uv run python -m scripts.simulate_home_credit_drift
uv run python -m scripts.run_drift
uv run python -m scripts.analyze_score_impact
```

### Artefatos gerados

```text
data/processed/production_drift.parquet
reports/drift_baseline.html
reports/drift_baseline.json
reports/drift_simulated.html
reports/drift_simulated.json
reports/drift_alerts.json
reports/score_impact.json
```

Os arquivos HTML permitem inspecionar visualmente as distribuições e devem ser gerados localmente. Os JSONs registram os resultados de forma estruturada. Recomenda-se manter os relatórios HTML gerados fora do controle de versão, por seu tamanho, e versionar apenas os JSONs necessários como evidências.

### Testes do monitoramento

```bash
uv run pytest tests/unit/test_drift.py -v
uv run pytest tests/unit/test_drift_monitor.py -v
uv run pytest tests/unit/test_score_impact.py -v
```

A suíte completa apresentou **40 testes aprovados** no ambiente de desenvolvimento durante a implementação desta funcionalidade.

### Limitações do experimento de drift

- A produção representa uma divisão aleatória do histórico, não um lote coletado em período posterior.
- Foram monitoradas duas variáveis com uma amostra de 5.000 registros por base, não todas as entradas do modelo.
- O PSI é sensível às distribuições, à amostragem e à escolha de intervalos; o limiar de 0,20 não é uma regra universal.
- O cenário de estresse foi definido para tornar as mudanças detectáveis e não representa uma previsão de alterações reais.
- A comparação das predições mede alteração de comportamento, não degradação comprovada de desempenho.

## Observabilidade e governança: próximos passos

A implementação atual já registra métricas e experimentos com MLflow e produz relatórios e alertas estruturados de Data Drift. Para completar a solução de sustentação e governança, permanecem como próximos passos:

- Definir e instrumentar logs operacionais e indicadores de execução dos pipelines.
- Avaliar monitoramento recorrente, gatilhos de alerta e canais de notificação.
- Acompanhar a qualidade preditiva em bases rotuladas independentes, quando disponíveis.
- Documentar governança, ciclo de vida do modelo, responsabilidade por decisões e critérios de revisão.
- Tratar privacidade e LGPD, incluindo minimização de dados, finalidade, controle de acesso e retenção.
- Aprofundar a análise de viés e registrar limitações de representatividade.
- Diferenciar associação estatística de causalidade e descrever o que o experimento permite ou não concluir.
- Preparar a demonstração e o vídeo STAR solicitados no Tech Challenge.

## Validação final

Para reproduzir os principais testes e verificações:

```bash
uv run pytest -v
uv run ruff check .
uv run ruff format . --check
uv run pre-commit run --all-files
```
