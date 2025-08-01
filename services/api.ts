import { Webhook } from '../components/AddEditWebhookModal';

// In a real app, this would come from environment variables
const astraUrl = `https://a4a5c451-23d1-432d-8356-d4f107f91574-us-east-2.apps.astra.datastax.com/api/rest/v2/keyspaces/leads_datastore`;

const getApiHeaders = () => ({
  'Content-Type': 'application/json',
  // Replace with your actual authentication token
  'X-Cassandra-Token': `AstraCS:your-astra-db-token-goes-here`
});

type NewWebhookData = Omit<Webhook, 'id'>;

export const webhookService = {
  /**
   * Creates a new webhook.
   * @param webhookData - The webhook data, including the stringified headers.
   */
  createWebhook: async (webhookData: NewWebhookData): Promise<Webhook> => {
    const response = await fetch(`${astraUrl}/webhooks`, {
      method: 'POST',
      headers: getApiHeaders(),
      body: JSON.stringify(webhookData)
    });
    if (!response.ok) {
      const errorBody = await response.text();
      console.error('Failed to create webhook:', errorBody);
      throw new Error('Failed to create webhook');
    }
    return response.json();
  },

  /**
   * Updates an existing webhook.
   * @param webhook - The full webhook object, including its ID.
   */
  updateWebhook: async (webhook: Webhook): Promise<Webhook> => {
    const { id, ...webhookData } = webhook;
    const response = await fetch(`${astraUrl}/webhooks/${id}`, {
      method: 'PUT', // or PATCH
      headers: getApiHeaders(),
      body: JSON.stringify(webhookData)
    });
    if (!response.ok) {
      const errorBody = await response.text();
      console.error('Failed to update webhook:', errorBody);
      throw new Error('Failed to update webhook');
    }
    return response.json();
  }
};

/**
 * Example of how the onSave function would be implemented in a parent component.
 * This demonstrates how to use the webhookService.
 */
const handleSaveWebhook = async (webhookData: NewWebhookData | Webhook) => {
    try {
        if ('id' in webhookData) {
            await webhookService.updateWebhook(webhookData);
            // Add success notification (e.g., toast)
            console.log('Webhook updated successfully!');
        } else {
            await webhookService.createWebhook(webhookData);
            // Add success notification
            console.log('Webhook created successfully!');
        }
        // Optionally, refresh the list of webhooks
    } catch (error) {
        // Add error notification
        console.error('Failed to save webhook:', error);
    }
};

/**
 * Example of how to use the modal in your application.
 * You would place this in a component that manages webhooks.
 */
const WebhookManagementComponent = () => {
    const existingWebhook: Webhook = {
        id: 'wh_123',
        url: 'https://example.com/hook',
        events: ['contact.created'],
        headers: '{"X-API-Key": "my-secret-key"}'
    };

    return (
        <div>
            {/* Example for creating a new webhook */}
            <AddEditWebhookModal onSave={handleSaveWebhook}>
                <Button>Add Webhook</Button>
            </AddEditWebhookModal>

            {/* Example for editing an existing webhook */}
            <AddEditWebhookModal webhook={existingWebhook} onSave={handleSaveWebhook}>
                <Button variant="outline">Edit Webhook</Button>
            </AddEditWebhookModal>
        </div>
    );
};
