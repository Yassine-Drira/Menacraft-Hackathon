function AnalysisDetail({ result }) {
  if (result.early_exit) {
    return null; // Don't show analysis detail for early exit
  }

  const clipScoreValue = typeof result.clip_score === 'number'
    ? result.clip_score
    : (result.clip_score?.normalized ?? (result.clip_score?.display ?? 0) / 100);

  return (
    <section className="analysis-section">
      <h3>Analysis Details</h3>

      <div className="analysis-grid">
        <div className="analysis-item">
          <h4>CLIP Score</h4>
          <div className="clip-score">
            <div className="clip-bar">
              <div
                className="clip-fill"
                style={{ width: `${clipScoreValue * 100}%` }}
              ></div>
            </div>
            <span className="clip-value">{clipScoreValue.toFixed(2)}</span>
          </div>
        </div>

        {result.blip_description && (
          <div className="analysis-item">
            <h4>BLIP Description</h4>
            <p className="blip-text">"{result.blip_description}"</p>
          </div>
        )}

        {result.entities && (
          <>
            <div className="analysis-item">
              <h4>Locations</h4>
              <p>{result.entities.locations.length > 0 ? result.entities.locations.join(', ') : 'None detected'}</p>
            </div>

            <div className="analysis-item">
              <h4>Dates</h4>
              <p>{result.entities.dates.length > 0 ? result.entities.dates.join(', ') : 'None detected'}</p>
            </div>

            <div className="analysis-item">
              <h4>Events</h4>
              <p>{result.entities.events.length > 0 ? result.entities.events.join(', ') : 'None detected'}</p>
            </div>
          </>
        )}
      </div>
    </section>
  );
}

export default AnalysisDetail;