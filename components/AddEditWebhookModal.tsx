import React, { useState, useEffect } from 'react';
import { Button } from './ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { HoverCard, HoverCardContent, HoverCardTrigger } from './ui/hover-card';
import { Info, PlusCircle, Trash2 } from 'lucide-react';

// --- Type Definitions ---
export interface Webhook {
  id: string;
  url: string;
  events: string[];
  headers: string; // Stored as a JSON string
}

export type Header = {
  key: string;
  value: string;
};

// --- Component Props ---
interface AddEditWebhookModalProps {
  webhook?: Webhook;
  onSave: (webhookData: Omit<Webhook, 'id'> | Webhook) => void;
  children: React.ReactNode; // To trigger the dialog
}

export default function AddEditWebhookModal({ webhook, onSave, children }: AddEditWebhookModalProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [url, setUrl] = useState('');
  const [events, setEvents] = useState('contact.created, contact.updated'); // Example events
  const [headers, setHeaders] = useState<Header[]>([{ key: '', value: '' }]);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (webhook && isOpen) {
      setUrl(webhook.url);
      setEvents(webhook.events.join(', '));
      if (webhook.headers) {
        try {
          const parsedHeaders = JSON.parse(webhook.headers);
          const headersArray = Object.entries(parsedHeaders).map(([key, value]) => ({ key, value: String(value) }));
          setHeaders(headersArray.length > 0 ? headersArray : [{ key: '', value: '' }]);
        } catch (error) {
          console.error('Failed to parse headers:', error);
          setHeaders([{ key: '', value: '' }]);
        }
      } else {
        setHeaders([{ key: '', value: '' }]);
      }
    } else if (!isOpen) {
      // Reset form on close
      setUrl('');
      setEvents('contact.created, contact.updated');
      setHeaders([{ key: '', value: '' }]);
      setErrors({});
    }
  }, [webhook, isOpen]);

  const handleHeaderChange = (index: number, field: 'key' | 'value', value: string) => {
    const newHeaders = [...headers];
    newHeaders[index][field] = value;
    setHeaders(newHeaders);
  };

  const addHeader = () => {
    setHeaders([...headers, { key: '', value: '' }]);
  };

  const removeHeader = (index: number) => {
    const newHeaders = headers.filter((_, i) => i !== index);
    // If all headers are removed, add a blank one back
    if (newHeaders.length === 0) {
        setHeaders([{ key: '', value: '' }]);
    } else {
        setHeaders(newHeaders);
    }
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!url) {
      newErrors.url = 'URL is required.';
    } else {
        try {
            new URL(url);
        } catch (_) {
            newErrors.url = 'Please enter a valid URL.';
        }
    }

    headers.forEach((h, i) => {
        if (h.key && !h.value) {
            newErrors[`header_value_${i}`] = 'Value is required.';
        }
        if (!h.key && h.value) {
            newErrors[`header_key_${i}`] = 'Key is required.';
        }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validate()) {
      return;
    }

    const headersObject = headers.reduce((acc, header) => {
      if (header.key && header.value) {
        acc[header.key] = header.value;
      }
      return acc;
    }, {} as Record<string, string>);

    const webhookData = {
      url,
      events: events.split(',').map(e => e.trim()).filter(e => e),
      headers: JSON.stringify(headersObject),
    };

    if (webhook) {
      onSave({ ...webhook, ...webhookData });
    } else {
      onSave(webhookData);
    }
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>{children}</DialogTrigger>
      <DialogContent className="sm:max-w-[625px]">
        <DialogHeader>
          <DialogTitle>{webhook ? 'Edit Webhook' : 'Add Webhook'}</DialogTitle>
          <DialogDescription>
            Configure your webhook to send event data to your own server.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-6 py-4">
          <div className="grid gap-2">
            <Label htmlFor="url">Webhook URL</Label>
            <Input id="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://api.example.com/webhook" />
            {errors.url && <p className="text-sm text-destructive">{errors.url}</p>}
          </div>
          <div className="grid gap-2">
            <Label htmlFor="events">Events</Label>
            <Input id="events" value={events} onChange={(e) => setEvents(e.target.value)} placeholder="contact.created, contact.updated" />
          </div>

          <div className="grid gap-2">
            <div className="flex items-center space-x-2">
                <Label>Headers</Label>
                <HoverCard>
                    <HoverCardTrigger>
                        <Info className="h-4 w-4 text-muted-foreground" />
                    </HoverCardTrigger>
                    <HoverCardContent className="w-80">
                        <p className="text-sm">
                            HTTP headers are sent with the webhook request. Use them for authentication (e.g., Authorization) or to provide metadata.
                        </p>
                    </HoverCardContent>
                </HoverCard>
            </div>
            <div className="space-y-2">
                {headers.map((header, index) => (
                    <div key={index} className="flex items-center space-x-2">
                        <div className="grid flex-1 gap-1.5">
                            <Input
                                placeholder="Key (e.g., Authorization)"
                                value={header.key}
                                onChange={(e) => handleHeaderChange(index, 'key', e.target.value)}
                            />
                            {errors[`header_key_${index}`] && <p className="text-sm text-destructive">{errors[`header_key_${index}`]}</p>}
                        </div>
                        <div className="grid flex-1 gap-1.5">
                            <Input
                                placeholder="Value (e.g., Bearer your-secret-token)"
                                value={header.value}
                                onChange={(e) => handleHeaderChange(index, 'value', e.target.value)}
                            />
                            {errors[`header_value_${index}`] && <p className="text-sm text-destructive">{errors[`header_value_${index}`]}</p>}
                        </div>
                        <Button variant="ghost" size="icon" onClick={() => removeHeader(index)} disabled={headers.length === 1 && !headers[0].key && !headers[0].value}>
                            <Trash2 className="h-4 w-4" />
                        </Button>
                    </div>
                ))}
            </div>
            <Button variant="outline" size="sm" className="mt-2 w-fit" onClick={addHeader}>
                <PlusCircle className="mr-2 h-4 w-4" />
                Add Header
            </Button>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => setIsOpen(false)}>Cancel</Button>
          <Button onClick={handleSave}>Save Webhook</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
