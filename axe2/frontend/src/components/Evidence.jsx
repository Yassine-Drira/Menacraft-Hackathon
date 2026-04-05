function Evidence({ evidence }) {
  if (!evidence || evidence.length === 0) {
    return null;
  }

  return (
    <section className="evidence-section">
      <h3>Web Evidence</h3>
      <p className="evidence-intro">Sources found for this claim:</p>

      <div className="evidence-list">
        {evidence.map((item, index) => (
          <article key={index} className="evidence-item">
            <h4>
              <a href={item.url} target="_blank" rel="noopener noreferrer">
                {item.title || item.url}
              </a>
            </h4>
            <p className="evidence-snippet">{item.snippet}</p>
            {item.relevance_score !== undefined && (
              <small className="relevance-score">
                Relevance: {item.relevance_score}
              </small>
            )}
          </article>
        ))}
      </div>
    </section>
  );
}

export default Evidence;