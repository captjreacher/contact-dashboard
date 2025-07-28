# Contact Dashboard

This is a Flask-based web application for managing contacts and marketing campaigns.

## Prerequisites

- Docker
- Docker Compose

## Getting Started

1. **Build and run the application:**

   ```bash
   docker-compose up --build
   ```

2. **Access the application:**

   Open your web browser and navigate to [http://localhost:5000](http://localhost:5000).

## API Endpoints

The application provides a RESTful API for managing contacts, campaigns, and other resources. The API endpoints are available under the `/api` prefix.

### Contacts

- `GET /api/contacts`: Retrieve a list of contacts.
- `GET /api/contacts/<contact_id>`: Retrieve a single contact.
- `POST /api/contacts`: Create a new contact.
- `PUT /api/contacts/<contact_id>`: Update an existing contact.
- `DELETE /api/contacts/<contact_id>`: Delete a contact.

### Campaigns

- `GET /api/campaigns`: Retrieve a list of campaigns.
- `GET /api/campaigns/<campaign_id>`: Retrieve a single campaign.
- `POST /api/campaigns`: Create a new campaign.
- `POST /api/campaigns/<campaign_id>/start`: Start a campaign.

### Upload

- `POST /api/upload`: Upload a spreadsheet of contacts.

### Webhooks

- `POST /api/webhooks/campaign-results`: Receive campaign results from Make.com.

## Database

The application uses a SQLite database to store its data. The database file is located at `/tmp/app.db` within the container and is mounted to the host filesystem to ensure data persistence.


### Webhook API Key Authentication

To secure the webhook endpoints (`/api/webhooks/verification-results` and `/api/webhooks/campaign-results`), API key authentication has been implemented. When sending requests to these endpoints, you must include an `X-API-Key` header with a valid API key. The API key is now read from the `WEBHOOK_API_KEY` environment variable.

**Generating a Secure API Key:**
You can generate a secure API key using Python's `secrets` module. Open a Python interpreter or run a Python script with the following code:

```python
import secrets
print(secrets.token_urlsafe(32))
```

This will output a strong, URL-safe API key (e.g., `3eCx0zo7-pQsLTE7VYDTfZKALTD1dTLhuEEor4bBnRM`).

**Setting the API Key Environment Variable:**
When running the application with Docker Compose, you can set the `WEBHOOK_API_KEY` environment variable in your `.env` file or directly in your shell before running `docker-compose up`.

Example `.env` file:
```
WEBHOOK_API_KEY=your_generated_api_key_here
```

**Example Request with API Key:**

```
POST /api/webhooks/campaign-results
Content-Type: application/json
X-API-Key: your_generated_api_key_here

{
    "some_data": "value"
}
```

**Note:** Replace `your_generated_api_key_here` with the actual API key you generated. For security, it is recommended to store your API key securely (e.g., in environment variables) and not hardcode it in your Make.com scenarios.

