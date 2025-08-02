import React, { useState, useEffect } from 'react';

export interface Webhook {
  webhook_id: string;
  name: string;
  url: string;
  header_name?: string;
  header_value?: string;
}

interface AddEditWebhookModalProps {
  webhook?: Webhook | null;
  onSave: (webhook: Omit<Webhook, 'webhook_id'> | Webhook) => void;
  onClose: () => void;
}

const AddEditWebhookModal: React.FC<AddEditWebhookModalProps> = ({ webhook, onSave, onClose }) => {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [headerName, setHeaderName] = useState('');
  const [headerValue, setHeaderValue] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    if (webhook) {
      setName(webhook.name);
      setUrl(webhook.url);
      setHeaderName(webhook.header_name || '');
      setHeaderValue(webhook.header_value || '');
    } else {
      setName('');
      setUrl('');
      setHeaderName('');
      setHeaderValue('');
    }
  }, [webhook]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!name || !url) {
      setError('Name and URL are required.');
      return;
    }

    const webhookData: any = {
      name,
      url,
      header_name: headerName,
      header_value: headerValue,
      webhook_type: 'verification', // Hardcoding for now
      is_active: true,
    };

    if (webhook) {
      webhookData.webhook_id = webhook.webhook_id;
    }

    onSave(webhookData);
  };

  return (
    <div className="modal">
      <div className="modal-content">
        <h2>{webhook ? 'Edit' : 'Add'} Webhook</h2>
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <div>
            <label>Name</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div>
            <label>URL</label>
            <input type="text" value={url} onChange={(e) => setUrl(e.target.value)} />
          </div>
          <div>
            <label>Header Name (Optional)</label>
            <input type="text" value={headerName} onChange={(e) => setHeaderName(e.target.value)} />
          </div>
          <div>
            <label>Header Value (Optional)</label>
            <input type="text" value={headerValue} onChange={(e) => setHeaderValue(e.target.value)} />
          </div>
          <button type="submit">Save</button>
          <button type="button" onClick={onClose}>Cancel</button>
        </form>
      </div>
    </div>
  );
};

export default AddEditWebhookModal;
