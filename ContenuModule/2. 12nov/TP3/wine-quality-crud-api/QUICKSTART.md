# QUICKSTART.md

# Quick Start Guide for Wine Quality CRUD API

This document provides a quick start guide for using the Wine Quality CRUD API. Follow the instructions below to set up and interact with the API.

## Prerequisites

- Python 3.7 or higher
- FastAPI
- Uvicorn
- Required libraries listed in `requirements.txt`

## Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd wine-quality-crud-api
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables in the `.env` file:

   ```
   JWT_SECRET_KEY=<your_secret_key>
   DATABASE_URL=<your_database_url>
   ```

## Running the API

To start the FastAPI server, run the following command:

```
uvicorn src.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

## API Endpoints

### Authentication

- **Login**: `POST /auth/login`
  - Request body: `{ "username": "<your_username>", "password": "<your_password>" }`
  - Response: `{ "access_token": "<token>", "token_type": "bearer" }`

### Wine Management

- **Create Wine**: `POST /wines`
  - Request body: `{ "name": "<wine_name>", "type": "<wine_type>", "quality": <quality_score>, ... }`
  - Response: `{ "id": <wine_id>, "name": "<wine_name>", ... }`

- **Read Wine**: `GET /wines/{id}`
  - Response: `{ "id": <wine_id>, "name": "<wine_name>", ... }`

- **Update Wine**: `PUT /wines/{id}`
  - Request body: `{ "name": "<new_wine_name>", "type": "<new_wine_type>", "quality": <new_quality_score>, ... }`
  - Response: `{ "id": <wine_id>, "name": "<new_wine_name>", ... }`

- **Delete Wine**: `DELETE /wines/{id}`
  - Response: `{ "message": "Wine deleted successfully" }`

### Documentation

For more detailed information about the API, visit the interactive API documentation at `http://127.0.0.1:8000/docs`.

## Conclusion

You are now ready to use the Wine Quality CRUD API. For any issues or contributions, please refer to the project's GitHub repository.