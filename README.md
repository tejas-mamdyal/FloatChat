# FloatChat

FloatChat is an AI-powered conversational interface for ARGO oceanographic data. It allows researchers and scientists to easily discover, filter, and analyze oceanographic profiles through a conversational search interface powered by Large Language Models.

## Features
* **ARGO Data Discovery:** Search through millions of ARGO profiles.
* **Spatial/Temporal Filtering:** Pinpoint data by geographic bounding boxes, radiuses, and timeframes.
* **Scientific Aggregation:** Compute averages, minimums, maximums, and statistics on variables like temperature, salinity, and pressure.
* **Conversational Querying:** Ask natural language questions like "What was the average temperature near Mumbai in January 2025?".
* **DuckDB Analytics:** Fast, out-of-core analytics powered by DuckDB over Parquet datasets.
* **PostgreSQL/PostGIS Metadata:** Relational mapping and spatial indexing of ARGO files and profiles.
* **Future/Optional pgvector:** Prepared for advanced semantic metadata retrieval.

## Architecture
```text
                         ┌──────────────┐
                         │   Frontend   │
                         └──────┬───────┘
                                ↓
                         ┌──────────────┐
                         │ FastAPI v2   │
                         └──────┬───────┘
                                ↓
                         ┌──────────────┐
                         │ QueryPlanner │ (Llama3-8b via Groq)
                         └──────┬───────┘
                                ↓
              ┌─────────────────┼─────────────────┐
              ↓                 ↓                 ↓
       PostgreSQL/PostGIS   PostgreSQL/       DuckDB
       Metadata/Spatial      pgvector      (Scientific Ops)
              │                 │                 │
              └─────────────────┼─────────────────┘
                                ↓
                         Result Builder
                                ↓
                              Groq
                                ↓
                            Response
```

## Tech Stack
* **Frontend:** React, Vite (Assumed based on environment)
* **Backend:** Python, FastAPI, Uvicorn, Pydantic
* **Analytics Engine:** DuckDB, Pandas, fastparquet
* **Database:** PostgreSQL, PostGIS, pgvector (via Docker)
* **LLM Integration:** Groq (llama3-8b-8192)

## Project Structure
```text
FloatChat/
├── backend/
│   ├── database/       # DB connection and schemas
│   ├── models/         # Pydantic data models (e.g., QueryPlan)
│   ├── routers/        # FastAPI endpoints
│   ├── services/       # Core logic (DuckDB, Planner, RAG)
│   ├── scripts/        # Data ingestion and backfill tools
│   └── tests/          # Unit tests
├── frontend/
│   ├── src/            # React source code
│   ├── public/         # Static assets
│   └── package.json    # Frontend dependencies
├── docker-compose.db.yml # Local database infrastructure
├── Dockerfile.db       # Custom PostGIS/pgvector image
└── README.md
```

## Setup

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-org/FloatChat.git
   cd FloatChat
   ```

2. **Backend Python Environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Create configuration files based on the provided examples:
   - Copy `backend/config.example.yaml` to `backend/config.yaml` and configure paths and keys.
   - Set the `GROQ_API_KEY` environment variable in your terminal.
   *(Never commit real secrets or API keys to GitHub.)*

4. **Configure PostgreSQL/PostGIS/pgvector**
   Ensure Docker is installed, then launch the database:
   ```bash
   docker-compose -f docker-compose.db.yml up -d
   ```
   *(Note: The database must be running for spatial features to work.)*

5. **Run Backend**
   ```bash
   cd backend
   python main.py
   # Runs on http://localhost:8000
   ```

6. **Run Frontend**
   ```bash
   cd frontend
   npm install
   npm run dev
   # Runs on local Vite port
   ```

## Environment Variables
The application relies on secure environment variable injection to prevent hardcoded credentials. Ensure you review:
- `backend/config.example.yaml`
- `frontend/.env.example` (if applicable)

## ARGO Data
Raw NetCDF files and compiled Parquet datasets are massive and are **NOT** included in this repository. 
You must download Argo data into the configured `downloads` folder and run the provided pipeline scripts (`backend/scripts/nc_to_parquet.py` and `backend/scripts/backfill_argo_metadata.py`) to hydrate the DuckDB and PostgreSQL engines.

## Query Examples
- "Find floats in the Arabian Sea."
- "What is the average temperature during January 2025?"
- "Find profiles within 200 km of Mumbai."
- "Show salinity observations for a given period."

## Architecture Limitations
- **PostGIS Integration:** The spatial filtering capabilities natively require the configured PostgreSQL environment. If the database cannot be reached, the API will safely return a 503 error rather than crashing.

## Development
Run the backend test suite:
```bash
cd backend
python -m unittest discover tests
```

## Security
**Do not** commit `.env`, `config.yaml`, or any file containing passwords, API keys, or database credentials. Ensure your environment variables are configured locally.

## License
License decision is pending. Please review with the project maintainers before distributing.
