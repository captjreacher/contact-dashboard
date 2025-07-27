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
