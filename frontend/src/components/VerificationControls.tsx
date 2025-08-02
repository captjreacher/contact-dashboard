import React, { useState } from 'react';
import { createVerificationJob, runVerificationJob } from '../services/api';

interface VerificationControlsProps {
  selectedContacts: number[];
  onVerificationStarted: () => void;
}

const VerificationControls: React.FC<VerificationControlsProps> = ({ selectedContacts, onVerificationStarted }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [jobId, setJobId] = useState<string | null>(null);

  const handleCreateJob = async () => {
    if (selectedContacts.length === 0) {
      setError('Please select at least one contact to verify.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await createVerificationJob(selectedContacts);
      setJobId(response.job.job_id);
    } catch (err: any) {
      setError(err.message || 'Failed to create verification job.');
    } finally {
      setLoading(false);
    }
  };

  const handleRunJob = async () => {
    if (!jobId) {
      setError('Please create a job first.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      await runVerificationJob(jobId);
      onVerificationStarted();
      setJobId(null);
    } catch (err: any) {
      setError(err.message || 'Failed to run verification job.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h3>Verification Controls</h3>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <button onClick={handleCreateJob} disabled={loading || selectedContacts.length === 0}>
        Add to Verification Queue ({selectedContacts.length} selected)
      </button>
      {jobId && (
        <>
          <p>Job Created: {jobId}</p>
          <button onClick={handleRunJob} disabled={loading}>
            Run Verification Job
          </button>
        </>
      )}
    </div>
  );
};

export default VerificationControls;
