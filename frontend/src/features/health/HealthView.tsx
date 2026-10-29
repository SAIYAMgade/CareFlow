import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { SystemHealth } from '../../types';
import { Badge } from '../../components/common/Badge';
import { Activity, Database, Server, Clock, RefreshCw, CheckCircle2, AlertTriangle } from 'lucide-react';

export const HealthView: React.FC = () => {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getSystemHealth();
      setHealth(res);
    } catch (err: any) {
      setError(err.message || 'Failed to ping health endpoint');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">System & Database Health</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time infrastructure telemetry, database driver status, and dialect connection pooling.
          </p>
        </div>
        <button
          onClick={fetchHealth}
          disabled={loading}
          className="inline-flex items-center px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Run Health Ping
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2" />
          <span>{error}</span>
        </div>
      )}

      {health && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Application Server Card */}
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-lg bg-teal-50 text-teal-700">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900">Application API Layer</h3>
                  <span className="text-xs text-slate-400">FastAPI • Python 3.14</span>
                </div>
              </div>
              <Badge status={health.status} size="md" />
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Service Name</span>
                <span className="font-semibold text-slate-800">{health.application}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Software Version</span>
                <span className="font-mono text-slate-800">{health.version}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Deployment Context</span>
                <span className="font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded">{health.environment}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">API Gateway</span>
                <span className="font-mono text-emerald-700 font-semibold">/api (Healthy)</span>
              </div>
            </div>
          </div>

          {/* Database Layer Card */}
          <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center space-x-3">
                <div className="p-2.5 rounded-lg bg-blue-50 text-blue-700">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900">Database Engine</h3>
                  <span className="text-xs text-slate-400">
                    Dialect: {health.database.dialect.toUpperCase()}
                  </span>
                </div>
              </div>
              <Badge status={health.database.status} size="md" />
            </div>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Engine Version</span>
                <span className="font-mono font-semibold text-slate-800">
                  {health.database.database_version || 'Oracle Database Free (23ai)'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Connection State</span>
                <span className="font-semibold text-emerald-700 flex items-center">
                  <CheckCircle2 className="w-3.5 h-3.5 mr-1" />
                  {health.database.connected ? 'Connected & Verified' : 'Disconnected'}
                </span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">Server Clock Timestamp</span>
                <span className="font-mono text-slate-700">{health.database.server_time || '—'}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Connection Mode</span>
                <span className="font-mono text-slate-700">
                  {health.database.dialect === 'oracle' ? 'oracledb Pool (1-10 connections)' : 'Local File-Backed Relational Engine'}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
