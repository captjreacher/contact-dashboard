import React, { useState } from 'react';
import ContactManager from './pages/ContactManager';
import WebhookSettings from './pages/WebhookSettings';
import './App.css';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('contacts');

  return (
    <div className="App">
      <header>
        <h1>Lead & Webhook Management</h1>
        <nav>
          <button onClick={() => setActiveTab('contacts')} className={activeTab === 'contacts' ? 'active' : ''}>
            Contact Manager
          </button>
          <button onClick={() => setActiveTab('webhooks')} className={activeTab === 'webhooks' ? 'active' : ''}>
            Webhook Settings
          </button>
        </nav>
      </header>
      <main>
        {activeTab === 'contacts' && <ContactManager />}
        {activeTab === 'webhooks' && <WebhookSettings />}
      </main>
    </div>
  );
};

export default App;
