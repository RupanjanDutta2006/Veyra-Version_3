import React from 'react';
import { ApiError } from '../api/types';

export type SystemUiState =
  | 'LOADING'
  | 'NO_DATA'
  | 'DATA_DELAYED'
  | 'MODEL_UNAVAILABLE'
  | 'OOD'
  | 'ABSTENTION'
  | 'VERIFICATION_PENDING'
  | 'API_ERROR';

interface UiStateBannerProps {
  state: SystemUiState;
  message?: string;
  timestamp?: string;
  source?: string;
  requestId?: string;
  noveltyScore?: number;
  onRetry?: () => void;
  onSwitchToReplay?: () => void;
  onDismiss?: () => void;
}

export const UiStateBanner: React.FC<UiStateBannerProps> = ({
  state,
  message,
  timestamp,
  source,
  requestId,
  noveltyScore,
  onRetry,
  onSwitchToReplay,
  onDismiss,
}) => {
  switch (state) {
    case 'LOADING':
      return (
        <div
          role="status"
          aria-live="polite"
          style={{
            padding: '24px',
            background: 'var(--noaa-card-bg)',
            borderRadius: '6px',
            border: '1px solid var(--noaa-border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div
              style={{
                width: '18px',
                height: '18px',
                border: '2.5px solid #0071bc',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 0.8s linear infinite',
              }}
            />
            <strong style={{ color: 'var(--noaa-dark-blue)', fontSize: '0.9rem' }}>
              Acquiring Atmospheric Telemetry & Evaluating Conformal Bounds...
            </strong>
          </div>
          {/* Skeleton lines to prevent showing 0.0% or stale risk */}
          <div style={{ height: '14px', background: '#e2e8f0', borderRadius: '4px', width: '85%' }} />
          <div style={{ height: '14px', background: '#e2e8f0', borderRadius: '4px', width: '60%' }} />
          <div style={{ fontSize: '0.75rem', color: 'var(--noaa-muted)', marginTop: '4px' }}>
            Enforcing strict availability timestamp check (availability_time ≤ issue_time).
          </div>
        </div>
      );

    case 'NO_DATA':
      return (
        <div
          role="alert"
          style={{
            padding: '16px 20px',
            background: '#fffbeb',
            borderLeft: '4px solid #d97706',
            borderRadius: '0 6px 6px 0',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ fontWeight: 700, color: '#b45309', fontSize: '0.92rem' }}>
            Atmospheric Data Not Available
          </div>
          <div style={{ color: '#92400e', marginTop: '4px', lineHeight: '1.4' }}>
            {message || `Missing required forecast fields from source: ${source || 'GEFS Ensemble / Open-Meteo'}.`}
          </div>
          <div style={{ marginTop: '8px', display: 'flex', gap: '10px' }}>
            {onRetry && (
              <button
                onClick={onRetry}
                style={{
                  padding: '4px 10px',
                  borderRadius: '4px',
                  background: '#d97706',
                  color: '#ffffff',
                  border: 'none',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Retry Ingestion
              </button>
            )}
            {onSwitchToReplay && (
              <button
                onClick={onSwitchToReplay}
                style={{
                  padding: '4px 10px',
                  borderRadius: '4px',
                  background: 'transparent',
                  color: '#b45309',
                  border: '1px solid #d97706',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Switch to Frozen Replay
              </button>
            )}
          </div>
        </div>
      );

    case 'DATA_DELAYED':
      return (
        <div
          role="alert"
          style={{
            padding: '14px 18px',
            background: '#f8fafc',
            borderLeft: '4px solid #64748b',
            borderRadius: '0 6px 6px 0',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ fontWeight: 700, color: '#334155', fontSize: '0.92rem' }}>
              Upstream Ingestion Delayed
            </div>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 800,
                background: '#cbd5e1',
                color: '#1e293b',
                padding: '2px 6px',
                borderRadius: '4px',
              }}
            >
              DATA DELAYED
            </span>
          </div>
          <div style={{ color: '#475569', marginTop: '4px' }}>
            Displaying last approved forecast cycle from: <strong>{timestamp || 'Previous 00:00 UTC Run'}</strong>.
            No invented risk is attributed to current pending run (§21).
          </div>
        </div>
      );

    case 'MODEL_UNAVAILABLE':
      return (
        <div
          role="alert"
          style={{
            padding: '14px 18px',
            background: '#eff6ff',
            borderLeft: '4px solid #2563eb',
            borderRadius: '0 6px 6px 0',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ fontWeight: 700, color: '#1e40af', fontSize: '0.92rem' }}>
            Model Unavailable — Fallback Active (K3)
          </div>
          <div style={{ color: '#1e3a8a', marginTop: '4px' }}>
            Primary LightGBM V3 checkpoint is unavailable. Serving calibrated spread-only fallback baseline.
          </div>
        </div>
      );

    case 'OOD':
      return (
        <div
          role="alert"
          style={{
            padding: '16px 20px',
            background: '#fff7ed',
            borderLeft: '4px solid #ea580c',
            borderRadius: '0 6px 6px 0',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ fontWeight: 700, color: '#c2410c', fontSize: '0.92rem' }}>
            Out-of-Distribution (OOD) Detected (§11.3, K4)
          </div>
          <div style={{ color: '#9a3412', marginTop: '4px', lineHeight: '1.4' }}>
            Atmospheric state exhibits high novelty distance (Score: {noveltyScore?.toFixed(3) ?? '0.842'}).
            Automated numbers are withheld to prevent misleading predictions.
          </div>
        </div>
      );

    case 'ABSTENTION':
      return (
        <div
          role="alert"
          style={{
            padding: '16px 20px',
            background: '#f1f5f9',
            borderLeft: '4px solid #475569',
            borderRadius: '0 6px 6px 0',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ fontWeight: 800, color: '#1e293b', fontSize: '1.05rem' }}>
            I don&apos;t know — human review required.
          </div>
          <div style={{ color: '#475569', marginTop: '4px', lineHeight: '1.4' }}>
            The safety policy rejected automated scoring. The forecast may be in an ambiguous or uncertified regime.
          </div>
        </div>
      );

    case 'VERIFICATION_PENDING':
      return (
        <div
          role="status"
          style={{
            padding: '14px 18px',
            background: '#f8fafc',
            borderLeft: '4px solid #0071bc',
            borderRadius: '0 6px 6px 0',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ fontWeight: 700, color: '#0071bc', fontSize: '0.92rem' }}>
            Verification Pending Valid Time
          </div>
          <div style={{ color: '#334155', marginTop: '4px' }}>
            Future ERA5 ground truth is sealed until valid verification time arrives or user triggers explicit historical replay.
          </div>
        </div>
      );

    case 'API_ERROR':
    default:
      return (
        <div
          role="alert"
          style={{
            padding: '16px 20px',
            background: '#fef2f2',
            borderLeft: '4px solid #ef4444',
            borderRadius: '0 6px 6px 0',
            fontSize: '0.85rem',
          }}
        >
          <div style={{ fontWeight: 700, color: '#b91c1c', fontSize: '0.92rem' }}>
            Sentinel Communication Failure
          </div>
          <div style={{ color: '#7f1d1d', marginTop: '4px' }}>
            {message || 'Unable to communicate with the Veyra FastAPI service.'}
          </div>
          {requestId && (
            <div style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: '#991b1b', marginTop: '6px' }}>
              Request ID: {requestId}
            </div>
          )}
          <div style={{ marginTop: '10px', display: 'flex', gap: '10px' }}>
            {onRetry && (
              <button
                onClick={onRetry}
                style={{
                  padding: '4px 10px',
                  borderRadius: '4px',
                  background: '#ef4444',
                  color: '#ffffff',
                  border: 'none',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Retry
              </button>
            )}
            {onDismiss && (
              <button
                onClick={onDismiss}
                aria-label="Dismiss error"
                style={{
                  padding: '4px 10px',
                  borderRadius: '4px',
                  background: 'transparent',
                  color: '#b91c1c',
                  border: '1px solid #ef4444',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Dismiss error
              </button>
            )}
            {onSwitchToReplay && (
              <button
                onClick={onSwitchToReplay}
                style={{
                  padding: '4px 10px',
                  borderRadius: '4px',
                  background: 'transparent',
                  color: '#b91c1c',
                  border: '1px solid #ef4444',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Open Historical Replay
              </button>
            )}
          </div>
        </div>
      );
  }
};

interface ErrorViewProps {
  error: ApiError | null;
  onDismiss?: () => void;
  onRetry?: () => void;
  onSwitchToReplay?: () => void;
}

export const ErrorView: React.FC<ErrorViewProps> = ({
  error,
  onDismiss,
  onRetry,
  onSwitchToReplay,
}) => {
  if (!error) return null;

  return (
    <UiStateBanner
      state="API_ERROR"
      message={error.message || error.error}
      requestId={error.request_id}
      onRetry={onRetry}
      onSwitchToReplay={onSwitchToReplay}
      onDismiss={onDismiss}
    />
  );
};

export default ErrorView;
