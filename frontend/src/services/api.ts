const API_BASE_URL = 'http://localhost:5000/api';

// Helper function to handle API responses
const handleResponse = async (response: Response) => {
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Something went wrong');
  }
  return response.json();
};

// --- Contact API ---

export const getContacts = async () => {
  const response = await fetch(`${API_BASE_URL}/contacts`);
  return handleResponse(response);
};

export const addContact = async (contact: { first_name: string; last_name: string; email_address: string }) => {
  const response = await fetch(`${API_BASE_URL}/contacts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(contact),
  });
  return handleResponse(response);
};

// --- Webhook API ---

export const getWebhooks = async () => {
  const response = await fetch(`${API_BASE_URL}/settings/webhooks`);
  return handleResponse(response);
};

export const addWebhook = async (webhook: any) => {
  const response = await fetch(`${API_BASE_URL}/settings/webhooks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(webhook),
  });
  return handleResponse(response);
};

export const updateWebhook = async (webhook: any) => {
  const response = await fetch(`${API_BASE_URL}/settings/webhooks/${webhook.webhook_id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(webhook),
  });
  return handleResponse(response);
};

export const deleteWebhook = async (webhookId: string) => {
  const response = await fetch(`${API_BASE_URL}/settings/webhooks/${webhookId}`, {
    method: 'DELETE',
  });
  return handleResponse(response);
};


// --- Verification API ---

export const createVerificationJob = async (contactIds: number[]) => {
  const response = await fetch(`${API_BASE_URL}/verification/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ contact_ids: contactIds }),
  });
  return handleResponse(response);
};

export const runVerificationJob = async (jobId: string) => {
    const response = await fetch(`${API_BASE_URL}/verification/jobs/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId }),
    });
    return handleResponse(response);
  };
