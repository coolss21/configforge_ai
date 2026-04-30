import { GenerateResponse } from './types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || (typeof window !== 'undefined' ? `http://${window.location.hostname}:8000` : "http://localhost:8000");

export const generateConfig = async (prompt: string, mode: 'fast' | 'quality'): Promise<GenerateResponse> => {
  const response = await fetch(`${API_URL}/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt, mode }),
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.error || errBody.detail || 'Failed to generate configuration');
  }
  return response.json();
};

export const evaluateSystem = async () => {
  const response = await fetch(`${API_URL}/evaluate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });
  if (!response.ok) {
    const errBody = await response.json().catch(() => ({}));
    throw new Error(errBody.error || errBody.detail || 'Failed to run evaluation');
  }
  return response.json();
};
