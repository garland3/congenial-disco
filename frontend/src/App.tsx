import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AdminDashboard from './components/AdminDashboard';
import InterviewHome from './components/InterviewHome';
import InterviewSession from './components/InterviewSession';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100 w-full" style={{ fontFamily: 'Inter, sans-serif' }}>
        <div className="w-full bg-white overflow-hidden">
          <header className="bg-indigo-600 p-6">
            <h1 className="text-3xl font-bold text-white text-center">Interview Assistant</h1>
            <nav className="mt-4 flex justify-center space-x-4">
              <Link to="/" className="text-white hover:text-indigo-200 transition-colors">
                Interviews
              </Link>
              <Link to="/admin" className="text-white hover:text-indigo-200 transition-colors">
                Admin
              </Link>
            </nav>
          </header>
          
          <div className="p-6">
            <Routes>
              <Route path="/" element={<InterviewHome />} />
              <Route path="/admin" element={<AdminDashboard />} />
              <Route path="/interview/:sessionId" element={<InterviewSession />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  );
}

export default App;
