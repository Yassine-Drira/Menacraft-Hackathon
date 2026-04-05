import { useState, useEffect } from 'react';

const stages = [
  'Running CLIP gate...',
  'Analysing image...',
  'Extracting entities...',
  'Building verdict...'
];

function LoadingState() {
  const [currentStage, setCurrentStage] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentStage((prev) => (prev + 1) % stages.length);
    }, 1500);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="loading-section">
      <div className="loading-spinner"></div>
      <p className="loading-text">{stages[currentStage]}</p>
    </section>
  );
}

export default LoadingState;