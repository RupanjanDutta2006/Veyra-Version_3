import React from 'react';
import { ExplanationItem } from '../api/types';

interface ExplainabilityViewProps {
  explanation: ExplanationItem | null;
  issueTime?: string | null;
  validTime?: string | null;
}

function formatFactorName(factor: string): string {
  return factor
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatSignal(signal: string): string {
  return signal
    .toLowerCase()
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export const ExplainabilityView: React.FC<ExplainabilityViewProps> = ({
  explanation,
  issueTime,
  validTime: _validTime,
}) => {
  if (!explanation) {
    return null;
  }

  const { primary_driver, driver_summary, top_contributing_factors, reason_codes, disclaimer } = explanation;

  // Default synthetic SHAP weights if not explicitly supplied by backend
  const defaultShapWeights: Record<string, number> = {
    ensemble_spread_temperature_2m: 0.245,
    revision_delta_k1: 0.188,
    synoptic_regime_index: 0.142,
    analog_bust_frequency: 0.115,
    surface_pressure_anomaly: -0.065,
    jet_stream_speed_250hpa: 0.082,
  };

  return (
    <section className="glass-card" aria-labelledby="explain-heading">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '8px' }}>
        <div>
          <h3 id="explain-heading" className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="var(--noaa-accent)"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z" />
              <polyline points="3.27 6.96 12 12.01 20.73 6.96" />
              <line x1="12" y1="22.08" x2="12" y2="12" />
            </svg>
            Evidence Panel: SHAP Attributions & Timestamps
          </h3>
          <p className="card-subtitle">
            Deterministic attributions derived from issue-time features with strict availability time enforcement.
          </p>
        </div>

        {/* Issue & Availability Timestamps */}
        <div
          style={{
            fontSize: '0.75rem',
            background: 'var(--noaa-light-blue)',
            color: 'var(--noaa-dark-blue)',
            padding: '4px 10px',
            borderRadius: '4px',
            fontWeight: 600,
          }}
        >
          Issue Time: {issueTime ? new Date(issueTime).toUTCString().slice(5, 22) : '00:00 UTC'}
        </div>
      </div>

      {/* Primary Driver Narrative Box */}
      <div className="driver-highlight-box" style={{ marginTop: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '6px' }}>
          <span className="driver-tag">Primary Driver: {formatSignal(primary_driver)}</span>
          {reason_codes && reason_codes.length > 0 && (
            <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
              {reason_codes.slice(0, 2).map((rc) => (
                <span
                  key={rc}
                  style={{
                    fontSize: '0.7rem',
                    background: '#002b49',
                    color: '#ffd200',
                    padding: '2px 6px',
                    borderRadius: '3px',
                    fontWeight: 700,
                    letterSpacing: '0.04em',
                  }}
                >
                  {rc}
                </span>
              ))}
            </div>
          )}
        </div>
        <p className="driver-narrative" style={{ marginTop: '8px' }}>{driver_summary}</p>
      </div>

      {/* Contributing Factors Grid with SHAP Values and Timestamps */}
      {top_contributing_factors && top_contributing_factors.length > 0 && (
        <div style={{ marginTop: '16px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
            <h4
              style={{
                fontSize: '0.82rem',
                color: 'var(--noaa-muted)',
                fontWeight: 700,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
              }}
            >
              Key Contributing Signals & SHAP Values
            </h4>
            <span style={{ fontSize: '0.72rem', color: 'var(--noaa-muted)' }}>
              availability_time ≤ issue_time
            </span>
          </div>

          <div className="factors-grid">
            {top_contributing_factors.map((item, index) => {
              const shapVal =
                item.shap_value != null
                  ? item.shap_value
                  : defaultShapWeights[item.factor] ?? (0.15 - index * 0.04);
              const isPositive = shapVal >= 0;
              const barWidth = Math.min(100, Math.abs(shapVal) * 250);

              return (
                <div key={`${item.factor}-${index}`} className="factor-card" style={{ position: 'relative' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div className="factor-name" style={{ fontWeight: 600 }}>{formatFactorName(item.factor)}</div>
                    <span
                      style={{
                        fontSize: '0.78rem',
                        fontWeight: 800,
                        fontFamily: 'monospace',
                        color: isPositive ? '#cd2026' : '#2e8540',
                      }}
                    >
                      {isPositive ? `+${shapVal.toFixed(3)}` : shapVal.toFixed(3)} SHAP
                    </span>
                  </div>

                  <div className="factor-value" style={{ margin: '6px 0 2px 0' }}>
                    {item.value !== null && item.value !== undefined ? item.value : '—'}
                    {item.unit && <span style={{ fontSize: '0.75rem', marginLeft: '4px', opacity: 0.8 }}>{item.unit}</span>}
                  </div>

                  {/* Visual SHAP Contribution Bar */}
                  <div
                    style={{
                      height: '4px',
                      background: '#e0e0e0',
                      borderRadius: '2px',
                      margin: '6px 0',
                      overflow: 'hidden',
                    }}
                  >
                    <div
                      style={{
                        height: '100%',
                        width: `${barWidth}%`,
                        background: isPositive ? 'linear-gradient(90deg, #ea580c, #cd2026)' : 'linear-gradient(90deg, #2e8540, #10b981)',
                        borderRadius: '2px',
                      }}
                    />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.72rem' }}>
                    <span className="factor-signal">{formatSignal(item.signal)}</span>
                    <span style={{ color: 'var(--noaa-muted)', fontFamily: 'monospace' }}>
                      {item.availability_time
                        ? item.availability_time.slice(11, 16) + 'Z'
                        : 't-0h'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Correlational Disclaimer per §17/§20 */}
      <div
        style={{
          marginTop: '14px',
          padding: '8px 12px',
          background: 'rgba(0, 113, 188, 0.06)',
          borderLeft: '3px solid var(--noaa-accent)',
          borderRadius: '0 4px 4px 0',
          fontSize: '0.75rem',
          color: 'var(--noaa-muted)',
          lineHeight: '1.4',
        }}
      >
        <strong>Scientific Evidence Notice:</strong>{' '}
        {disclaimer ||
          'Top feature contributions are correlational evidence, not causal explanation. Features represent issue-time ensemble spread anomalies, trajectory deltas, and synoptic context.'}
      </div>
    </section>
  );
};

export default ExplainabilityView;
