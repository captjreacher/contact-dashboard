import React, { useState } from 'react';
import { addContact } from '../services/api';

interface AddContactProps {
  onContactAdded: () => void;
}

const AddContact: React.FC<AddContactProps> = ({ onContactAdded }) => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!firstName || !lastName || !email) {
      setError('All fields are required.');
      return;
    }

    try {
      await addContact({ first_name: firstName, last_name: lastName, email_address: email });
      setSuccess('Contact added successfully!');
      setFirstName('');
      setLastName('');
      setEmail('');
      onContactAdded();
    } catch (err: any) {
      setError(err.message || 'Failed to add contact.');
    }
  };

  return (
    <div>
      <h3>Add New Contact</h3>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {success && <p style={{ color: 'green' }}>{success}</p>}
      <form onSubmit={handleSubmit}>
        <div>
          <input
            type="text"
            placeholder="First Name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
          />
        </div>
        <div>
          <input
            type="text"
            placeholder="Last Name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
          />
        </div>
        <div>
          <input
            type="email"
            placeholder="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <button type="submit">Add Contact</button>
      </form>
    </div>
  );
};

export default AddContact;
