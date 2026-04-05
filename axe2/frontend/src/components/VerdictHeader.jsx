function VerdictHeader({ result }) {
  const getVerdictClass = (verdict) => {
    switch (verdict) {
      case 'CONSISTENT':
        return 'verdict-consistent';
      case 'SUSPICIOUS':
        return 'verdict-suspicious';
      case 'MISMATCH':
        return 'verdict-mismatch';
      default:
        return 'verdict-gray';
    }
  };

  const getScoreColor = (score) => {
    if (score >= 70) return '#10b981'; // green
    if (score >= 35) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };

  return (
    <section className="verdict-header">
      <div className="score-display">
        <div className="score-gauge">
          <div
            className="score-fill"
            style={{ width: `${result.score}%`, backgroundColor: getScoreColor(result.score) }}
          ></div>
        </div>
        <div className="score-text">
          <span className="score-number">{result.score}</span>
          <span className="score-label">/100</span>
        </div>
      </div>

      <div className="verdict-info">
        <span className={`verdict-badge ${getVerdictClass(result.verdict)}`}>
          {result.verdict}
        </span>
        {result.early_exit && (
          <p className="early-exit-notice">
            Verdict reached at screening stage — image and caption are semantically unrelated.
          </p>
        )}
      </div>
    </section>
  );
}

export default VerdictHeader;