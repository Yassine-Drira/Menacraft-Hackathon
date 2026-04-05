import { useState } from 'react';

function UploadForm({ onSubmit, disabled }) {
  const [file, setFile] = useState(null);
  const [caption, setCaption] = useState('');
  const [searchEnabled, setSearchEnabled] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (file && caption.trim()) {
      onSubmit(file, caption.trim(), searchEnabled);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    setFile(selectedFile);
  };

  return (
    <section className="upload-section">
      <h2>Upload media and caption</h2>
      <form onSubmit={handleSubmit} className="upload-form">
        <div className="file-input">
          <label htmlFor="media-file">Select image or video</label>
          <input
            id="media-file"
            type="file"
            accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime"
            onChange={handleFileChange}
            disabled={disabled}
          />
          {file && <p className="file-name">Selected: {file.name}</p>}
        </div>

        <div className="caption-input">
          <label htmlFor="caption">Caption / Claim</label>
          <textarea
            id="caption"
            value={caption}
            onChange={(e) => setCaption(e.target.value)}
            placeholder="Paste the post caption or claim here..."
            rows={4}
            disabled={disabled}
            maxLength={2000}
          />
          <small>{caption.length}/2000 characters</small>
        </div>

        <div className="search-toggle">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={searchEnabled}
              onChange={(e) => setSearchEnabled(e.target.checked)}
              disabled={disabled}
            />
            Enable evidence search (DuckDuckGo)
          </label>
        </div>

        <button
          type="submit"
          className="submit-button"
          disabled={disabled || !file || !caption.trim()}
        >
          {disabled ? 'Verifying...' : 'Verify now'}
        </button>
      </form>
    </section>
  );
}

export default UploadForm;