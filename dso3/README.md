# DSO3 - Intelligent Recommendation Engine

DSO3 is a FastAPI-based microservice designed to match **Products** with the most relevant **Delegates** using state-of-the-art Natural Language Processing (NLP).

## 🏗️ Architecture

The project follows a modular and tiered architecture to ensure maintainability and scalability:

- **`main.py`**: The application entry point that aggregates all documentation and routes.
- **`models/`**: SQLAlchemy models defining the database schema (SQLite).
  - `Product`: Stores product details and their computed embeddings.
  - `Delegate`: Stores delegate profiles (expertise and interests).
  - `Recommendation`: Links products to delegates with a calculated similarity score.
- **`routes/`**: API controllers that handle incoming HTTP requests.
  - `/products`: Handles product creation and triggers the recommendation logic.
  - `/delegates`: Manages delegate profiles.
  - `/recommend`: Specific endpoints for retrieving pre-calculated recommendations.
- **`schemas/`**: Pydantic models for data validation and serialization.
- **`services/`**: Core business logic.
  - `recommender.py`: The matching engine.
  - `embedding.py`: Wrapper for `sentence-transformers` to generate vectors from text.
- **`database.py`**: Configuration for SQLAlchemy and session management.

## 🧠 Core Logic: Embedding-Based Matching

DSO3 doesn't just match keywords; it understands the **semantic context** of expertise and interests.

1.  **Text Representation**: When a product or delegate is created, a descriptive text is formed from their attributes (e.g., Category + Description).
2.  **Vectorization**: This text is passed through the `all-MiniLM-L6-v2` transformer model to create a high-dimensional vector.
3.  **Similarity Calculation**: We use **Cosine Similarity** to compare the Product vector against all Delegate vectors.
4.  **Ranking**: The system filters out low-scoring matches (threshold < 0.35) and returns the top 5 most relevant delegates.

## 🚀 Execution

To ensure all internal paths are resolved correctly, always run the application from the repository root.

### Prerequisites
Ensure your virtual environment is active and dependencies are installed:
```powershell
.\venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy sentence-transformers scikit-learn
```

### Starting the Server
Navigate to the repository root and run:
```powershell
cd ESPRIT-PI-4DS10-25-26-Co_Win
uvicorn dso3.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can explore the interactive documentation at `/docs`.

---
*Note: This component is part of the Co-Win project ecosystem.*
