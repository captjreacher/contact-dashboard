import React, { useState } from 'react';
import AddEditWebhookModal from './AddEditWebhookModal';  // Adjust path if needed

function App() {
  const [modalOpen, setModalOpen] = useState(false);

  return (
    <div style={{ padding: 20 }}>
      <h1>Contact Dashboard</h1>
      <button onClick={() => setModalOpen(true)} style={{ marginBottom: 20 }}>
        Open Webhook Modal
      </button>

      {modalOpen && (
        <AddEditWebhookModal
          onClose={() => setModalOpen(false)}
          // Add props here as needed, e.g. editing webhook data
        />
      )}
    </div>
  );
}

export default App;






