const flagDescriptions = {
  semantic_mismatch: 'Image and caption are semantically unrelated',
  location_mismatch: 'Location could not be confirmed in image',
  temporal_claim_unverifiable: 'Caption makes a time claim that cannot be verified visually',
  event_type_mismatch: 'Event type in caption does not match what the image shows',
  overclaiming_specificity: 'Caption makes multiple specific claims unsupported by the image',
  evidence_contradicts_claim: 'Search results suggest the claim is inaccurate'
};

function FlagChips({ flags }) {
  if (!flags || flags.length === 0) {
    return (
      <section className="flags-section">
        <h3>Issues Detected</h3>
        <div className="no-flags">
          <span className="flag-chip flag-none">No issues detected</span>
        </div>
      </section>
    );
  }

  return (
    <section className="flags-section">
      <h3>Issues Detected</h3>
      <div className="flags-list">
        {flags.map((flag) => (
          <div key={flag} className="flag-item">
            <span className="flag-chip flag-issue">{flag.replace(/_/g, ' ')}</span>
            <p className="flag-description">{flagDescriptions[flag] || 'Unknown issue'}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

export default FlagChips;