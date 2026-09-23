# Diagrama de arquitectura

```mermaid
flowchart LR
    Client["Client / Frontend"] -- HTTP --> API["FastAPI API\napp/main.py"]
    API --> Endpoints["Asset Endpoints\napp/api/assets.py"]
    Endpoints --> Service["Asset Service\napp/services/assets_service.py"]
    Service --> CRUD["CRUD & Data Access\napp/crud.py"] & S3["S3 Client\napp/services/s3_client.py"]
    CRUD --> DB[("Database\napp/database.py")]
    S3 -- presigned url --> Client

This diagram illustrates the core structure of the service: the client consumes the API, the routing layer delegates requests to the business logic, and the service layer communicates with both the database and S3 storage.