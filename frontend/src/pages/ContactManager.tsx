import React, { useState } from 'react';
import AddContact from '../components/AddContact';
import ContactList from '../components/ContactList';
import VerificationControls from '../components/VerificationControls';

const ContactManager: React.FC = () => {
  const [selectedContacts, setSelectedContacts] = useState<number[]>([]);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleContactAdded = () => {
    setRefreshKey(prev => prev + 1);
  };

  const handleVerificationStarted = () => {
    setRefreshKey(prev => prev + 1);
    setSelectedContacts([]);
  };

  return (
    <div>
      <h2>Contact Management</h2>
      <AddContact onContactAdded={handleContactAdded} />
      <hr />
      <VerificationControls selectedContacts={selectedContacts} onVerificationStarted={handleVerificationStarted} />
      <ContactList
        selectedContacts={selectedContacts}
        setSelectedContacts={setSelectedContacts}
        refreshKey={refreshKey}
      />
    </div>
  );
};

export default ContactManager;
