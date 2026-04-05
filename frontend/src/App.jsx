import { useState } from 'react';
import UploadForm from './components/UploadForm';
import LoadingState from './components/LoadingState';
import VerdictHeader from './components/VerdictHeader';
import FlagChips from './components/FlagChips';
import Explanation from './components/Explanation';
import AnalysisDetail from './components/AnalysisDetail';
import Evidence from './components/Evidence';

const API_URL = 'http://localhost:8000';

function App() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleVerification = async (file, caption, searchEnabled) => {
    setError('');
    setResult(null);
    setLoading(true);

    const formData = new FormData();
    formData.append('media', file);
    formData.append('caption', caption);
    formData.append('search_enabled', searchEnabled.toString());

    try {
      const response = await fetch(`${API_URL}/verify`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Verification failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>VerifyAI</h1>
        <p>Check whether an image or video is being used truthfully.</p>
      </header>

      <main className="main-content">
        <UploadForm onSubmit={handleVerification} disabled={loading} />

        {loading && <LoadingState />}

        {error && (
          <div className="error-message">
            <h3>Error</h3>
            <p>{error}</p>
          </div>
        )}

        {result && (
          <div className="results">
            <VerdictHeader result={result} />
            <FlagChips flags={result.flags} />
            <Explanation explanation={result.explanation} />
            <AnalysisDetail result={result} />
            {result.evidence && result.evidence.length > 0 && (
              <Evidence evidence={result.evidence} />
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;