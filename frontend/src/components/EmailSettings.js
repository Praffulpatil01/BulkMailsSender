import React, { useState } from 'react';
import axios from 'axios';

const EmailSettings = ({ onClose, onUpdate }) => {
  const [senderEmail, setSenderEmail] = useState('');
  const [senderPassword, setSenderPassword] = useState('');
  const [status, setStatus] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://127.0.0.1:5000/api/update-credentials', {
        email: senderEmail,
        password: senderPassword
      });
      
      if (response.data.status === 'success') {
        setStatus('Credentials updated successfully!');
        onUpdate && onUpdate();
        setTimeout(() => onClose(), 1500);
      }
    } catch (error) {
      setStatus('Error updating credentials: ' + (error.response?.data?.message || error.message));
    }
  };

  return (
    <div className="settings-modal">
      <div className="settings-content">
        <h3>Email Settings</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Sender Email:</label>
            <input
              type="email"
              value={senderEmail}
              onChange={(e) => setSenderEmail(e.target.value)}
              placeholder="Enter Gmail address"
              required
            />
          </div>
          <div className="form-group">
            <label>App Password:</label>
            <input
              type="password"
              value={senderPassword}
              onChange={(e) => setSenderPassword(e.target.value)}
              placeholder="Enter Gmail App Password"
              required
            />
            <small className="help-text">
              Use an App Password from your Google Account settings
            </small>
          </div>
          <div className="button-group">
            <button type="submit" className="save-btn">Save</button>
            <button type="button" onClick={onClose} className="cancel-btn">Cancel</button>
          </div>
        </form>
        {status && <div className="settings-status">{status}</div>}
      </div>
    </div>
  );
};

export default EmailSettings; 