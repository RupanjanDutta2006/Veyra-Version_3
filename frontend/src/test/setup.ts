import '@testing-library/jest-dom';
import React from 'react';
import { vi } from 'vitest';

vi.mock('leaflet', () => ({
  default: {
    Icon: {
      Default: {
        prototype: {},
        mergeOptions: vi.fn(),
      },
    },
  },
  Icon: {
    Default: {
      prototype: {},
      mergeOptions: vi.fn(),
    },
  },
}));

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: any) => React.createElement('div', { 'data-testid': 'mock-map-container' }, children),
  TileLayer: () => React.createElement('div', { 'data-testid': 'mock-tile-layer' }),
  Marker: ({ children }: any) => React.createElement('div', { 'data-testid': 'mock-marker' }, children),
  Popup: ({ children }: any) => React.createElement('div', { 'data-testid': 'mock-popup' }, children),
  Polygon: ({ children }: any) => React.createElement('div', { 'data-testid': 'mock-polygon' }, children),
  Circle: ({ children }: any) => React.createElement('div', { 'data-testid': 'mock-circle' }, children),
  Polyline: ({ children }: any) => React.createElement('div', { 'data-testid': 'mock-polyline' }, children),
  Tooltip: ({ children }: any) => React.createElement('div', { 'data-testid': 'mock-tooltip' }, children),
  useMap: () => ({ setView: vi.fn(), flyTo: vi.fn(), invalidateSize: vi.fn() }),
}));

vi.mock('react-chartjs-2', () => ({
  Line: (props: any) =>
    React.createElement('div', {
      'data-testid': 'mock-chart-line',
      'data-chart-data': JSON.stringify(props.data || {}),
    }, 'Mock Line Chart'),
  Bar: (props: any) =>
    React.createElement('div', {
      'data-testid': 'mock-chart-bar',
      'data-chart-data': JSON.stringify(props.data || {}),
    }, 'Mock Bar Chart'),
}));

