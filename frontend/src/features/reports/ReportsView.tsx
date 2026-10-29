import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { ReportCatalogItem, ReportExecutionResult } from '../../types';
import { BarChart3, Download, Play, Code, Table as TableIcon, Clock, Database, AlertCircle } from 'lucide-react';

export const ReportsView: React.FC = () => {
  const [catalog, setCatalog] = useState<ReportCatalogItem[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>('RPT_01_DAILY_SCHEDULE');
  const [params, setParams] = useState<Record<string, any>>({});
  const [activeTab, setActiveTab] = useState<'results' | 'sql'>('results');

  const [execResult, setExecResult] = useState<ReportExecutionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const fetchCatalog = async () => {
      try {
        const cat = await api.getReportCatalog();
        setCatalog(cat);
        if (cat.length > 0) {
          setSelectedReportId(cat[0].id);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchCatalog();
  }, []);

  const selectedReport = catalog.find(r => r.id === selectedReportId);

  const handleExecute = async (targetPage = 1) => {
    if (!selectedReportId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.executeReport(selectedReportId, params, targetPage, 20);
      setExecResult(res);
      setPage(targetPage);
    } catch (err: any) {
      setError(err.message || 'Report execution failed');
      setExecResult(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (selectedReportId) {
      setParams({});
      handleExecute(1);
    }
  }, [selectedReportId]);

  const handleExportCsv = async () => {
    if (!selectedReportId) return;
    try {
      const downloader = api.exportReportCsvUrl(selectedReportId, params);
      await downloader();
    } catch (err: any) {
      alert('Export failed: ' + err.message);
    }
  };

  const getSqlPreview = (reportId: string) => {
    switch (reportId) {
      case 'RPT_01_DAILY_SCHEDULE':
        return `SELECT a.appointment_id, a.appointment_time, a.department, a.provider_name,\n       a.status, p.mrn, p.first_name || ' ' || p.last_name AS patient_name,\n       a.check_in_time, e.encounter_id, e.status AS encounter_status\nFROM APPOINTMENTS a\nJOIN PATIENTS p ON a.patient_id = p.patient_id\nLEFT JOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id\nWHERE (:p_department IS NULL OR a.department = :p_department)\nORDER BY a.appointment_time ASC;`;
      case 'RPT_02_WAITING_TIME':
        return `SELECT a.department, EXTRACT(HOUR FROM a.check_in_time) AS arrival_hour,\n       COUNT(*) AS total_patients_seen,\n       ROUND(AVG(EXTRACT(DAY FROM (e.start_time - a.check_in_time)) * 1440 +\n                 EXTRACT(HOUR FROM (e.start_time - a.check_in_time)) * 60 +\n                 EXTRACT(MINUTE FROM (e.start_time - a.check_in_time))), 1) AS avg_wait_minutes,\n       MIN(...) AS min_wait_minutes, MAX(...) AS max_wait_minutes\nFROM APPOINTMENTS a\nJOIN ENCOUNTERS e ON a.appointment_id = e.appointment_id\nWHERE a.check_in_time IS NOT NULL AND e.start_time >= a.check_in_time\nGROUP BY a.department, EXTRACT(HOUR FROM a.check_in_time)\nORDER BY a.department, arrival_hour;`;
      case 'RPT_03_ENCOUNTER_COMPLETION':
        return `SELECT department, encounter_type, provider_name,\n       COUNT(*) AS completed_encounters_count,\n       ROUND(AVG(EXTRACT(MINUTE FROM (end_time - start_time))), 1) AS avg_duration_minutes\nFROM ENCOUNTERS\nWHERE status = 'COMPLETED' AND end_time IS NOT NULL\nGROUP BY department, encounter_type, provider_name\nORDER BY department, encounter_type, provider_name;`;
      case 'RPT_04_PENDING_ORDERS':
        return `SELECT o.order_id, o.order_code, o.order_name, o.priority, o.ordered_at,\n       ROUND(EXTRACT(HOUR FROM (SYSTIMESTAMP - o.ordered_at)), 1) AS age_hours,\n       p.mrn, p.last_name, e.department\nFROM ORDERS o\nJOIN PATIENTS p ON o.patient_id = p.patient_id\nJOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id\nWHERE o.order_status IN ('ORDERED', 'IN_PROGRESS')\nORDER BY CASE o.priority WHEN 'STAT' THEN 1 WHEN 'URGENT' THEN 2 ELSE 3 END, o.ordered_at ASC;`;
      case 'RPT_05_AWAITING_REVIEW':
        return `SELECT r.result_id, r.result_time, r.result_value, r.abnormal_flag,\n       o.order_code, p.mrn, p.last_name, e.department\nFROM RESULTS r\nJOIN ORDERS o ON r.order_id = o.order_id\nJOIN PATIENTS p ON o.patient_id = p.patient_id\nJOIN ENCOUNTERS e ON o.encounter_id = e.encounter_id\nWHERE r.result_status = 'PENDING_REVIEW'\nORDER BY CASE r.abnormal_flag WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'LOW' THEN 3 ELSE 4 END;`;
      case 'RPT_06_ORDER_TURNAROUND':
        return `SELECT order_code, order_name, priority, COUNT(*) AS total_completed,\n       ROUND(AVG(EXTRACT(HOUR FROM (completed_at - ordered_at))), 2) AS avg_turnaround_hours\nFROM ORDERS\nWHERE order_status = 'COMPLETED'\nGROUP BY order_code, order_name, priority\nORDER BY avg_turnaround_hours DESC;`;
      case 'RPT_07_CANCELLATIONS_NOSHOW':
        return `SELECT department, appointment_type, COUNT(*) as total_booked,\n       ROUND((COUNT(CASE WHEN status='CANCELLED' THEN 1 END)*100.0)/COUNT(*), 1) AS cancellation_rate_pct,\n       ROUND((COUNT(CASE WHEN status='NO_SHOW' THEN 1 END)*100.0)/COUNT(*), 1) AS noshow_rate_pct\nFROM APPOINTMENTS\nGROUP BY department, appointment_type;`;
      case 'RPT_08_DATA_QUALITY':
        return `SELECT issue_id, rule_code, severity, affected_entity, entity_id, description\nFROM DATA_QUALITY_ISSUES\nORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END;`;
      default:
        return `-- Parameterized Oracle SQL query executed directly against DB engine.`;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Reporting Workspace</h1>
          <p className="text-sm text-slate-500 mt-1">
            Production-grade operational reports and clinical aggregations executed directly against the database.
          </p>
        </div>
      </div>

      {/* Catalog Selector */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
        {catalog.map((cat) => {
          const isSelected = cat.id === selectedReportId;
          return (
            <div
              key={cat.id}
              onClick={() => setSelectedReportId(cat.id)}
              className={`p-3.5 rounded-xl border text-left cursor-pointer transition-all ${
                isSelected
                  ? 'bg-teal-50/70 border-teal-500 shadow-sm'
                  : 'bg-white border-slate-200/80 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider text-teal-700 font-semibold">
                  {cat.category}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">{cat.id}</span>
              </div>
              <h3 className="text-xs font-bold text-slate-900 mt-1 truncate">{cat.title}</h3>
              <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">{cat.business_question}</p>
            </div>
          );
        })}
      </div>

      {/* Report Execution & Filter Console */}
      {selectedReport && (
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs space-y-4">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
            <div>
              <h2 className="text-base font-bold text-slate-900">{selectedReport.title}</h2>
              <p className="text-xs text-slate-500 mt-0.5">{selectedReport.description}</p>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleExecute(1)}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50 transition-colors"
              >
                <Play className="w-3.5 h-3.5 mr-1.5" />
                {loading ? 'Executing...' : 'Run Query'}
              </button>
              <button
                onClick={handleExportCsv}
                className="inline-flex items-center px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-colors border border-slate-200"
              >
                <Download className="w-3.5 h-3.5 mr-1.5" /> Export CSV
              </button>
            </div>
          </div>

          {/* Parameter Inputs */}
          {selectedReport.parameters.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
              {selectedReport.parameters.map((p) => (
                <div key={p.name}>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">{p.label}</label>
                  {p.type === 'select' ? (
                    <select
                      value={params[p.name] || ''}
                      onChange={(e) => setParams({ ...params, [p.name]: e.target.value })}
                      className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                    >
                      {p.options?.map((opt) => (
                        <option key={opt} value={opt === 'All' ? '' : opt}>{opt}</option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type={p.type}
                      value={params[p.name] || ''}
                      onChange={(e) => setParams({ ...params, [p.name]: e.target.value })}
                      className="w-full px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs"
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Execution Metadata Bar */}
          {execResult && (
            <div className="flex flex-wrap items-center justify-between text-xs font-mono text-slate-500 pt-3 border-t border-slate-100">
              <div className="flex items-center space-x-4">
                <span className="flex items-center text-emerald-700">
                  <Clock className="w-3.5 h-3.5 mr-1" /> {execResult.execution_time_ms} ms
                </span>
                <span className="flex items-center text-slate-600">
                  <Database className="w-3.5 h-3.5 mr-1" /> Dialect: {execResult.dialect.toUpperCase()}
                </span>
                <span>Total Rows: <strong>{execResult.total_rows}</strong></span>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setActiveTab('results')}
                  className={`px-2.5 py-1 rounded text-xs font-sans font-semibold ${
                    activeTab === 'results' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <TableIcon className="w-3 h-3 inline mr-1" /> Data Grid
                </button>
                <button
                  onClick={() => setActiveTab('sql')}
                  className={`px-2.5 py-1 rounded text-xs font-sans font-semibold ${
                    activeTab === 'sql' ? 'bg-slate-800 text-white' : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <Code className="w-3 h-3 inline mr-1" /> SQL Query
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center">
          <AlertCircle className="w-4 h-4 mr-2" />
          <span>{error}</span>
        </div>
      )}

      {/* SQL Code Preview Tab */}
      {activeTab === 'sql' && (
        <div className="bg-slate-900 text-slate-200 p-5 rounded-xl border border-slate-800 font-mono text-xs overflow-x-auto shadow-inner">
          <div className="text-teal-400 font-semibold mb-2 flex items-center">
            <Database className="w-4 h-4 mr-2" /> Oracle Relational SQL Specification ({selectedReportId})
          </div>
          <pre className="whitespace-pre">{getSqlPreview(selectedReportId)}</pre>
        </div>
      )}

      {/* Results Table Tab */}
      {activeTab === 'results' && execResult && (
        <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  {execResult.columns.map((col) => (
                    <th key={col} className="px-4 py-3 font-mono">{col.replace(/_/g, ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {execResult.rows.length === 0 ? (
                  <tr>
                    <td colSpan={execResult.columns.length || 1} className="text-center py-12 text-slate-400">
                      No matching records returned by reporting query.
                    </td>
                  </tr>
                ) : (
                  execResult.rows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                      {execResult.columns.map((col) => {
                        const val = row[col];
                        return (
                          <td key={col} className="px-4 py-3 text-xs font-mono text-slate-800">
                            {val === null || val === undefined ? '—' : String(val)}
                          </td>
                        );
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="px-5 py-3 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
            <span>
              Page {page} of {Math.ceil(execResult.total_rows / 20) || 1} ({execResult.total_rows} total rows)
            </span>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => handleExecute(page - 1)}
                className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page * 20 >= execResult.total_rows}
                onClick={() => handleExecute(page + 1)}
                className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
