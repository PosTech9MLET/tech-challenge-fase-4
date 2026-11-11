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
- Observabilidade operacional com logs estruturados, métricas Prometheus e dashboard Grafana.
- Regras automáticas de alerta para Data Drift e indisponibilidade da coleta.
- Documentação de governança, privacidade, LGPD e limitações do modelo, com trabalhos futuros claramente identificados.

O projeto utiliza o dataset **Home Credit Default Risk** como base para o desenvolvimento e as simulações.

## Estrutura do projeto

```text
├── .github/workflows/             # Automação e verificações de CI
├── compose.observability.yaml      # Stack local de observabilidade
├── configs/                       # Configurações da aplicação
├── data/                          # Dados raw, interim, processed e features
├── docs/                          # Documentação técnica e governança
├── infra/observability/
│   ├── prometheus/
│   │   ├── prometheus.yml          # Configuração de coleta
│   │   └── alerts.yml              # Regras de alerta
│   └── grafana/
│       ├── dashboard-provider.yml  # Provisionamento dos dashboards
│       ├── dashboards/
│       │   └── credit-scoring-observability.json
│       └── datasources/
│           └── prometheus.yml      # Datasource pré-configurada
├── models/                        # Modelo e métricas locais
├── notebooks/                     # Exploração, sem outputs no Git
├── reports/                       # Relatórios de drift e métricas .prom
├── scripts/                       # Scripts operacionais e demonstrações
│   ├── run_monitored_drift.py      # Pandera + Evidently + Prometheus
│   └── ...
├── src/
│   ├── data/                      # Carga, contratos e simulação de drift
│   ├── features/                  # Engenharia de atributos
│   ├── models/                    # Scoring e persistência
│   ├── training/                  # Treinamento e avaliação
│   ├── pipelines/                 # Preparação e drift
│   ├── monitoring/                # Métricas, logs e validação monitorada
│   ├── api/                       # Componentes de API
│   └── utils/                     # Configurações e utilitários
├── tests/                         # Testes automatizados
├── pyproject.toml                 # Dependências e ferramentas
└── uv.lock                        # Versões resolvidas
```

Os dados brutos, os datasets processados e os modelos treinados são artefatos locais e **não devem ser enviados ao GitHub**.

## Quick start

### Pré-requisitos

- Python 3.12.
- Git.
- [uv](https://docs.astral.sh/uv/).
- Docker Engine / Docker Desktop com plugin Docker Compose **para a observabilidade**; dispensável para executar apenas os scripts Python.
- Acesso ao dataset Home Credit Default Risk para gerar os artefatos locais.

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

O dataset não é versionado no Git: ele é rastreado pelo **DVC** (`data/raw/application_train.csv.dvc` guarda apenas o hash). Ainda não há remote configurado, então cada pessoa baixa o CSV do Kaggle; quando houver um remote, basta `uv run dvc pull`.

### Pipeline reprodutível (DVC)

As etapas abaixo também estão declaradas em `dvc.yaml`. Para executar só o que mudou (dados, código ou parâmetros):

```bash
uv run dvc repro          # roda as etapas desatualizadas
uv run dvc status         # mostra o que está desatualizado
uv run dvc metrics show   # métricas do treino, drift e impacto no score
uv run dvc dag            # grafo das etapas
```

`dvc.lock` registra os hashes de cada execução e deve ser commitado junto com as mudanças.

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

# 7. Executar validação + monitoramento + exportação para Prometheus
uv run python -m scripts.run_monitored_drift
```

A última etapa gera `reports/operational_metrics.prom`. Para iniciar Prometheus e Grafana, consulte a seção [Observabilidade operacional com Docker](#observabilidade-operacional-com-docker).

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
| DVC | Versionamento dos dados e pipeline reprodutível (`dvc.yaml`) |
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

Os indicadores são armazenados em `reports/drift_alerts.json`. Além desses resultados, o script monitorado exporta PSI para o Prometheus e as regras de alerta o avaliam automaticamente. **Ainda não há envio de notificações externas, agendamento contínuo do pipeline nem garantia de atualização dos dados coletados.**

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

Após a implementação de métricas, logs estruturados e integração com Pandera, a suíte completa apresentou **50 testes aprovados** no ambiente de desenvolvimento em 08/11/2026. Esse número reflete aquela execução de testes e pode aumentar conforme o projeto evoluir.

### Limitações do experimento de drift

- A produção representa uma divisão aleatória do histórico, não um lote coletado em período posterior.
- Foram monitoradas duas variáveis com uma amostra de 5.000 registros por base, não todas as entradas do modelo.
- O PSI é sensível às distribuições, à amostragem e à escolha de intervalos; o limiar de 0,20 não é uma regra universal.
- O cenário de estresse foi definido para tornar as mudanças detectáveis e não representa uma previsão de alterações reais.
- A comparação das predições mede alteração de comportamento, não degradação comprovada de desempenho.

## Observabilidade operacional com Docker

A solução possui instrumentação em Python e um ambiente local de monitoramento com **Prometheus, Node Exporter (Textfile Collector) e Grafana**. Foi validada em Windows 11 com Docker Desktop e pode ser reproduzida por outros integrantes do grupo em Windows, macOS ou Linux, desde que os pré-requisitos estejam presentes.

### Arquitetura e fluxo de dados

```text
application_train.csv
       |
       v
Carregamento -> Contratos Pandera -> Evidently (drift simulado)
       |                |                    |
       +----------------+--------------------+
                        |
              Logs JSON no terminal
                        |
              Métricas prometheus_client
                        |
            reports/operational_metrics.prom
                        |
       Docker volume bind mount (somente leitura)
                        |
              Node Exporter :9100
                        |
              Prometheus :9090
               |                |
       Regras de alerta    Histórico de coletas
                               |
                           Grafana :3000
```

**Importante:** o Python é executado localmente via `uv`. O Docker Compose sobe somente os serviços de observabilidade; **não** treina o modelo nem agenda o script de drift automaticamente.

### Componentes implementados

| Componente | Arquivo ou recurso | Responsabilidade |
|---|---|---|
| Métricas Prometheus | `src/monitoring/metrics.py` | Contagem por resultado, duração e PSI |
| Logs JSON | `src/monitoring/logging_config.py` | Registro estruturado sem valores individuais de clientes |
| Validação monitorada | `src/monitoring/validation.py` | Aprovação/rejeição Pandera com log e métrica |
| Orquestração monitorada | `scripts/run_monitored_drift.py` | Carga, validação, drift e exportação `.prom` |
| Textfile Collector | `node-exporter` | Expõe as métricas do arquivo do projeto |
| Prometheus | `infra/observability/prometheus/prometheus.yml` | Coleta a cada 10 segundos |
| Alertas | `infra/observability/prometheus/alerts.yml` | PSI alto e indisponibilidade do exporter |
| Grafana | `infra/observability/grafana/` | Datasource e dashboard provisionados pelo repositório |

#### Métricas disponíveis

| Métrica | Tipo | O que representa |
|---|---|---|
| `credit_pipeline_runs_total{pipeline,status}` | Counter | Resultado da execução **atual/exportada** por etapa; reinicia em um novo processo Python |
| `credit_pipeline_duration_seconds_{sum,count,bucket}` | Histogram | Duração observada na execução exportada, em segundos |
| `credit_data_drift_psi{feature}` | Gauge | PSI da variável monitorada no cenário simulado |

As etapas instrumentadas são `data_loading`, `data_validation` e `drift_monitor`. Os resultados de execução registrados são `success` ou `error`. Em caso de rejeição por contrato Pandera, o log contém `status=rejected` e a métrica de execução contém `status=error`.

#### Logs estruturados

Exemplo de evento emitido ao validar a base real:

```json
{
  "level": "INFO",
  "message": "Lote aprovado",
  "event": "data_validation",
  "status": "approved",
  "records": 307511,
  "pipeline": "home_credit"
}
```

O registro real também contém `timestamp` em UTC. Nos eventos de rejeição são usados `status=rejected` e `error_type`, preservando a exceção Pandera. A instrumentação não inclui rendas, identificadores individuais ou exemplos de registros no log estruturado. Em aplicações reais, logs de outras dependências e rastreamentos de erro também exigem revisão de privacidade.

### Reproduzir a observabilidade no notebook de outro integrante

Os comandos abaixo são executados **na raiz do repositório**. Em Windows, prefira Git Bash ou o terminal do VS Code; em macOS/Linux, utilize um shell compatível. O Docker Desktop deve estar iniciado no Windows e macOS. Em Linux, o Docker Engine deve estar operacional.

**1. Clonar, instalar dependências e preparar o dataset**

```bash
git clone https://github.com/PosTech9MLET/tech-challenge-fase-4.git
cd tech-challenge-fase-4
uv python install 3.12
uv sync --locked
```

O código de observabilidade precisa estar presente na branch utilizada (enquanto o PR não for integrado, usar `feat/operational-observability`). Coloque `application_train.csv` em `data/raw/`, conforme a seção [Dataset](#dataset), e prepare os artefatos locais:

```bash
uv run python -m src.pipelines.prepare_data
uv run python -m src.training.train
```

O arquivo `data/raw/application_train.csv`, os Parquet processados e o modelo são locais e não são disponibilizados automaticamente pelo clone.

**2. Gerar o arquivo de métricas**

```bash
uv run python -m scripts.run_monitored_drift
```

Esse comando valida os dados reais, avalia o cenário de Data Drift simulado, registra logs e grava `reports/operational_metrics.prom`. É esperado ver `307511` registros aprovados se a base e as etapas anteriores corresponderem à execução usada no projeto.

**3. Configurar a senha local do Grafana**

No Git Bash (Windows) ou em Bash (macOS/Linux):

```bash
read -rs -p "Senha local do Grafana: " GRAFANA_ADMIN_PASSWORD
echo
export GRAFANA_ADMIN_PASSWORD
```

No PowerShell, uma alternativa sem exibir a senha digitada:

```powershell
$senhaSegura = Read-Host "Senha local do Grafana" -AsSecureString
$env:GRAFANA_ADMIN_PASSWORD = [System.Net.NetworkCredential]::new("admin", $senhaSegura).Password
```

A senha é exigida na inicialização do Compose, **não deve ser escrita no README, versionada ou compartilhada no GitHub**. O usuário inicial do Grafana é `admin`. Uma instalação que já tenha o volume do Grafana inicializado mantém a senha armazenada mesmo que a variável mude posteriormente.

**4. Iniciar os serviços**

```bash
docker compose -f compose.observability.yaml config --quiet
docker compose -f compose.observability.yaml up -d
docker compose -f compose.observability.yaml ps
```

O Compose deve exibir `node-exporter`, `prometheus` e `grafana` em execução. Se a imagem ainda não estiver disponível, o Docker a baixará na primeira inicialização.

**5. Acessar as interfaces**

| Serviço | Endereço local | O que verificar |
|---|---|---|
| Node Exporter | http://localhost:9100/metrics | Métricas com prefixo `credit_` |
| Prometheus | http://localhost:9090/targets | Target `credit_scoring` em `UP` |
| Alertas | http://localhost:9090/alerts | Regras e estados dos alertas |
| Grafana | http://localhost:3000 | Dashboard `Credit Scoring \| Observabilidade Operacional` |

O Grafana provisiona o datasource `Prometheus` (UID `prometheus`) e o dashboard a partir dos arquivos em `infra/observability/grafana/`. **Os três painéis são instalados automaticamente**; não é necessário recriá-los pela interface. As portas estão vinculadas ao `127.0.0.1`, de modo que não são expostas diretamente na rede local.

### Dashboard do Grafana

O dashboard versionado em `infra/observability/grafana/dashboards/credit-scoring-observability.json` contém:

| Painel | Consulta | Interpretação |
|---|---|---|
| Data Drift por variável (PSI) | `credit_data_drift_psi` | Valores mais recentes por coluna, com vermelho a partir do PSI 0,20 |
| Tempo de execução dos pipelines | `credit_pipeline_duration_seconds_sum` | Duração, em segundos, de cada etapa na execução exportada |
| Status dos pipelines | `credit_pipeline_runs_total` | Etapas e status da execução exportada; não é total histórico |

Os painéis utilizam consultas instantâneas. O PSI exibido é do **cenário simulado**; o cenário original tem seus valores disponíveis nos relatórios Evidently, e não nesse painel. As configurações de visualização e as consultas estão versionadas em JSON, portanto as mudanças duráveis devem ser feitas no arquivo e reenviadas ao GitHub.

### Regras de alerta

O Prometheus avalia `infra/observability/prometheus/alerts.yml` automaticamente:

| Regra | Expressão PromQL | Duração | Significado |
|---|---|---|---|
| `CreditScoringDataDrift` | `credit_data_drift_psi >= 0.20` | 30 s | Dispara uma instância por variável cujo PSI ultrapassou o limite |
| `CreditScoringExporterDown` | `up{job="credit_scoring"} == 0` | 1 min | Detecta indisponibilidade do endpoint de coleta |

O primeiro alerta foi demonstrado com duas instâncias em **FIRING**: `AMT_INCOME_TOTAL` (PSI aproximadamente `0,6733`) e `AMT_CREDIT` (`0,4521`). Na mesma demonstração, o alerta de indisponibilidade permaneceu **INACTIVE**.

**Alerta em FIRING não significa notificação enviada.** Não há Alertmanager com canais de entrega configurados, nem integração automática com e-mail ou Microsoft Teams. As regras atuam no Prometheus e ficam visíveis em `/alerts`.

Verificar sintaxe do arquivo de alertas dentro do contêiner:

```bash
# Linux / macOS:
docker compose -f compose.observability.yaml exec -T prometheus promtool check rules /etc/prometheus/alerts.yml
```

No **Git Bash do Windows**, use `MSYS_NO_PATHCONV=1` para impedir que `/etc/prometheus/alerts.yml` seja convertido em um caminho do Windows:

```bash
MSYS_NO_PATHCONV=1 docker compose -f compose.observability.yaml exec -T prometheus promtool check rules /etc/prometheus/alerts.yml
```

### Operação e resolução de problemas

Verificar saúde e logs dos serviços:

```bash
docker compose -f compose.observability.yaml ps
docker compose -f compose.observability.yaml logs --tail=50
```

Verificar a saída do Textfile Collector no Git Bash / Linux / macOS:

```bash
curl -s http://localhost:9100/metrics | grep '^credit_'
curl -s http://localhost:9100/metrics | grep 'node_textfile'
```

Se o target estiver `UP`, mas não houver métricas `credit_`, confirme a existência de `reports/operational_metrics.prom` e execute novamente `uv run python -m scripts.run_monitored_drift`. O diretório `reports/` é montado como somente leitura pelo Node Exporter.

Para encerrar os contêineres sem perder os volumes persistentes:

```bash
docker compose -f compose.observability.yaml down
```

**Não use `down -v`** sem decidir conscientemente descartar os dados locais do Prometheus e do Grafana, pois esse comando remove os volumes da stack.

Caso a senha local do Grafana seja esquecida, ela pode ser redefinida dentro do contêiner com `grafana cli admin reset-admin-password`; redefinir uma variável de ambiente não altera automaticamente a senha já armazenada no volume.

Portas ocupadas (`3000`, `9090` ou `9100`) exigem liberar a porta ou alterar somente o mapeamento externo no Compose. Os endereços internos `prometheus:9090` e `node-exporter:9100` devem permanecer como estão para garantir a comunicação entre os contêineres.

### Limitações da observabilidade atual

1. **Pipeline batch:** o Python executa e termina; não há serviço de inferência contínua, agendamento ou job automático.
2. **Métricas instantâneas:** `prometheus_client` reinicia os Counters e Histograms em cada execução. O `.prom` representa a execução mais recente e substitui os valores anteriores. O Prometheus guarda amostras das coletas, mas consultar `credit_pipeline_runs_total` não representa um contador acumulado entre execuções; não se deve usar `rate()` ou `increase()` nessa métrica como contagem confiável de jobs.
3. **Dados potencialmente desatualizados:** o Textfile Collector continua expondo o último `.prom` mesmo sem nova execução Python. Assim, um alerta de PSI pode permanecer em FIRING indefinidamente. Para uso real, é necessário adicionar métrica de horário da última execução e regra de frescor/ausência de dados.
4. **Ausência de notificação:** os alertas são avaliados pelo Prometheus, mas ainda não têm roteamento externo para Teams ou e-mail.
5. **Dados simulados:** o drift observado foi provocado artificialmente. O dashboard não monitora novos clientes de produção nem valida a qualidade preditiva em dados novos rotulados.
6. **Escopo operacional:** o pipeline registra resultados de carga, validação e drift; métricas de API de inferência, latência por requisição, tráfego e monitoramento de desempenho do modelo em produção ainda não foram instrumentadas.
7. **Segurança local:** a configuração foi desenhada para demonstração em notebooks de desenvolvimento, não para implantação pública. A exposição externa exigiria autenticação, TLS, gestão de credenciais, segregação de acesso e políticas de retenção.

## Governança, privacidade e evolução do projeto

A instrumentação evita incluir dados individuais nos logs estruturados de validação. O dataset Home Credit e seus artefatos brutos/processados permanecem locais. A verificação exploratória de ROC-AUC por gênero e faixa etária ajuda a identificar questões para investigação, mas não comprova equidade, ausência de viés nem conformidade com a LGPD.

**Implementado:** contratos Pandera para oito colunas, baseline XGBoost/MLflow, Evidently/PSI para duas variáveis, análise de impacto no score, logs estruturados, métricas, dashboard e regras de alerta.

**Próximos trabalhos recomendados:**

- Criar métrica `last_success_timestamp` e alertas de ausência de atualização para o pipeline batch.
- Definir uma estratégia de contadores persistentes ou de métricas por execução, e testar múltiplos runs.
- Automatizar execução periódica e, se necessário, usar um mecanismo de entrega de métricas para jobs curtos (por exemplo, Pushgateway com regras de ciclo de vida adequadas).
- Configurar Alertmanager e canais de notificação, caso o escopo exija alertas enviados.
- Registrar políticas de minimização, finalidade, bases legais, controle de acesso e retenção sob LGPD.
- Aprofundar métricas de fairness, taxas de erro por grupo e análise da representatividade da amostra.
- Documentar hipóteses causais e possíveis confundidores; **o experimento de drift não demonstra causalidade**.
- Avaliar degradação efetiva de desempenho com rótulos independentes e dados de períodos posteriores.
- Preparar o vídeo demonstrativo no formato STAR, destacando cenário, ações, evidências e limitações.

## Validação final

Para reproduzir os principais testes e verificações:

```bash
uv sync --locked
uv run pytest -v
uv run ruff check .
uv run ruff format . --check
uv run python scripts/check_notebooks.py
uv run pre-commit run --all-files

docker compose -f compose.observability.yaml config --quiet
docker compose -f compose.observability.yaml ps
```

Na execução registrada em 08/11/2026, **50 testes passaram** e os hooks do pre-commit foram aprovados. Os serviços Docker e a exportação de métricas foram validados separadamente com a base real. O número de testes pode variar com novos commits.

Antes de abrir um PR para `development`, verifique também os arquivos adicionados e modificados:

```bash
git status --short
git diff --check
```

**Dica:** arquivos ainda não rastreados pelo Git não aparecem em `git diff`; inclua-os com `git add` antes de validar o conteúdo staged e criar o commit.

## Governança e LGPD

### Escopo

O cenário simula uma fintech que utiliza um modelo para apoiar nas decisões de crédito. No contexto acadêmico, o dataset é o Home Credit Defaault Risk (Kaggle), público e sem identificação direta de pessoas reais:
`SK_ID_CURR` é um código sem vínculo com titulares identificáveis. O plano abaixo detalha como a esteira trataria dados reais.

### Inventário de dados pessoais

| Dado | Classificação | Uso no projeto | Tratamento |
|---|---|---|---|
| `SK_ID_CURR` | Identificador | Unicidade e junção | Não é feature; não aparece em logs nem métricas; em produção, seria pseudonimizado (hash com chave secreta) |
| `CODE_GENDER` | Atributo protegido (risco de discriminação) | Somente auditoria de viés | Excluído das features do modelo (`MODEL_FEATURES`) |
| `DAYS_BIRTH` → `AGE_YEARS` | Atributo protegido / quase-identificador | Feature do modelo e auditoria | Mantido por relevância para risco de crédito; monitorado por faixa etária (ver "Mitigação de vieses") |
| Renda, crédito, anuidade, emprego | Dados financeiros pessoais | Features | Apenas as colunas listadas em `RAW_COLUMNS` são carregadas |
| `EXT_SOURCE_1/2/3` | Scores de bureaus externos | Features | Origem de terceiros; em produção, exige contrato de compartilhamento |

Gênero e idade não são dados sensíveis de acordo com a LGPD (**art. 5, II**), contudo o princípio da não discriminação (**art. 6º, iX**) exige monitorar seu efeito nas decisões.

### Finalidade e base legal

- ** Art. 7º, X - proteção do crédito:** base principal para analisar o risco de inadimplência;
- **Art. 7º, V - execução de contrato / procedimentos:** a análise ocorre a pedido do cliente que solicita o crédito;
- Os dados são utilizados **somente** para avaliar o risco de crédito; outros usos (ex.: marketing) exigiriam nova base legal.

### Princípios aplicados (art. 6º)

- **Minimização:** a esteira carrega uma lista fechada de colunas (`RAW_COLUMNS`), e não as 122 colunas do dataset original;
- **Finalidade:** o gênero é lido apenas para auditoria e não influencia o score;
- **Segurança (art. 6º):** dados brutos, processados e artefatos gerados ficam fora do GitHub;
- **Transparência:** regras de validação, features e métricas documentadas neste README e no model card (`docs/model_card.md`).

### Direitos do titular

- **Art. 18:** acesso, correção e eliminção dos dados, via canal do encarregado.
- **Art. 20 - decisões automatizadas:** o cliente pode pedir revisão da decisão e informações sobre os critérios usados. O modelo atual não gera explicações individuais. Em produção, cada decisão retornaria os principais fatores e as recusas teriam revisão humana.

### Plano de retenção (art. 16)

| Dado | Prazo | Justificativa |
|---|---|---|
| Dados brutos e processados do projeto | Eliminados ao fim do projeto | A finalidade acadêmica se encerra |
| Em produção: informações negativas | Até 5 anos | CDC, art. 43, §1º |
| Em produção: histórico de adimplemento | Até 15 anos | Lei 12.414/2011 (Cadastro Positivo) |
| Métricas no Prometheus | 7 dias | `--storage.tsdb.retention.time=7d` em `compose.observability.yaml` |
| Logs estruturados | Curto prazo; apenas dados agregados | Não contêm dados pessoais |

### Papeis e resposta a incidentes

- **Controlador:** a fintech, que decide sobre concessão de crédito;
- **Operadores:** fornecedores de infraestrutura e bureus de crédito;
- **Encarregado (DPO, art. 41):** canal para os titulares e também para a ANPD
- **Registro das operações (art. 37)** e **Relatório de Impacto (RIPD, art. 38)** revisados a cada retreino de modelo;
- **Incidentes:** comunicação à ANPD e aos titulares envolvidos quando houver risco relevante.

### Mitigação de vieses

- O gênero é **excluído** das features e usado somente para medir o comportamento do modelo por grupo.
- O treinamento registra no MLflow o ROC-AUC por gênero e faixa etária. Feminino (0,7671) e masculino (0,7515) ficam próximos; maior diferença de **60 anos ou mais (0,7290)**.
- **Limitação:** AUC por grupo não basta para afirmar equidade. Variáveis como renda e tipo de ocupação podem funcionar como *proxies* de atributos protegidos.


> **Nota:** dados, artefatos do modelo e relatórios gerados devem ser avaliados antes de serem enviados ao repositório. Não versione dados pessoais ou arquivos de produção sem necessidade e autorização.
