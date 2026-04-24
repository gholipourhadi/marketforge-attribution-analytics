# Architecture

MarketForge separates ingestion, journey construction, measurement models, decision scenarios and delivery. `ingestion.py` owns the event contract and consent boundary. `journey_table` creates point-in-time paths ending at the first conversion. Attribution, Markov analysis, business metrics, experiments and budget allocation are independent services. FastAPI and Streamlit consume these services without duplicating analytical logic.

The sample CSV is loaded per request for portability. A production deployment should replace this with an immutable warehouse snapshot, versioned semantic layer, authentication, authorization, caching, tracing and scheduled materialization.

