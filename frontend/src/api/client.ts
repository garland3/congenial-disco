import axios from 'axios';

export const apiClient = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface InterviewTemplate {
  id: number;
  name: string;
  description?: string;
  questions_schema: Record<string, { prompt: string; type: string }>;
  created_at: string;
  updated_at?: string;
  is_active: boolean;
}

export interface InterviewSession {
  id: number;
  template_id: number;
  session_data?: Record<string, any>;
  conversation_history?: Array<{sender: string, text: string}>;
  current_question_index: number;
  is_completed: boolean;
  awaiting_confirmation?: boolean;
  extracted_data?: Record<string, any>;
  field_scores?: Record<string, number>;
  created_at: string;
}

export interface ChatResponse {
  response: string;
  is_complete: boolean;
  awaiting_confirmation?: boolean;
  extracted_data?: Record<string, any>;
  field_scores?: Record<string, number>;
  session_data?: Record<string, any>;
}

export interface SessionStatus {
  session_id: number;
  current_question: number;
  total_questions: number;
  is_completed: boolean;
  progress_percentage: number;
}

export const adminApi = {
  getTemplates: () => apiClient.get<InterviewTemplate[]>('/api/admin/templates'),
  createTemplate: (data: { name: string; description?: string; questions_schema: Record<string, any> }) =>
    apiClient.post<InterviewTemplate>('/api/admin/templates', data),
  updateTemplate: (id: number, data: Partial<InterviewTemplate>) =>
    apiClient.put<InterviewTemplate>(`/api/admin/templates/${id}`, data),
  deleteTemplate: (id: number) => apiClient.delete(`/api/admin/templates/${id}`),
  getTemplate: (id: number) => apiClient.get<InterviewTemplate>(`/api/admin/templates/${id}`),
  generateTemplate: (goals: string) => 
    apiClient.post<InterviewTemplate>('/api/admin/generate-template', { goals }),
};

export const interviewApi = {
  getTemplates: () => apiClient.get<InterviewTemplate[]>('/api/interview/templates'),
  startInterview: (templateId: number) => 
    apiClient.post<InterviewSession>(`/api/interview/start/${templateId}`),
  getSession: (sessionId: number) => 
    apiClient.get<InterviewSession>(`/api/interview/session/${sessionId}`),
  sendMessage: (sessionId: number, message: string) =>
    apiClient.post<ChatResponse>(`/api/interview/session/${sessionId}/chat`, { message }),
  getSessionStatus: (sessionId: number) => 
    apiClient.get<SessionStatus>(`/api/interview/session/${sessionId}/status`),
};