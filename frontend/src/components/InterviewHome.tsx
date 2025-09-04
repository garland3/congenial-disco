import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { interviewApi } from '../api/client';
import type { InterviewTemplate } from '../api/client';

const InterviewHome = () => {
  const [templates, setTemplates] = useState<InterviewTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await interviewApi.getTemplates();
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const startInterview = async (templateId: number) => {
    try {
      const response = await interviewApi.startInterview(templateId);
      navigate(`/interview/${response.data.id}`);
    } catch (error) {
      console.error('Failed to start interview:', error);
      alert('Failed to start interview session.');
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="bg-gray-50 p-6 rounded-2xl">
        <h2 className="text-2xl font-bold text-gray-800 mb-4">Available Interviews</h2>
        <p className="text-gray-600 mb-6">Select an interview template to begin your interview session.</p>
        
        {templates.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2">
            {templates.map((template) => (
              <div key={template.id} className="bg-white p-4 rounded-xl border border-gray-200 hover:border-indigo-300 transition-colors">
                <h3 className="font-semibold text-lg text-gray-800">{template.name}</h3>
                <p className="text-gray-600 text-sm mt-2 mb-4">{template.description || "No description available"}</p>
                <p className="text-sm text-gray-500 mb-4">{Object.keys(template.questions_schema).length} questions</p>
                <button 
                  onClick={() => startInterview(template.id)}
                  className="w-full px-4 py-2 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  Start Interview
                </button>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No interview templates available.</p>
            <button
              onClick={() => navigate('/admin')}
              className="inline-block px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Go to Admin to Create Templates
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default InterviewHome;