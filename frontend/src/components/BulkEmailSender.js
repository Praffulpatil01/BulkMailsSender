import React, { useState, useEffect } from 'react';
import axios from 'axios';
import '../styles/BulkEmailSender.css';
import EmailSettings from './EmailSettings';

const BulkEmailSender = () => {
  const [emails, setEmails] = useState('');
  const [subject, setSubject] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [attachment, setAttachment] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [senderEmail, setSenderEmail] = useState('');

  useEffect(() => {
    fetchSenderEmail();
  }, []);

  const fetchSenderEmail = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/api/get-sender-email');
      if (response.data.email) {
        setSenderEmail(response.data.email);
      }
    } catch (error) {
      console.error('Error fetching sender email:', error);
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 25 * 1024 * 1024) { // 25MB limit
        setStatus('File size must be less than 25MB');
        e.target.value = null;
        return;
      }
      setAttachment(file);
      setStatus('File attached: ' + file.name);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setStatus('');
    
    try {
      const emailList = emails
        .split(/[\n,;]/)
        .map(email => email.trim())
        .filter(email => email.length > 0);
      
      if (emailList.length === 0) {
        setStatus('Please enter at least one email address');
        return;
      }

      // Create FormData to handle file upload
      const formData = new FormData();
      formData.append('emails', JSON.stringify(emailList));
      formData.append('subject', subject);
      formData.append('content', content);
      if (attachment) {
        formData.append('attachment', attachment);
      }
      
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:5000';
      const response = await axios.post(`${apiUrl}/api/send-emails`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      console.log('Response:', response.data);
      setStatus(`${response.data.message}`);
      
      if (response.data.status === 'success') {
        setEmails('');
        setSubject('');
        setContent('');
        setAttachment(null);
        // Reset file input
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) fileInput.value = '';
      }
    } catch (error) {
      console.error('Error:', error);
      setStatus(`Error: ${error.response?.data?.message || error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bulk-email-container">
      <div className="form-container">
        <div className="header">
          <h2>Sendify</h2>
          <div className="settings-info">
            {senderEmail && <span>Sending as: {senderEmail}</span>}
            <button 
              className="settings-btn"
              onClick={() => setShowSettings(true)}
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Email Addresses (one per line):</label>
            <textarea
              value={emails}
              onChange={(e) => setEmails(e.target.value)}
              rows="10"
              placeholder="Enter email addresses (separate by newline, comma, or semicolon)..."
              required
            />
          </div>
          <div className="form-group">
            <label>Subject:</label>
            <input
              type="text"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Enter email subject"
              required
            />
          </div>
          <div className="form-group">
            <label>Content:</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows="10"
              placeholder="Enter email content..."
              required
            />
          </div>
          <div className="form-group">
            <label>Attachment (optional, max 25MB):</label>
            <input
              type="file"
              onChange={handleFileChange}
              className="file-input"
            />
          </div>
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Sending...' : 'Send Emails'}
          </button>
        </form>
        {status && <div className={`status ${status.includes('Error') ? 'error' : 'success'}`}>{status}</div>}
      </div>
      {showSettings && (
        <EmailSettings 
          onClose={() => setShowSettings(false)}
          onUpdate={fetchSenderEmail}
        />
      )}
    </div>
  );
};

export default BulkEmailSender; 