import React, { useEffect, useState } from 'react';
import { getContacts } from '../services/api';

interface Contact {
  contact_id: number;
  first_name: string;
  last_name: string;
  email_address: string;
  company_name: string;
  email_verification_status: string;
}

interface ContactListProps {
  selectedContacts: number[];
  setSelectedContacts: React.Dispatch<React.SetStateAction<number[]>>;
  refreshKey: number;
}

const ContactList: React.FC<ContactListProps> = ({ selectedContacts, setSelectedContacts, refreshKey }) => {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchContacts = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await getContacts();
        setContacts(response.contacts);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch contacts.');
      } finally {
        setLoading(false);
      }
    };

    fetchContacts();
  }, [refreshKey]);

  const handleSelectContact = (contactId: number) => {
    setSelectedContacts(prev =>
      prev.includes(contactId)
        ? prev.filter(id => id !== contactId)
        : [...prev, contactId]
    );
  };

  if (loading) return <p>Loading contacts...</p>;
  if (error) return <p style={{ color: 'red' }}>{error}</p>;

  return (
    <div>
      <h3>Contact List</h3>
      <table>
        <thead>
          <tr>
            <th>Select</th>
            <th>Name</th>
            <th>Email</th>
            <th>Company</th>
            <th>Verification Status</th>
          </tr>
        </thead>
        <tbody>
          {contacts.map(contact => (
            <tr key={contact.contact_id}>
              <td>
                <input
                  type="checkbox"
                  checked={selectedContacts.includes(contact.contact_id)}
                  onChange={() => handleSelectContact(contact.contact_id)}
                />
              </td>
              <td>{contact.first_name} {contact.last_name}</td>
              <td>{contact.email_address}</td>
              <td>{contact.company_name}</td>
              <td>{contact.email_verification_status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ContactList;
