import React, { useState } from 'react';
import { ExternalLink, RefreshCw, Shield, FileText, CheckCircle2 } from 'lucide-react';

const DOCS_URL = 'http://127.0.0.1:8000/docs';

export const ApiDocsView: React.FC = () => {
  const [iframeKey, setIframeKey] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const handleRefresh = () => {
    setIsLoading(true);
    setIframeKey((prev) => prev + 1);
  };

  return (
    <div className="api-docs-container" role="region" aria-label="Embedded API Documentation">
      {/* Top Controls Toolbar */}
      <div className="api-docs-toolbar">
        <div className="api-docs-toolbar-left">
          <FileText size={18} className="api-docs-icon" />
          <div>
            <h2 className="api-docs-title">Forecast-Bust Sentinel API — Swagger UI</h2>
            <div className="api-docs-subtitle">
              OpenAPI 3.1 Specification &bull; http://127.0.0.1:8000/docs
            </div>
          </div>
        </div>

        <div className="api-docs-toolbar-right">
          <span className="api-docs-badge">
            <CheckCircle2 size={12} /> Live Swagger UI
          </span>
          <button
            type="button"
            className="api-docs-btn"
            onClick={handleRefresh}
            title="Reload Documentation"
            aria-label="Reload Documentation"
          >
            <RefreshCw size={14} className={isLoading ? 'spin' : ''} />
            <span className="btn-label">Reload</span>
          </button>
          <a
            href={DOCS_URL}
            target="_blank"
            rel="noreferrer"
            className="api-docs-btn primary"
            title="Open in New Tab"
            aria-label="Open documentation in new tab"
          >
            <ExternalLink size={14} />
            <span className="btn-label">Open in New Tab</span>
          </a>
        </div>
      </div>

      {/* Embedded Iframe Frame */}
      <div className="api-docs-frame-wrapper">
        {isLoading && (
          <div className="api-docs-loading-overlay">
            <div className="api-docs-spinner" />
            <div style={{ marginTop: '12px', fontSize: '0.85rem', fontWeight: 600, color: 'var(--noaa-dark-blue)' }}>
              Loading Interactive API Documentation...
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--noaa-muted)', marginTop: '4px' }}>
              Connecting to <code>{DOCS_URL}</code>
            </div>
          </div>
        )}
        <iframe
          key={iframeKey}
          src={DOCS_URL}
          title="Veyra Sentinel API Interactive Documentation"
          className="api-docs-iframe"
          onLoad={() => setIsLoading(false)}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
        />
      </div>

      {/* Bottom Information Footer */}
      <div className="api-docs-info-banner">
        <Shield size={14} style={{ flexShrink: 0, color: 'var(--noaa-accent)' }} />
        <span>
          Includes complete endpoints for <code>POST /v1/dashboard/intelligence</code>,{' '}
          <code>POST /v1/predict</code>, <code>POST /v1/predict/batch</code>, and{' '}
          <code>GET /v1/health</code> with full JSON schema contracts and interactive test runners.
        </span>
      </div>
    </div>
  );
};

export default ApiDocsView;
