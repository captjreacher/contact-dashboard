import React, { useState, useEffect } from 'react';
import AddEditWebhookModal, { Webhook } from '../components/AddEditWebhookModal';
import { Button } from './ui/button';

export default function WebhookSettings() {
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [editingWebhook, setEditingWebhook] = useState<Webhook | undefined>(undefined);

  // Load webhooks on mount
  useEffect(() => {
    fetch('/api/settings/webhooks')
      .then(res => res.json())
      .then(data => {
        console.log('Fetched webhooks:', data.webhooks); // Add this line to see the data in browser console
        if (data.success && Array.isArray(data.webhooks)) {
          setWebhooks(data.webhooks);
        }
      })
      .catch(console.error);
  }, []);
  ;

  // Save webhook (new or update)
  const handleSaveWebhook = async (webhookData: Omit<Webhook, 'id'> | Webhook) => {
    try {
      const method = 'id' in webhookData ? 'PUT' : 'POST';
      const url = 'id' in webhookData
        ? `/api/settings/webhooks/${webhookData.id}`
        : '/api/settings/webhooks';

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(webhookData),
      });

      if (!response.ok) throw new Error('Failed to save webhook');
      const savedWebhook = await response.json();

      setWebhooks(prev => {
        if ('id' in savedWebhook) {
          // Update existing webhook in list
          return prev.map(w => (w.id === savedWebhook.id ? savedWebhook : w));
        } else if (savedWebhook.webhook?.id) {
          // Sometimes backend wraps in "webhook" object
          const newWebhook = savedWebhook.webhook;
          return prev.some(w => w.id === newWebhook.id)
            ? prev.map(w => (w.id === newWebhook.id ? newWebhook : w))
            : [...prev, newWebhook];
        }
        return prev;
      });

      setEditingWebhook(undefined);
    } catch (error: any) {
      alert('Error saving webhook: ' + error.message);
    }
  };

  return (
    <div>
      <h1>Webhook Settings</h1>

      {/* Add new webhook */}
      <AddEditWebhookModal onSave={handleSaveWebhook}>
        <Button>Add New Webhook</Button>
      </AddEditWebhookModal>

      {/* List existing webhooks */}
      <ul>
        {webhooks.map(webhook => (
          <li key={webhook.id} className="flex justify-between items-center py-2">
            <div>
              <strong>{webhook.url}</strong> — Events: {webhook.events.join(', ')}
            </div>
            <Button variant="outline" size="sm" onClick={() => setEditingWebhook(webhook)}>
              Edit
            </Button>
          </li>
        ))}
      </ul>

      {/* Edit webhook modal */}
      {editingWebhook && (
        <AddEditWebhookModal webhook={editingWebhook} onSave={handleSaveWebhook}>
          {/* Invisible trigger because modal is controlled */}
          <span />
        </AddEditWebhookModal>
      )}
    </div>
  );
}
