function Explanation({ explanation }) {
  return (
    <section className="explanation-section">
      <h3>Explanation</h3>
      <div className="explanation-card">
        <p>{explanation}</p>
      </div>
    </section>
  );
}

export default Explanation;