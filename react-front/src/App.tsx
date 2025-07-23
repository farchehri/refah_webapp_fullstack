// src/App.tsx
import React, { useState, useEffect, useRef } from 'react';
import { Box, Typography, Paper, TextField, Button, CircularProgress } from '@mui/material';
import { Send as SendIcon, AutoAwesome as AiIcon } from '@mui/icons-material';

// Define a type for our message objects for better type safety
interface ChatMessage {
  sender: 'user' | 'assistant';
  text: string;
}

function App() {
  // --- IMPORTANT ---
  // This URL is hardcoded for this preview environment to work.
  // When you move this code back to your VSCode project, you should use your environment variable:
  // const flaskApiUrl = import.meta.env.VITE_FLASK_API_URL;
  const flaskApiUrl = "https://gemini-web-agent-466416.uk.r.appspot.com";

  // --- STATE MANAGEMENT FOR CHAT ---
  const [messages, setMessages] = useState<ChatMessage[]>([
    { sender: 'assistant', text: "Ask questions about the data and get instant insights." }
  ]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const chatboxRef = useRef<HTMLDivElement>(null);

  // --- FUNCTION TO SCROLL CHAT TO THE LATEST MESSAGE ---
  useEffect(() => {
    if (chatboxRef.current) {
      chatboxRef.current.scrollTop = chatboxRef.current.scrollHeight;
    }
  }, [messages]);

  // --- FUNCTION TO HANDLE SENDING A MESSAGE ---
  const handleSendMessage = async () => {
    const trimmedMessage = currentMessage.trim();
    if (trimmedMessage === '' || isLoading) return;

    setMessages(prevMessages => [...prevMessages, { sender: 'user', text: trimmedMessage }]);
    setCurrentMessage('');
    setIsLoading(true);

    try {
      const response = await fetch(`${flaskApiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: trimmedMessage }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.statusText}`);
      }

      const data = await response.json();
      const assistantMessage = data.response || "Sorry, I couldn't get a response.";
      setMessages(prevMessages => [...prevMessages, { sender: 'assistant', text: assistantMessage }]);

    } catch (error) {
      console.error("Failed to fetch from backend:", error);
      const errorMessage = "Sorry, I'm having trouble connecting. Please try again later.";
      setMessages(prevMessages => [...prevMessages, { sender: 'assistant', text: errorMessage }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Allow sending with the "Enter" key
  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  // The entire app is now just the chat component, designed to fill whatever frame it's embedded in.
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: '#f4f6f8', p: 1 }}>
      <Paper 
        elevation={0} // No shadow needed when embedded
        sx={{ 
          display: 'flex',
          flexDirection: 'column',
          flexGrow: 1, // Allows the paper to grow and fill the available space
          borderRadius: '12px',
          border: '1px solid #e0e0e0',
          overflow: 'hidden' // Ensures content stays within the rounded corners
        }}
      >
        {/* Chat Header */}
        <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', bgcolor: '#ffffff' }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <AiIcon color="primary" sx={{ mr: 1.5 }}/>
                <Typography variant="h6" component="h2" sx={{ fontWeight: 'bold', color: '#333' }}>
                  AI Assistant
                </Typography>
            </Box>
        </Box>
        
        {/* Chat Message Area */}
        <Box 
          ref={chatboxRef}
          sx={{ 
            flexGrow: 1,
            p: 2,
            display: 'flex',
            flexDirection: 'column',
            gap: 2,
            overflowY: 'auto'
          }}
        >
          {messages.map((msg, index) => (
            <Box 
              key={index}
              sx={{
                alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                bgcolor: msg.sender === 'user' ? 'primary.main' : '#ffffff',
                color: msg.sender === 'user' ? 'primary.contrastText' : 'text.primary',
                px: 1.5,
                py: 1,
                borderRadius: '16px',
                maxWidth: '80%',
                boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
              }}
            >
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>{msg.text}</Typography>
            </Box>
          ))}
          {isLoading && (
            <Box sx={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
               <CircularProgress size={20} />
               <Typography variant="body2" color="text.secondary">Assistant is typing...</Typography>
            </Box>
          )}
        </Box>

        {/* Chat Input Area */}
        <Box sx={{ p: 2, borderTop: '1px solid #e0e0e0', bgcolor: '#ffffff' }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <TextField 
                fullWidth 
                variant="outlined" 
                placeholder="Ask a question..."
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                disabled={isLoading}
                sx={{ '& .MuiOutlinedInput-root': { borderRadius: '12px' } }}
              />
              <Button 
                variant="contained" 
                aria-label="send message"
                onClick={handleSendMessage}
                disabled={isLoading}
                sx={{ borderRadius: '12px', px: 2 }}
              >
                <SendIcon />
              </Button>
            </Box>
        </Box>
      </Paper>
    </Box>
  );
}

export default App;
