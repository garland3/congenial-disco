import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { interviewApi } from '../api/client';
import type { InterviewSession as ISession, SessionStatus, ChatResponse } from '../api/client';

interface Message {
  sender: 'user' | 'assistant';
  text: string;
}

const InterviewSession = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [session, setSession] = useState<ISession | null>(null);
  const [status, setStatus] = useState<SessionStatus | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(true);
  const [isComplete, setIsComplete] = useState(false);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [extractedData, setExtractedData] = useState<Record<string, any>>({});
  const [fieldScores, setFieldScores] = useState<Record<string, number>>({});
  const [sessionData, setSessionData] = useState<Record<string, any>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (sessionId) {
      fetchSession();
      startConversation();
    }
  }, [sessionId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchSession = async () => {
    if (!sessionId) return;
    
    try {
      const [sessionResponse, statusResponse] = await Promise.all([
        interviewApi.getSession(parseInt(sessionId)),
        interviewApi.getSessionStatus(parseInt(sessionId))
      ]);
      
      setSession(sessionResponse.data);
      setStatus(statusResponse.data);
      setIsComplete(sessionResponse.data.is_completed);
      
      if (sessionResponse.data.session_data) {
        setSessionData(sessionResponse.data.session_data);
      }
    } catch (error) {
      console.error('Failed to fetch session:', error);
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const startConversation = () => {
    setMessages([{
      sender: 'assistant',
      text: 'Hello! Welcome to your interview session. I will ask you a series of questions. Please answer as completely as possible. Let me know when you\'re ready to begin!'
    }]);
  };

  const updateStatus = async () => {
    if (!sessionId) return;
    
    try {
      const response = await interviewApi.getSessionStatus(parseInt(sessionId));
      setStatus(response.data);
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !sessionId || isComplete) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setMessages(prev => [...prev, { sender: 'user', text: userMessage }]);

    try {
      const response = await interviewApi.sendMessage(parseInt(sessionId), userMessage);
      const data: ChatResponse = response.data;
      
      setMessages(prev => [...prev, { sender: 'assistant', text: data.response }]);
      
      // Update extracted data and field scores if available
      if (data.extracted_data) {
        setExtractedData(data.extracted_data);
      }
      if (data.field_scores) {
        setFieldScores(data.field_scores);
      }
      
      // Handle different states
      if (data.is_complete) {
        setIsComplete(true);
        setAwaitingConfirmation(false);
        if (data.session_data) {
          setSessionData(data.session_data);
        }
      } else if (data.awaiting_confirmation) {
        setAwaitingConfirmation(true);
      } else {
        setAwaitingConfirmation(false);
      }
      
      updateStatus();
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages(prev => [...prev, { sender: 'assistant', text: 'Sorry, there was an error processing your message. Please try again.' }]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      sendMessage();
    }
  };

  const exportData = () => {
    const dataStr = JSON.stringify({ sessionData, status }, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `interview-session-${sessionId}.json`;
    link.click();
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (!session) {
    return <div className="text-center py-8">Session not found.</div>;
  }

  return (
    <div className="space-y-6">
      {/* Progress Bar */}
      <div className="bg-gray-50 p-4 rounded-xl">
        <div className="flex justify-between items-center mb-2">
          <h2 className="text-lg font-semibold">Interview Progress</h2>
          <div className="text-sm text-gray-600">
            {awaitingConfirmation ? "Awaiting Confirmation" : "In Progress"}
          </div>
        </div>
        
        {Object.keys(fieldScores).length > 0 && (
          <div className="space-y-2 mb-4">
            {Object.entries(fieldScores).map(([fieldName, score]) => (
              <div key={fieldName} className="flex items-center justify-between">
                <span className="text-sm text-gray-700 capitalize">
                  {fieldName.replace(/_/g, ' ')}
                </span>
                <div className="flex items-center space-x-2">
                  <div className="w-20 bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        score >= 7 ? 'bg-green-500' : score >= 4 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${(score / 10) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-600">{score}/10</span>
                </div>
              </div>
            ))}
          </div>
        )}
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-300 ${
              awaitingConfirmation ? 'bg-blue-600' : 'bg-indigo-600'
            }`}
            style={{ width: `${status?.progress_percentage || 0}%` }}
          ></div>
        </div>
      </div>

      {/* Chat Interface */}
      <div className="flex flex-col h-96 bg-gray-50 rounded-2xl p-4">
        <div className="flex-grow overflow-y-auto space-y-4 p-2 mb-4">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex flex-col max-w-xs p-3 rounded-2xl break-words whitespace-pre-wrap ${
                message.sender === 'user'
                  ? 'self-end bg-indigo-100 text-indigo-900 rounded-br-none'
                  : 'self-start bg-gray-100 text-gray-800 rounded-bl-none'
              }`}
            >
              {message.text}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
        
        <div className="flex items-center space-x-2">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isComplete}
            className="flex-grow p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-colors duration-200"
            placeholder={isComplete ? "Interview completed" : "Type your response..."}
          />
          <button
            onClick={sendMessage}
            disabled={isComplete || !inputMessage.trim()}
            className="p-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>

      {/* Confirmation Panel */}
      {awaitingConfirmation && !isComplete && Object.keys(extractedData).length > 0 && (
        <div className="bg-blue-50 p-6 rounded-2xl border-2 border-blue-200">
          <h2 className="text-xl font-semibold text-blue-800 mb-3">Please Review Your Information</h2>
          <p className="text-blue-700 mb-4">I've gathered the following information from our conversation. Please confirm if this is accurate:</p>
          
          <div className="bg-white p-4 rounded-xl mb-4">
            {Object.entries(extractedData).map(([key, value]) => (
              value && (
                <div key={key} className="mb-3">
                  <strong className="text-gray-800">{key.replace(/_/g, ' ').toUpperCase()}:</strong>
                  <p className="text-gray-600 mt-1">{value}</p>
                </div>
              )
            ))}
          </div>
          
          <div className="space-x-4">
            <button
              onClick={async () => {
                if (!sessionId) return;
                const confirmMessage = 'yes, that looks correct';
                setMessages(prev => [...prev, { sender: 'user', text: confirmMessage }]);
                try {
                  const response = await interviewApi.sendMessage(parseInt(sessionId), confirmMessage);
                  const data: ChatResponse = response.data;
                  setMessages(prev => [...prev, { sender: 'assistant', text: data.response }]);
                  if (data.is_complete) {
                    setIsComplete(true);
                    setAwaitingConfirmation(false);
                    if (data.session_data) {
                      setSessionData(data.session_data);
                    }
                  }
                } catch (error) {
                  console.error('Failed to confirm:', error);
                }
              }}
              className="px-6 py-3 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors"
            >
              ✓ Confirm - This is Correct
            </button>
            <button
              onClick={async () => {
                if (!sessionId) return;
                const changeMessage = 'no, that needs changes';
                setMessages(prev => [...prev, { sender: 'user', text: changeMessage }]);
                try {
                  const response = await interviewApi.sendMessage(parseInt(sessionId), changeMessage);
                  const data: ChatResponse = response.data;
                  setMessages(prev => [...prev, { sender: 'assistant', text: data.response }]);
                  setAwaitingConfirmation(false);
                } catch (error) {
                  console.error('Failed to request changes:', error);
                }
              }}
              className="px-6 py-3 bg-gray-600 text-white font-semibold rounded-xl hover:bg-gray-700 transition-colors"
            >
              ✗ Make Changes
            </button>
          </div>
        </div>
      )}

      {/* Completion Panel */}
      {isComplete && (
        <div className="bg-green-50 p-6 rounded-2xl">
          <h2 className="text-xl font-semibold text-green-800 mb-3">Interview Complete!</h2>
          <p className="text-green-700 mb-4">Thank you for completing the interview. Here's a summary of your responses:</p>
          
          {Object.keys(sessionData).length > 0 && (
            <div className="bg-white p-4 rounded-xl mb-4">
              {Object.entries(sessionData).map(([key, value]) => (
                <div key={key} className="mb-3">
                  <strong className="text-gray-800">{key.replace(/_/g, ' ').toUpperCase()}:</strong>
                  <p className="text-gray-600 mt-1">{value}</p>
                </div>
              ))}
            </div>
          )}
          
          <div className="space-x-4">
            <button
              onClick={() => navigate('/')}
              className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Take Another Interview
            </button>
            <button
              onClick={exportData}
              className="px-6 py-3 bg-gray-600 text-white font-semibold rounded-xl hover:bg-gray-700 transition-colors"
            >
              Export Data
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterviewSession;