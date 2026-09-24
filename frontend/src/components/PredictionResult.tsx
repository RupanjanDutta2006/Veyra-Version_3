import React from 'react';
import { PredictionResponse, RiskLevel, DataSourceMode } from '../api/types';

interface PredictionResultProps {
  prediction: PredictionResponse;
}

function normalizeTrustState(trust: any): 'NORMAL' | 'UNUSUAL' | 'OOD' | 'ABSTAIN' {
  if (!trust) return 'NORMAL';
  const str = String(trust).toUpperCase();
  if (str === 'ABSTAIN' || str === 'ABSTAINED') return 'ABSTAIN';
  if (str === 'OOD' || str === 'OUT_OF_DISTRIBUTION') return 'OOD';
  if (str === 'UNUSUAL' || str === 'LOW_CONFIDENCE') return 'UNUSUAL';
  if (str === 'NORMAL' || str === 'HIGH_CONFIDENCE' || str === 'MODERATE_CONFIDENCE') return 'NORMAL';
  return 'NORMAL';
}

function getTrustBannerDetails(state: 'NORMAL' | 'UNUSUAL' | 'OOD' | 'ABSTAIN') {
  switch (state) {
    case 'ABSTAIN':
      return {
        title: 'I don\'t know — human review required.',
        subtitle: 'The safety and abstention layer rejected automated scoring to prevent deceptive overconfidence.',
        badgeClass: 'trust-abstain',
        bg: '#f1f5f9',
        border: '#64748b',
        color: '#334155',
        icon: (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748b" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" />
            <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
          </svg>
        ),
      };
    case 'OOD':
      return {
        title: 'Out-Of-Distribution (OOD) Detected',
        subtitle: 'Atmospheric state or feature distance exceeds training distribution boundaries. Proceed with elevated caution.',
        badgeClass: 'trust-ood',
        bg: '#fff7ed',
        border: '#ea580c',
        color: '#9a3412',
        icon: (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ea580c" strokeWidth="2.5">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        ),
      };
    case 'UNUSUAL':
      return {
        title: 'Unusual Atmospheric Regime',
        subtitle: 'Forecast state exhibits elevated variance or regime novelty. Broadened conformal prediction intervals applied.',
        badgeClass: 'trust-unusual',
        bg: '#fefce8',
        border: '#ca8a04',
        color: '#854d0e',
        icon: (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ca8a04" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        ),
      };
    case 'NORMAL':
    default:
      return {
        title: 'Nominal Operational State',
        subtitle: 'Inputs within verified meteorological distribution. Conformal calibration active with certified bounds.',
        badgeClass: 'trust-normal',
        bg: '#f0fdf4',
        border: '#16a34a',
        color: '#166534',
        icon: (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <polyline points="9 12 11 14 15 10" />
          </svg>
        ),
      };
  }
}

function getRiskClass(risk: RiskLevel | null, isAbstained: boolean): string {
  if (isAbstained) return 'risk-gray';
  if (!risk) return 'risk-low';
  switch (risk.toUpperCase()) {
    case 'LOW':
      return 'risk-low';
    case 'MEDIUM':
      return 'risk-medium';
    case 'HIGH':
      return 'risk-high';
    case 'CRITICAL':
      return 'risk-critical';
    case 'GRAY':
      return 'risk-gray';
    default:
      return 'risk-low';
  }
}

/** Phase 08: Data source provenance badge for trust disclosure. */
function getDataSourceBadge(mode: DataSourceMode | null | undefined): { label: string; icon: string; bg: string; color: string } {
  switch (mode) {
    case 'LIVE':
      return { label: 'Live', icon: '🟢', bg: '#dcfce7', color: '#166534' };
    case 'FIXTURE':
      return { label: 'Fixture', icon: '🔵', bg: '#dbeafe', color: '#1e40af' };
    case 'SYNTHETIC':
      return { label: 'Synthetic', icon: '🟣', bg: '#f3e8ff', color: '#6b21a8' };
    case 'CACHED':
      return { label: 'Cached', icon: '🟡', bg: '#fef9c3', color: '#854d0e' };
    case 'FALLBACK':
      return { label: 'Fallback', icon: '🟠', bg: '#ffedd5', color: '#9a3412' };
    case 'UNAVAILABLE':
      return { label: 'Unavailable', icon: '⚫', bg: '#f1f5f9', color: '#334155' };
    default:
      return { label: 'Live', icon: '🟢', bg: '#dcfce7', color: '#166534' };
  }
}

export const PredictionResult: React.FC<PredictionResultProps> = ({ prediction }) => {
  const {
    location,
    bust_probability,
    risk_level,
    trust_state,
    abstain,
    reason_codes,
    model_version,
    confidence_index,
    uncertainty_pct,
    ood_score,
    lead_hours,
  } = prediction;

  const dataSourceMode = (prediction as any).data_source_mode as DataSourceMode | null | undefined;
  const sourceBadge = getDataSourceBadge(dataSourceMode);

  const isAbstained = abstain || trust_state === 'ABSTAINED' || trust_state === ('ABSTAIN' as any);
  const normalizedState = isAbstained ? 'ABSTAIN' : normalizeTrustState(trust_state);
  const banner = getTrustBannerDetails(normalizedState);
  const riskClass = getRiskClass(risk_level, isAbstained);

  const percentage =
    !isAbstained && bust_probability !== null && bust_probability !== undefined
      ? (bust_probability * 100).toFixed(2)
      : null;

  return (
    <section className="hero-prob-card" aria-labelledby="prob-heading" aria-live="polite">
      {/* 1. Authoritative Trust Banner per §17, §20 */}
      <div
        role="alert"
        title="Operational Trust: Nominal Pipeline Integrity (valid location, QC passed, model loaded)"
        style={{
          background: banner.bg,
          border: `1.5px solid ${banner.border}`,
          borderRadius: '6px',
          padding: '12px 14px',
          marginBottom: '16px',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start',
        }}
      >
        <div style={{ flexShrink: 0, marginTop: '2px' }}>{banner.icon}</div>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 800, fontSize: '0.95rem', color: banner.color, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{banner.title}</span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 800,
                textTransform: 'uppercase',
                padding: '1px 6px',
                borderRadius: '3px',
                background: banner.border,
                color: '#ffffff',
              }}
            >
              {normalizedState}
            </span>
          </div>
          <div style={{ fontSize: '0.8rem', color: banner.color, opacity: 0.9, marginTop: '3px', lineHeight: '1.4' }}>
            {banner.subtitle}
          </div>

          {/* Phase 08: Data source provenance badge */}
          <div style={{ marginTop: '6px', display: 'flex', gap: '6px', alignItems: 'center' }}>
            <span
              style={{
                fontSize: '0.72rem',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '4px',
                background: sourceBadge.bg,
                color: sourceBadge.color,
              }}
              title={`Data source: ${sourceBadge.label}`}
            >
              {sourceBadge.icon} {sourceBadge.label}
            </span>
            {prediction.data_version && (
              <span
                style={{
                  fontSize: '0.68rem',
                  fontFamily: 'monospace',
                  color: '#64748b',
                  padding: '1px 6px',
                  background: 'rgba(0,0,0,0.04)',
                  borderRadius: '3px',
                }}
              >
                {prediction.data_version}
              </span>
            )}
          </div>

          {/* If Abstained or OOD, show reason codes */}
          {isAbstained && reason_codes && reason_codes.length > 0 && (
            <div style={{ marginTop: '8px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              {reason_codes.map((rc) => (
                <span
                  key={rc}
                  style={{
                    fontSize: '0.72rem',
                    fontFamily: 'monospace',
                    background: 'rgba(0,0,0,0.08)',
                    padding: '2px 6px',
                    borderRadius: '4px',
                    color: banner.color,
                    fontWeight: 700,
                  }}
                >
                  {rc}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 2. Calibrated Probability or Explicit Abstention Placeholder */}
      <div className="prob-metric-title" id="prob-heading">
        {isAbstained ? 'Automated Scoring Abstained' : 'Calibrated Bust Probability (q95 MAD)'}
      </div>

      {isAbstained ? (
        <div
          style={{
            fontSize: '1.6rem',
            fontWeight: 800,
            color: '#64748b',
            padding: '14px 0',
            fontFamily: 'monospace',
            letterSpacing: '0.02em',
          }}
        >
          [HUMAN REVIEW REQUIRED]
        </div>
      ) : (
        <div className={`prob-value-large ${riskClass}`} aria-label={`Bust probability: ${percentage} percent`}>
          {percentage}%
        </div>
      )}

      {/* Summary Narrative */}
      <p className="prob-summary-text">
        {isAbstained ? (
          <>
            Atmospheric forecast reliability evaluation for{' '}
            <strong style={{ color: 'var(--text-primary)' }}>{location}</strong> requires manual forecaster review.
            Do not make automated operational decisions using uncalibrated predictions.
          </>
        ) : (
          <>
            Estimated calibrated probability that the forecast for{' '}
            <strong style={{ color: 'var(--text-primary)' }}>{location}</strong> will exceed the stratum-specific 95th percentile error threshold at {lead_hours ?? 48}h lead.
          </>
        )}
      </p>

      {/* Meta Badges */}
      <div className="meta-badges-row">
        {/* Risk Band Badge (5-Tier: GREEN, YELLOW, ORANGE, RED, GRAY) */}
        <div
          className={`risk-badge ${riskClass}`}
          role="status"
          style={{
            background: isAbstained ? '#64748b' : undefined,
            color: isAbstained ? '#ffffff' : undefined,
          }}
        >
          <span>Risk Band: {isAbstained ? 'GRAY (ABSTAIN)' : risk_level || 'LOW'}</span>
        </div>

        {/* Model Version */}
        <div className="version-badge">
          <span>Model: {model_version || 'veyra-v3'}</span>
        </div>

        {/* OOD Score if available */}
        {ood_score != null && (
          <div className="version-badge" title="Feature-distance and regime novelty score in [0.0, 1.0]">
            <span>OOD Score: {ood_score.toFixed(3)}</span>
          </div>
        )}

        {/* Conformal Uncertainty */}
        {uncertainty_pct != null && !isAbstained && (
          <div className="version-badge">
            <span>±{uncertainty_pct.toFixed(1)}% (90% Conformal)</span>
          </div>
        )}

        {/* Heuristic Decision Certainty Badge */}
        {confidence_index !== null && confidence_index !== undefined && !isAbstained && (
          <div
            className="version-badge"
            title="Probability Separation Score: 2*|P - 0.5| (heuristic distance from boundary ambiguity; not a formal statistical confidence interval)"
          >
            <span>Certainty: {(confidence_index * 100).toFixed(1)}%</span>
          </div>
        )}

        {/* Boundary Ambiguity Badge */}
        {uncertainty_pct !== null && uncertainty_pct !== undefined && !isAbstained && (
          <div
            className="version-badge"
            title="Decision Boundary Ambiguity: proximity to 0.5 threshold (not a formal predictive uncertainty interval)"
          >
            <span>Ambiguity: {uncertainty_pct.toFixed(1)}%</span>
          </div>
        )}

        {/* Scientific Certification Badge */}
        {prediction.certification && (
          <div
            className={`trust-badge cert-badge ${
              prediction.certification.certification_status === 'CERTIFIED'
                ? 'cert-certified'
                : prediction.certification.certification_status === 'OUTSIDE_CERTIFIED_SCOPE'
                ? 'cert-outside'
                : 'cert-unknown'
            }`}
            role="status"
            aria-label={`Scientific Certification: ${prediction.certification.certification_status}`}
            title={`Scientific Certification (${prediction.certification.certification_policy_version}): ${prediction.certification.certification_reason}`}
            style={{
              borderColor:
                prediction.certification.certification_status === 'CERTIFIED'
                  ? '#10b981'
                  : prediction.certification.certification_status === 'OUTSIDE_CERTIFIED_SCOPE'
                  ? '#f59e0b'
                  : '#ef4444',
              color:
                prediction.certification.certification_status === 'CERTIFIED'
                  ? '#059669'
                  : prediction.certification.certification_status === 'OUTSIDE_CERTIFIED_SCOPE'
                  ? '#d97706'
                  : '#dc2626',
              fontWeight: 600,
            }}
          >
            <span>
              {prediction.certification.certification_status === 'CERTIFIED'
                ? 'CERTIFIED EVIDENCE SCOPE'
                : prediction.certification.certification_status === 'OUTSIDE_CERTIFIED_SCOPE'
                ? 'OUTSIDE CERTIFIED EVIDENCE SCOPE'
                : 'CERTIFICATION UNKNOWN'}
            </span>
          </div>
        )}
      </div>
    </section>
  );
};

export default PredictionResult;
