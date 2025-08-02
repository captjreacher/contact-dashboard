import React, { useState, useEffect } from 'react';
import { getWebhooks, addWebhook, updateWebhook, deleteWebhook } from '../services/api';
import AddEditWebhookModal, { Webhook } from '../components/AddEditWebhookModal';

const WebhookSettings: React.FC = () => {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingWebhook, setEditingWebhook] = useState<Webhook | null>(null);

  const fetchWebhooks = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await getWebhooks();
      setWebhooks(response.webhooks);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch webhooks.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWebhooks();
  }, []);

  const handleSave = async (webhook: Omit<Webhook, 'webhook_id'> | Webhook) => {
    try {
      if ('webhook_id' in webhook) {
        await updateWebhook(webhook);
      } else {
        await addWebhook(webhook);
      }
      fetchWebhooks();
      setIsModalOpen(false);
      setEditingWebhook(null);
    } catch (err: any) {
      setError(err.message || 'Failed to save webhook.');
    }
  };

  const handleDelete = async (webhookId: string) => {
    if (window.confirm('Are you sure you want to delete this webhook?')) {
      try {
        await deleteWebhook(webhookId);
        fetchWebhooks();
      } catch (err: any) {
        setError(err.message || 'Failed to delete webhook.');
      }
    }
  };

  if (loading) return <p>Loading webhooks...</p>;

  return (
    <div>
      <h2>Webhook Settings</h2>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button onClick={() => { setEditingWebhook(null); setIsModalOpen(true); }}>Add Webhook</button>
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>URL</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {webhooks.map(webhook => (
            <tr key={webhook.webhook_id}>
              <td>{webhook.name}</td>
              <td>{webhook.url}</td>
              <td>
                <button onClick={() => { setEditingWebhook(webhook); setIsModalOpen(true); }}>Edit</button>
                <button onClick={() => handleDelete(webhook.webhook_id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {isModalOpen && (
        <AddEditWebhookModal
          webhook={editingWebhook}
          onSave={handleSave}
          onClose={() => { setIsModalOpen(false); setEditingWebhook(null); }}
        />
      )}
    </div>
  );
};

export default WebhookSettings;
