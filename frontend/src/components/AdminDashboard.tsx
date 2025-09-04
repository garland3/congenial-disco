import { useState, useEffect } from 'react';
import { adminApi } from '../api/client';
import type { InterviewTemplate } from '../api/client';

const AdminDashboard = () => {
  const [templates, setTemplates] = useState<InterviewTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [expandedTemplates, setExpandedTemplates] = useState<Set<number>>(new Set());
  const [goals, setGoals] = useState('');
  const [newTemplate, setNewTemplate] = useState({
    name: '',
    description: '',
    questions_schema: {}
  });

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await adminApi.getTemplates();
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateTemplate = async () => {
    if (!goals.trim()) return;
    
    try {
      setLoading(true);
      const response = await adminApi.generateTemplate(goals);
      setTemplates([...templates, response.data]);
      setGoals('');
      setShowGenerateForm(false);
    } catch (error) {
      console.error('Failed to generate template:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteTemplate = async (id: number) => {
    if (!confirm('Are you sure you want to delete this template?')) return;
    
    try {
      await adminApi.deleteTemplate(id);
      setTemplates(templates.filter(t => t.id !== id));
    } catch (error) {
      console.error('Failed to delete template:', error);
    }
  };

  const handleUpdateField = async (templateId: number, fieldName: string, fieldProp: string, value: string) => {
    try {
      // Update local state immediately for better UX
      setTemplates(templates.map(template => {
        if (template.id === templateId) {
          return {
            ...template,
            questions_schema: {
              ...template.questions_schema,
              [fieldName]: {
                ...template.questions_schema[fieldName],
                [fieldProp]: value
              }
            }
          };
        }
        return template;
      }));

      // Update the template on the server
      const template = templates.find(t => t.id === templateId);
      if (template) {
        await adminApi.updateTemplate(templateId, {
          questions_schema: {
            ...template.questions_schema,
            [fieldName]: {
              ...template.questions_schema[fieldName],
              [fieldProp]: value
            }
          }
        });
      }
    } catch (error) {
      console.error('Failed to update template field:', error);
      // Revert the local state change on error
      fetchTemplates();
    }
  };

  const toggleTemplateExpanded = (templateId: number) => {
    const newExpanded = new Set(expandedTemplates);
    if (newExpanded.has(templateId)) {
      newExpanded.delete(templateId);
    } else {
      newExpanded.add(templateId);
    }
    setExpandedTemplates(newExpanded);
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-800">Admin Dashboard</h2>
        <div className="space-x-2">
          <button
            onClick={() => setShowGenerateForm(true)}
            className="px-4 py-2 bg-green-600 text-white font-semibold rounded-xl hover:bg-green-700 transition-colors"
          >
            Generate Template
          </button>
        </div>
      </div>

      {showGenerateForm && (
        <div className="bg-gray-50 p-6 rounded-2xl">
          <h3 className="text-lg font-semibold mb-4">Generate Template from Goals</h3>
          <textarea
            value={goals}
            onChange={(e) => setGoals(e.target.value)}
            className="w-full h-32 p-4 border border-gray-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            placeholder="Describe your interview goals..."
          />
          <div className="mt-4 space-x-2">
            <button
              onClick={handleGenerateTemplate}
              className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
            >
              Generate
            </button>
            <button
              onClick={() => {
                setShowGenerateForm(false);
                setGoals('');
              }}
              className="px-6 py-3 bg-gray-600 text-white font-semibold rounded-xl hover:bg-gray-700 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {templates.map((template) => {
          const isExpanded = expandedTemplates.has(template.id);
          return (
            <div key={template.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              {/* Collapsed Header */}
              <div className="p-4 cursor-pointer hover:bg-gray-50 transition-colors" onClick={() => toggleTemplateExpanded(template.id)}>
                <div className="flex justify-between items-center">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        <svg 
                          className={`w-5 h-5 text-gray-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} 
                          fill="none" 
                          viewBox="0 0 24 24" 
                          stroke="currentColor"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg text-gray-800">{template.name}</h3>
                        <div className="flex items-center space-x-4 mt-1">
                          <p className="text-gray-600 text-sm">{template.description || "No description available"}</p>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {Object.keys(template.questions_schema).length} questions
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteTemplate(template.id);
                    }}
                    className="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-gray-100">
                  <div className="space-y-4 mt-4">
                    <h4 className="font-medium text-gray-800">Questions:</h4>
                    {Object.entries(template.questions_schema).map(([fieldName, field]) => (
                      <div key={fieldName} className="bg-gray-50 p-4 rounded-lg">
                        <div className="flex justify-between items-start mb-2">
                          <label className="font-medium text-sm text-gray-700">{fieldName}:</label>
                          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">{field.type}</span>
                        </div>
                        <textarea
                          value={field.prompt}
                          onChange={(e) => handleUpdateField(template.id, fieldName, 'prompt', e.target.value)}
                          className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                          rows={2}
                        />
                        <div className="mt-2">
                          <select
                            value={field.type}
                            onChange={(e) => handleUpdateField(template.id, fieldName, 'type', e.target.value)}
                            className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                          >
                            <option value="string">String</option>
                            <option value="story">Story</option>
                            <option value="yes/no">Yes/No</option>
                          </select>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {templates.length === 0 && (
        <div className="text-center py-8">
          <p className="text-gray-500 mb-4">No interview templates found.</p>
          <button
            onClick={() => setShowGenerateForm(true)}
            className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-colors"
          >
            Create Your First Template
          </button>
        </div>
      )}
    </div>
  );
};

export default AdminDashboard;