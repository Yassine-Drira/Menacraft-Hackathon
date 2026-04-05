import React, { useState } from 'react';
import axios from 'axios';
import { Upload, ShieldAlert, ShieldCheck, Loader2 } from 'lucide-react';

function App() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setResult(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/predict', formData);
      setResult(response.data);
    } catch (err) {
      alert("Error processing video. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-4">
      <div className="bg-white p-8 rounded-xl shadow-lg max-w-md w-full text-center">
        <h1 className="text-2xl font-bold mb-2">Deepfake Detector</h1>
        <p className="text-gray-500 mb-6 text-sm">Upload a video to analyze authenticity</p>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-blue-400 transition-colors">
            <input 
              type="file" 
              accept="video/*" 
              className="hidden" 
              id="video-upload"
              onChange={(e) => setFile(e.target.files[0])}
            />
            <label htmlFor="video-upload" className="cursor-pointer flex flex-col items-center">
              <Upload className="w-10 h-10 text-gray-400 mb-2" />
              <span className="text-sm text-gray-600">
                {file ? file.name : "Click to select a video"}
              </span>
            </label>
          </div>

          <button 
            disabled={!file || loading}
            className="w-full bg-blue-600 text-white py-2 rounded-lg font-semibold disabled:bg-gray-400 flex items-center justify-center gap-2"
          >
            {loading ? <Loader2 className="animate-spin" /> : "Run Analysis"}
          </button>
        </form>

        {result && (
          <div className={`mt-8 p-4 rounded-lg border ${result.is_fake ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
            <div className="flex items-center justify-center mb-2">
              {result.is_fake ? <ShieldAlert className="text-red-600" /> : <ShieldCheck className="text-green-600" />}
            </div>
            <h2 className={`text-xl font-bold ${result.is_fake ? 'text-red-700' : 'text-green-700'}`}>
              {result.prediction}
            </h2>
            <p className="text-sm text-gray-600 mt-1">Confidence: {result.confidence}</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;