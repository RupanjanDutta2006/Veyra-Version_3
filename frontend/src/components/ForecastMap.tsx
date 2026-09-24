import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import { RiskMapItem } from '../api/types';
import { BENCHMARK_LOCATIONS } from '../data/locations';

// Fix default marker icon issues in Vite
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
});

// Helper component to center map when coordinates update
function RecenterMap({ lat, lng }: { lat: number; lng: number }) {
  const map = useMap();
  useEffect(() => {
    if (lat != null && lng != null && !isNaN(lat) && !isNaN(lng)) {
      map.setView([lat, lng], 6);
    }
  }, [lat, lng, map]);
  return null;
}

// Helper component to invalidate size on mount and window resize
function MapResizer() {
  const map = useMap();
  useEffect(() => {
    const handleResize = () => {
      map.invalidateSize();
    };
    const timer = setTimeout(handleResize, 150);
    window.addEventListener('resize', handleResize);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('resize', handleResize);
    };
  }, [map]);
  return null;
}

// Canonical Indian Meteorological Risk Zones (GeoJSON / Polygon coordinates)
const DEFAULT_REGIONAL_POLYGONS: Array<{
  id: string;
  name: string;
  coords: [number, number][];
  defaultProb: number;
  defaultBand: 'GREEN' | 'YELLOW' | 'ORANGE' | 'RED' | 'GRAY';
  areaFraction: number;
}> = [
  {
    id: 'IN_NORTH',
    name: 'Northern Plains / Western Himalayas',
    coords: [
      [34.5, 74.0],
      [34.5, 78.5],
      [28.0, 80.5],
      [28.0, 75.0],
    ],
    defaultProb: 0.18,
    defaultBand: 'YELLOW',
    areaFraction: 0.22,
  },
  {
    id: 'IN_WEST',
    name: 'Western Arid / Gujarat & Rajasthan',
    coords: [
      [28.0, 69.5],
      [28.0, 75.0],
      [22.0, 74.0],
      [22.0, 68.5],
    ],
    defaultProb: 0.45,
    defaultBand: 'ORANGE',
    areaFraction: 0.18,
  },
  {
    id: 'IN_CENTRAL',
    name: 'Central Peninsular & Deccan Plateau',
    coords: [
      [24.0, 75.0],
      [24.0, 83.0],
      [18.0, 82.0],
      [18.0, 74.5],
    ],
    defaultProb: 0.08,
    defaultBand: 'GREEN',
    areaFraction: 0.25,
  },
  {
    id: 'IN_EAST',
    name: 'Eastern Gangetic / Bay of Bengal Coast',
    coords: [
      [27.0, 83.0],
      [27.0, 89.0],
      [19.5, 87.0],
      [19.5, 83.0],
    ],
    defaultProb: 0.68,
    defaultBand: 'RED',
    areaFraction: 0.16,
  },
  {
    id: 'IN_SOUTH',
    name: 'Southern Peninsular Coastal',
    coords: [
      [18.0, 74.5],
      [18.0, 80.5],
      [8.5, 78.5],
      [8.5, 76.5],
    ],
    defaultProb: 0.12,
    defaultBand: 'YELLOW',
    areaFraction: 0.14,
  },
  {
    id: 'IN_NORTHEAST',
    name: 'Northeastern Hills & Brahmaputra',
    coords: [
      [28.5, 89.5],
      [28.5, 96.5],
      [23.5, 95.0],
      [23.5, 90.0],
    ],
    defaultProb: 0.05,
    defaultBand: 'GREEN',
    areaFraction: 0.09,
  },
];

function getRiskBandColor(band: string): string {
  switch (band.toUpperCase()) {
    case 'RED':
      return '#cd2026';
    case 'ORANGE':
      return '#ea580c';
    case 'YELLOW':
      return '#b87a00';
    case 'GREEN':
      return '#2e8540';
    case 'GRAY':
    default:
      return '#64748b';
  }
}

interface ForecastMapProps {
  latitude?: number | null;
  longitude?: number | null;
  label?: string;
  riskMapData?: RiskMapItem[];
  centroidErrorKm?: number;
  highlightedRiskBand?: string;
}

export const ForecastMap: React.FC<ForecastMapProps> = ({
  latitude,
  longitude,
  label = 'Location',
  riskMapData: _riskMapData,
  centroidErrorKm = 42.5,
  highlightedRiskBand: _highlightedRiskBand,
}) => {
  const hasValidCoordinates =
    typeof latitude === 'number' &&
    typeof longitude === 'number' &&
    !isNaN(latitude) &&
    !isNaN(longitude);

  const centerLat = hasValidCoordinates ? latitude : 28.6139;
  const centerLon = hasValidCoordinates ? longitude : 77.2090;
  const position: [number, number] = [centerLat, centerLon];

  // Layer toggles
  const [showRiskPolygons, setShowRiskPolygons] = useState(true);
  const [showCentroidRadius, setShowCentroidRadius] = useState(true);
  const [showStations, setShowStations] = useState(true);

  return (
    <div
      className="forecast-map-wrapper"
      role="region"
      aria-label="Geographic Location and Spatial Risk Map"
      style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: '420px' }}
    >
      {/* Map Header & Layer Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '8px 14px',
          background: 'var(--noaa-card-bg)',
          borderBottom: '1px solid var(--noaa-border-subtle)',
          fontSize: '0.82rem',
          flexWrap: 'wrap',
          gap: '8px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <strong style={{ color: 'var(--noaa-dark-blue)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            Spatial Risk Objects (Leaflet + GeoJSON)
          </strong>
          <span
            style={{
              fontSize: '0.72rem',
              padding: '2px 6px',
              borderRadius: '4px',
              background: 'var(--noaa-light-blue)',
              color: 'var(--noaa-dark-blue)',
              fontWeight: 700,
            }}
          >
            FSS / Object-Aware
          </span>
        </div>

        {/* Layer Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showRiskPolygons}
              onChange={(e) => setShowRiskPolygons(e.target.checked)}
            />
            <span>Risk Zones</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showCentroidRadius}
              onChange={(e) => setShowCentroidRadius(e.target.checked)}
            />
            <span>Centroid Error ({centroidErrorKm} km)</span>
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '5px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={showStations}
              onChange={(e) => setShowStations(e.target.checked)}
            />
            <span>Stations</span>
          </label>
        </div>
      </div>

      {/* Map Container */}
      <div style={{ width: '100%', height: '380px', minHeight: '380px', position: 'relative' }}>
        <MapContainer
          center={position}
          zoom={5}
          scrollWheelZoom={false}
          style={{ height: '380px', minHeight: '380px', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {/* Regional Risk Polygons (GeoJSON-style objects) */}
          {showRiskPolygons &&
            DEFAULT_REGIONAL_POLYGONS.map((zone) => {
              const color = getRiskBandColor(zone.defaultBand);
              return (
                <Polygon
                  key={zone.id}
                  positions={zone.coords}
                  pathOptions={{
                    color,
                    fillColor: color,
                    fillOpacity: 0.35,
                    weight: 2,
                    dashArray: zone.defaultBand === 'GRAY' ? '4, 4' : undefined,
                  }}
                >
                  <Popup>
                    <div style={{ padding: '4px 2px' }}>
                      <div style={{ fontWeight: 700, color: 'var(--noaa-dark-blue)', marginBottom: '4px' }}>
                        {zone.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', display: 'grid', gridTemplateColumns: 'auto auto', gap: '4px 12px' }}>
                        <span style={{ color: 'var(--noaa-muted)' }}>Risk Band:</span>
                        <strong style={{ color }}>{zone.defaultBand}</strong>
                        <span style={{ color: 'var(--noaa-muted)' }}>Bust Prob:</span>
                        <strong>{(zone.defaultProb * 100).toFixed(1)}%</strong>
                        <span style={{ color: 'var(--noaa-muted)' }}>Area Fraction:</span>
                        <strong>{(zone.areaFraction * 100).toFixed(0)}%</strong>
                      </div>
                    </div>
                  </Popup>
                </Polygon>
              );
            })}

          {/* Target Location Marker & Centroid Radius */}
          {hasValidCoordinates && (
            <>
              <Marker position={position}>
                <Popup>
                  <div style={{ fontWeight: 700, color: 'var(--noaa-dark-blue)' }}>{label}</div>
                  <div style={{ fontSize: '0.8rem', color: '#555', marginTop: '2px' }}>
                    [{centerLat.toFixed(4)}°N, {centerLon.toFixed(4)}°E]
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--noaa-accent)', marginTop: '4px' }}>
                    Active Sentinel Atmospheric Target
                  </div>
                </Popup>
              </Marker>

              {/* Centroid Error Radius Circle */}
              {showCentroidRadius && (
                <Circle
                  center={position}
                  radius={centroidErrorKm * 1000} // meters
                  pathOptions={{
                    color: '#ea580c',
                    fillColor: '#ea580c',
                    fillOpacity: 0.12,
                    weight: 1.5,
                    dashArray: '5, 5',
                  }}
                >
                  <Popup>
                    <div style={{ fontSize: '0.8rem' }}>
                      <strong>Centroid Displacement Uncertainty</strong>
                      <div>Radius: {centroidErrorKm} km (J4 spatial verification benchmark)</div>
                    </div>
                  </Popup>
                </Circle>
              )}
            </>
          )}

          {/* 25 Canonical Stations Markers */}
          {showStations &&
            BENCHMARK_LOCATIONS.map((loc) => {
              if (hasValidCoordinates && Math.abs(loc.lat - centerLat) < 0.05 && Math.abs(loc.lon - centerLon) < 0.05) {
                return null; // Already shown as active target
              }
              return (
                <Circle
                  key={loc.name}
                  center={[loc.lat, loc.lon]}
                  radius={12000} // 12km dot
                  pathOptions={{
                    color: '#205493',
                    fillColor: '#205493',
                    fillOpacity: 0.8,
                    weight: 1,
                  }}
                >
                  <Popup>
                    <div style={{ fontSize: '0.8rem' }}>
                      <strong>{loc.name}</strong>
                      <div>Canonical Synoptic Station</div>
                      <div style={{ color: '#666', fontSize: '0.72rem' }}>
                        [{loc.lat.toFixed(2)}°, {loc.lon.toFixed(2)}°]
                      </div>
                    </div>
                  </Popup>
                </Circle>
              );
            })}

          <RecenterMap lat={centerLat} lng={centerLon} />
          <MapResizer />
        </MapContainer>
      </div>
    </div>
  );
};

export default ForecastMap;
