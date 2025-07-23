// src/components/Chatbot.tsx
// REMOVED: import React, { useState, useRef, useEffect } from 'react'; // React import is not needed for modern JSX transform
import { useState, useRef, useEffect } from 'react'; // Keep these hooks
import { TextField, Button, Box, Paper, Typography, CircularProgress } from '@mui/material';

// --- CRITICAL FIX 1: Define the Message interface ---
interface Message {
  sender: 'user' | 'ai'; // Explicitly define sender can only be 'user' or 'ai'
  text: string;           // Explicitly define text as a string
}

function Chatbot() {
  // --- CRITICAL FIX 2: Explicitly type the useState for messages ---
  const [messages, setMessages] = useState<Message[]>([]); // Initialize as an array of Message objects
  const [input, setInput] = useState<string>(''); // Good practice to type primitive states too
  const [loading, setLoading] = useState<boolean>(false); // Good practice to type primitive states too

  // --- CRITICAL FIX 3: Explicitly type useRef ---
  const messagesEndRef = useRef<HTMLDivElement>(null); // Type for div element

  // Ensure this is defined or available via .env setup for the Flask API
  const FLASK_API_BASE_URL = import.meta.env.VITE_FLASK_API_URL;

  const sendMessage = async () => {
    if (input.trim() === '') return;

    const userMessage: Message = { sender: 'user', text: input }; // Ensure userMessage conforms to Message type
    setMessages((prevMessages) => [...prevMessages, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch(`${FLASK_API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.details || 'Failed to get AI response');
      }

      const data = await response.json();
      const aiMessage: Message = { sender: 'ai', text: data.response }; // Ensure aiMessage conforms to Message type
      setMessages((prevMessages) => [...prevMessages, aiMessage]);
    } catch (error: unknown) { // --- CRITICAL FIX 4: Type guard for 'error' ---
      console.error('Error sending message:', error);
      let errorMessage = 'An unknown error occurred.';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      setMessages((prevMessages) => [
        ...prevMessages,
        { sender: 'ai', text: `Error: ${errorMessage}` }, // This now correctly matches Message[]
      ]);
    } finally {
      setLoading(false);
    }
  };

  // --- CRITICAL FIX 5: Type the 'event' parameter for handleKeyPress ---
  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter' && !loading) {
      sendMessage();
    }
  };

  // Scroll to the latest message
  useEffect(() => {
    // messagesEndRef.current is now correctly typed as HTMLDivElement | null
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }); // This error should be gone
  }, [messages]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 200px)', minHeight: '400px' }}>
      <Box sx={{ flexGrow: 1, overflowY: 'auto', p: 1, mb: 2 }}>
        {messages.map((msg, index) => ( // 'msg' is now correctly typed as 'Message'
          <Box key={index} sx={{
            display: 'flex',
            justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start', // 'msg.sender' is now correctly typed
            mb: 1
          }}>
            <Paper
              sx={{
                p: 1.5,
                maxWidth: '75%',
                bgcolor: msg.sender === 'user' ? '#e0f7fa' : '#f5f5f5', // 'msg.sender' is now correctly typed
                borderRadius: '10px',
                borderBottomRightRadius: msg.sender === 'user' ? '0' : '10px', // 'msg.sender' is now correctly typed
                borderBottomLeftRadius: msg.sender === 'ai' ? '0' : '10px', // 'msg.sender' is now correctly typed
              }}
            >
              <Typography variant="body2">{msg.text}</Typography> {/* 'msg.text' is now correctly typed */}
            </Paper>
          </Box>
        ))}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-start', mb: 1 }}>
            <CircularProgress size={20} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>
      <Box sx={{ display: 'flex', gap: 1, mt: 'auto' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
        />
        <Button variant="contained" onClick={sendMessage} disabled={loading}>
          Send
        </Button>
      </Box>
    </Box>
  );
}

export default Chatbot;