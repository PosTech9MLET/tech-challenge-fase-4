# Arquitetura

~~~mermaid
flowchart LR
    A[data/raw] --> B[src/data] --> C[src/features] --> D[src/training]
    D --> E[(MLflow)] --> F[src/api]
~~~
