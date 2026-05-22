# Wine Quality CRUD API

## Overview
This project implements a FastAPI application for managing a wine dataset. It provides a complete CRUD (Create, Read, Update, Delete) API for wine records, along with user authentication using JWT (JSON Web Tokens).

## Project Structure
```
wine-quality-crud-api
├── src
│   ├── main.py                # Entry point of the application
│   ├── config.py              # Configuration for JWT management
│   ├── auth.py                # Functions for managing JWT tokens
│   ├── dependencies.py         # Error handling for token verification
│   ├── models
│   │   ├── __init__.py        # Models package initializer
│   │   ├── user_models.py      # User model definitions
│   │   ├── token_models.py     # Token model definitions
│   │   └── wine_models.py      # Wine model definitions
│   ├── routers
│   │   ├── __init__.py        # Routers package initializer
│   │   ├── auth_router.py      # Authentication routes
│   │   └── wine_router.py      # CRUD operations for wine dataset
│   ├── services
│   │   ├── __init__.py        # Services package initializer
│   │   ├── auth_service.py     # User authentication logic
│   │   ├── wine_service.py     # Wine data management logic
│   │   └── model_persistence.py # Model persistence logic
│   └── database
│       ├── __init__.py        # Database package initializer
│       └── connection.py       # Database connection management
├── data
│   └── WineQT.csv             # Dataset of wines
├── models_storage
│   ├── wine_model.joblib      # Serialized wine prediction model
│   ├── model_metadata.json     # Metadata for the wine model
│   └── additional_data.csv     # Additional data related to wines
├── tests
│   ├── __init__.py            # Tests package initializer
│   ├── test_auth.py           # Unit tests for authentication
│   └── test_wine_routes.py     # Unit tests for wine routes
├── .env                        # Environment variables
├── .gitignore                  # Files to ignore in version control
├── requirements.txt            # Project dependencies
├── README.md                   # Project documentation
└── QUICKSTART.md               # Quick start guide for the API
```

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   cd wine-quality-crud-api
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables in the `.env` file:
   ```
   JWT_SECRET_KEY=<your_secret_key>
   DATABASE_URL=<your_database_url>
   ```

5. Run the application:
   ```
   uvicorn src.main:app --reload
   ```

## Usage
- Access the API documentation at `http://localhost:8000/docs`.
- Use the endpoints to manage wine records and authenticate users.

## Example Requests
- **Create a new wine record:**
  ```
  POST /wines
  {
      "name": "Chardonnay",
      "year": 2020,
      "quality": 8,
      ...
  }
  ```

- **Authenticate a user:**
  ```
  POST /auth/login
  {
      "username": "user",
      "password": "password"
  }
  ```

## License
This project is licensed under the MIT License.