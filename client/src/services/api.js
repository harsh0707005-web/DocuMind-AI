/**
 * API Service - handles all backend communication
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8003';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60s for AI responses
});

// ---- Chat ----
export const sendMessage = async (message, conversationId, model, mode = 'chat') => {
  const { data } = await api.post('/api/chat/', {
    message,
    conversation_id: conversationId,
    model,
    mode,
  });
  return data;
};

export const getConversations = async () => {
  const { data } = await api.get('/api/chat/conversations');
  return data.conversations;
};

export const getMessages = async (conversationId) => {
  const { data } = await api.get(`/api/chat/conversations/${conversationId}/messages`);
  return data.messages;
};

export const deleteConversation = async (conversationId) => {
  await api.delete(`/api/chat/conversations/${conversationId}`);
};

// ---- Documents ----
export const uploadDocument = async (file, onProgress) => {
  const formData = new FormData();
  formData.append('file', file);

  const { data } = await api.post('/api/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    },
  });
  return data;
};

export const getDocuments = async () => {
  const { data } = await api.get('/api/documents/');
  return data;
};

export const deleteDocument = async (docId) => {
  await api.delete(`/api/documents/${docId}`);
};

export const deleteAllDocuments = async () => {
  await api.delete('/api/documents/');
};

// ---- Study Tools ----
export const generateQuiz = async (model, numItems = 5, topic = null) => {
  const { data } = await api.post('/api/study/quiz', {
    model,
    num_items: numItems,
    topic,
  });
  return data;
};

export const generateFlashcards = async (model, numItems = 10, topic = null) => {
  const { data } = await api.post('/api/study/flashcards', {
    model,
    num_items: numItems,
    topic,
  });
  return data;
};

export const summarizeDocuments = async (model, topic = null) => {
  const { data } = await api.post('/api/study/summarize', {
    model,
    topic,
  });
  return data;
};

export const getStudyStats = async () => {
  const { data } = await api.get('/api/study/stats');
  return data;
};

// ---- Health ----
export const checkHealth = async () => {
  const { data } = await api.get('/api/health');
  return data;
};

export default api;
