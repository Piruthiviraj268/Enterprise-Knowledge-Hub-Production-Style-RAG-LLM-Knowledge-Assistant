# Atlas Knowledge Platform — Architecture Notes

The platform uses a browser client, a Python HTTP API, SQLite persistence and a local retrieval index. Documents are parsed into chunks before indexing. Retrieval combines TF-IDF similarity with lexical overlap so exact business terms remain discoverable.

The answer layer can run in local extractive mode or use an optional hosted language model. Hosted generation receives only the retrieved context and recent conversation messages. The citation validator rejects generated answers that contain invalid citations or unsupported sentence-level claims.

For production deployment, the recommended next step is replacing the local SQLite store with PostgreSQL and moving the retrieval index to a vector database. Authentication, encrypted object storage, audit logging and background ingestion should also be added before handling regulated data.
