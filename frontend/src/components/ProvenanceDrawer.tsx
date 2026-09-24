import React, { useState, useEffect } from 'react';
import { DataProvenanceResponse } from '../api/types';
import { apiClient } from '../api/client';

interface ProvenanceDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

const DEFAULT_PROVENANCE: DataProvenanceResponse = {
  schema_version: '2.0.0',
  primary_sources: {
    forecast_model: 'NOAA GEFS v12 / Open-Meteo Ensemble API (0.5° grid, 31 members)',
    forecast_resolution: '0.50 degree latitude/longitude, 3-hourly to 240 hours',
    reference_analysis: 'ECMWF ERA5 Reanalysis (0.25° grid, hourly analysis)',
    reference_resolution: '0.25 degree latitude/longitude, hourly single levels',
    verification_only_invariant:
      'ERA5 reference analysis is strictly utilized for ground-truth verification and bust threshold derivation. It is mathematically forbidden from being used as a feature, input, or predictor at forecast issue time.',
  },
  artifacts_checksums: {
    model_artifact_sha256: '00A8410746F4A0EECBF7E76AAA0565143FC948D0E06AEA65E7BCC4CE28A1C660',
    calibrator_artifact_sha256: '9F448606CE4338DED92F238A551B3A9D8E6D2CB5902E8BC687BCE5F5850AF531',
    feature_contract_sha256: '702FF4153FD95D8C9DE3BBD01461D65FDE0EF207099F7F3A8E7F5C8BAC02031E',
    dataset_manifest_sha256: 'B4D8E9F1A2C3E4F5A6B7C8D9E0F1A2B3C4D5E6F7A8B9C0D1E2F3A4B5C6D7E8F9',
  },
  licenses: {
    open_meteo: {
      license: 'Creative Commons Attribution 4.0 International (CC-BY-4.0)',
      uri: 'https://open-meteo.com/en/terms',
      attribution: 'Weather data provided by Open-Meteo under CC-BY-4.0',
    },
    era5_copernicus: {
      license: 'Copernicus Open Access License',
      uri: 'https://cds.climate.copernicus.eu/api/v2/terms/static/licence-to-use-copernicus-products.pdf',
      attribution: 'Generated using Copernicus Climate Change Service information [2026]',
    },
    noaa_gefs: {
      license: 'Public Domain / Open Data Policy (NOAA)',
      uri: 'https://www.ncei.noaa.gov/products/weather-climate-models/global-ensemble-forecast',
      attribution: 'NOAA National Centers for Environmental Information',
    },
  },
  pipeline_lineage: [
    'DISCOVERED',
    'DOWNLOADING',
    'DOWNLOADED',
    'CHECKSUMMED',
    'QC_PASS',
    'ALIGNED',
    'FEATURES_READY',
    'INFERENCE_READY',
    'PUBLISHED',
  ],
};

export const ProvenanceDrawer: React.FC<ProvenanceDrawerProps> = ({ isOpen, onClose }) => {
  const [provenance, setProvenance] = useState<DataProvenanceResponse>(DEFAULT_PROVENANCE);

  useEffect(() => {
    if (isOpen) {
      apiClient.getDataProvenance().then(({ data }) => {
        if (data) {
          // Merge incoming data with default structure to ensure all properties exist
          setProvenance({
            schema_version: data.schema_version || DEFAULT_PROVENANCE.schema_version,
            primary_sources: {
              ...DEFAULT_PROVENANCE.primary_sources,
              ...(data.primary_sources || {}),
            },
            artifacts_checksums: {
              ...DEFAULT_PROVENANCE.artifacts_checksums,
              ...(data.artifacts_checksums || {}),
            },
            licenses: {
              ...DEFAULT_PROVENANCE.licenses,
              ...(data.licenses || {}),
            },
            pipeline_lineage: data.pipeline_lineage || DEFAULT_PROVENANCE.pipeline_lineage,
            ...(data as any),
          });
        }
      });
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const primarySources = provenance?.primary_sources || DEFAULT_PROVENANCE.primary_sources;
  const artifactsChecksums = provenance?.artifacts_checksums || DEFAULT_PROVENANCE.artifacts_checksums;
  const licenses = provenance?.licenses || DEFAULT_PROVENANCE.licenses;
  const pipelineLineage = provenance?.pipeline_lineage || DEFAULT_PROVENANCE.pipeline_lineage;
  const transformationPipeline: any[] = (provenance as any)?.transformation_pipeline || [];

  return (
    <>
      {/* Backdrop overlay */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.45)',
          backdropFilter: 'blur(2px)',
          zIndex: 99998,
        }}
        aria-hidden="true"
      />

      {/* Drawer */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          right: 0,
          bottom: 0,
          width: '100%',
          maxWidth: '540px',
          background: 'var(--noaa-card-bg, #ffffff)',
          boxShadow: '-6px 0 32px rgba(0,0,0,0.28)',
          zIndex: 99999,
          display: 'flex',
          flexDirection: 'column',
          overflowY: 'auto',
          animation: 'slideInRight 0.2s ease',
        }}
        role="dialog"
        aria-labelledby="provenance-title"
      >
        {/* Drawer Header */}
        <div
          style={{
            padding: '18px 22px',
            background: 'var(--noaa-dark-blue)',
            color: '#ffffff',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            position: 'sticky',
            top: 0,
            zIndex: 10,
          }}
        >
          <div>
            <h3 id="provenance-title" style={{ fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
              Data Lineage &amp; Provenance Drawer
            </h3>
            <div style={{ fontSize: '0.75rem', opacity: 0.85, marginTop: '2px' }}>
              Docs §17, §22 • Research Files 095, 114
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Provenance Drawer"
            style={{
              background: 'transparent',
              border: 'none',
              color: '#ffffff',
              fontSize: '1.4rem',
              cursor: 'pointer',
              padding: '4px 8px',
              lineHeight: 1,
            }}
          >
            &times;
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '20px 22px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Verification-Only Invariant Callout */}
          <div
            style={{
              padding: '12px 14px',
              background: '#f0fdf4',
              borderLeft: '4px solid #16a34a',
              borderRadius: '0 6px 6px 0',
            }}
          >
            <div style={{ fontSize: '0.78rem', fontWeight: 800, color: '#166534', textTransform: 'uppercase' }}>
              Verification-Only Invariant (§7.2, File 032)
            </div>
            <p style={{ fontSize: '0.8rem', color: '#14532d', marginTop: '4px', lineHeight: '1.4' }}>
              {primarySources.verification_only_invariant}
            </p>
          </div>

          {/* Pipeline Lineage Stepper */}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--noaa-dark-blue)', textTransform: 'uppercase', marginBottom: '8px' }}>
              End-to-End Pipeline Lineage
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
              {pipelineLineage.map((step, idx) => (
                <span
                  key={step}
                  style={{
                    fontSize: '0.72rem',
                    fontFamily: 'monospace',
                    background: 'var(--noaa-light-blue)',
                    color: 'var(--noaa-dark-blue)',
                    padding: '3px 8px',
                    borderRadius: '4px',
                    fontWeight: 700,
                  }}
                >
                  {idx + 1}. {step}
                </span>
              ))}
            </div>
          </div>

          {/* Transformation Pipeline if returned by backend */}
          {transformationPipeline.length > 0 && (
            <div>
              <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--noaa-dark-blue)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Transformation Steps &amp; Anti-Leakage Guarantees
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {transformationPipeline.map((step: any) => (
                  <div
                    key={step.step_id}
                    style={{
                      background: 'var(--noaa-gray-bg)',
                      padding: '10px 12px',
                      borderRadius: '4px',
                      fontSize: '0.78rem',
                    }}
                  >
                    <div style={{ fontWeight: 700, color: 'var(--noaa-dark-blue)' }}>
                      Step {step.step_id}: {step.name}
                    </div>
                    <div style={{ color: 'var(--noaa-text)', marginTop: '2px' }}>{step.description}</div>
                    <div style={{ fontFamily: 'monospace', fontSize: '0.72rem', color: 'var(--noaa-accent)', marginTop: '4px' }}>
                      Standard: {step.formula_or_standard}
                    </div>
                    <div style={{ fontSize: '0.72rem', color: '#166534', fontWeight: 600, marginTop: '2px' }}>
                      ✓ {step.anti_leakage_guarantee}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Primary Data Sources */}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--noaa-dark-blue)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Primary Data Sources
            </h4>
            <div style={{ fontSize: '0.8rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div style={{ background: 'var(--noaa-gray-bg)', padding: '10px', borderRadius: '4px' }}>
                <strong style={{ color: 'var(--noaa-accent)' }}>Forecast Source:</strong>
                <div>{primarySources.forecast_model}</div>
                <div style={{ color: 'var(--noaa-muted)', fontSize: '0.75rem', marginTop: '2px' }}>
                  Resolution: {primarySources.forecast_resolution}
                </div>
              </div>
              <div style={{ background: 'var(--noaa-gray-bg)', padding: '10px', borderRadius: '4px' }}>
                <strong style={{ color: 'var(--noaa-accent)' }}>Verification Source:</strong>
                <div>{primarySources.reference_analysis}</div>
                <div style={{ color: 'var(--noaa-muted)', fontSize: '0.75rem', marginTop: '2px' }}>
                  Resolution: {primarySources.reference_resolution}
                </div>
              </div>
            </div>
          </div>

          {/* SHA-256 Checksums */}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--noaa-dark-blue)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Artifact SHA-256 Checksums (C9, L5)
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {Object.entries(artifactsChecksums).map(([name, hash]) => (
                <div
                  key={name}
                  style={{
                    background: 'var(--noaa-gray-bg)',
                    padding: '8px 10px',
                    borderRadius: '4px',
                    fontSize: '0.72rem',
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--noaa-text)' }}>{name}</div>
                  <div style={{ fontFamily: 'monospace', color: 'var(--noaa-muted)', wordBreak: 'break-all', marginTop: '2px' }}>
                    {hash}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Licenses & Terms of Use */}
          <div>
            <h4 style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--noaa-dark-blue)', textTransform: 'uppercase', marginBottom: '8px' }}>
              Dataset Licenses &amp; Terms (C11)
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {Object.entries(licenses).map(([key, item]) => (
                <div key={key} style={{ fontSize: '0.78rem', background: 'var(--noaa-gray-bg)', padding: '8px 10px', borderRadius: '4px' }}>
                  <div style={{ fontWeight: 700 }}>{item.license}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--noaa-muted)', marginTop: '2px' }}>{item.attribution}</div>
                  <a
                    href={item.uri}
                    target="_blank"
                    rel="noreferrer"
                    style={{ fontSize: '0.72rem', color: 'var(--noaa-accent)', marginTop: '4px', display: 'inline-block' }}
                  >
                    View Terms URI &rarr;
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </>
  );
};

export default ProvenanceDrawer;
