import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { AuditLog } from '../../types';
import { Modal } from '../../components/common/Modal';
import { History, Search, FileCode, CheckCircle2 } from 'lucide-react';

export const AuditView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [entityFilter, setEntityFilter] = useState('');
  const [actorFilter, setActorFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Diff inspection modal
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await api.getAuditLogs({
        entity_type: entityFilter || undefined,
        actor: actorFilter || undefined,
        page,
        page_size: 15
      });
      setLogs(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, [page, entityFilter, actorFilter]);

  const formatJson = (val?: string) => {
    if (!val) return 'None';
    try {
      return JSON.stringify(JSON.parse(val), null, 2);
    } catch {
      return val;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Audit Trail Explorer</h1>
          <p className="text-sm text-slate-500 mt-1">
            Immutable system change log capturing state transitions, actors, timestamps, and correlation IDs.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={entityFilter}
            onChange={(e) => { setEntityFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
          >
            <option value="">All Entities</option>
            <option value="PATIENT">PATIENT</option>
            <option value="APPOINTMENT">APPOINTMENT</option>
            <option value="ENCOUNTER">ENCOUNTER</option>
            <option value="ORDER">ORDER</option>
            <option value="RESULT">RESULT</option>
            <option value="DATA_QUALITY_ISSUE">DATA_QUALITY_ISSUE</option>
          </select>
          <input
            type="text"
            placeholder="Filter by actor..."
            value={actorFilter}
            onChange={(e) => { setActorFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
          />
        </div>
        <span className="text-xs text-slate-500 font-mono">{total} Audit Records</span>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">Audit ID / Timestamp</th>
                <th className="px-5 py-3.5">Entity</th>
                <th className="px-5 py-3.5">Action</th>
                <th className="px-5 py-3.5">Actor</th>
                <th className="px-5 py-3.5">Reason / Trigger</th>
                <th className="px-5 py-3.5">Correlation ID</th>
                <th className="px-5 py-3.5 text-right">State Diff</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600 mx-auto"></div>
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400 font-sans">
                    No audit records found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.audit_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-semibold text-slate-900">#{log.audit_id}</div>
                      <div className="text-[11px] text-slate-400">{log.changed_at.substring(0, 19).replace('T', ' ')}</div>
                    </td>
                    <td className="px-5 py-3.5 font-sans">
                      <span className="font-semibold text-slate-800">{log.entity_type}</span>
                      <span className="text-slate-500 text-xs block font-mono">ID #{log.entity_id}</span>
                    </td>
                    <td className="px-5 py-3.5 font-sans font-semibold text-teal-700">
                      {log.action}
                    </td>
                    <td className="px-5 py-3.5 font-sans text-xs text-slate-600">
                      {log.actor}
                    </td>
                    <td className="px-5 py-3.5 font-sans text-xs text-slate-500 max-w-xs truncate">
                      {log.reason || '—'}
                    </td>
                    <td className="px-5 py-3.5 text-[11px] text-slate-400 truncate max-w-[120px]" title={log.correlation_id}>
                      {log.correlation_id ? log.correlation_id.substring(0, 8) + '...' : '—'}
                    </td>
                    <td className="px-5 py-3.5 text-right font-sans">
                      <button
                        onClick={() => setSelectedLog(log)}
                        className="inline-flex items-center text-xs font-semibold text-teal-600 hover:text-teal-800"
                      >
                        <FileCode className="w-3.5 h-3.5 mr-1" /> Compare Diff
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-5 py-3.5 border-t border-slate-100 bg-slate-50/50 flex items-center justify-between text-xs text-slate-500">
          <span>Showing {(page - 1) * 15 + 1} to {Math.min(page * 15, total)} of {total}</span>
          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(p - 1, 1))}
              className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
            >
              Previous
            </button>
            <span className="font-mono text-slate-700 font-semibold">{page}</span>
            <button
              disabled={page * 15 >= total}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* State Diff Modal */}
      <Modal
        isOpen={!!selectedLog}
        onClose={() => setSelectedLog(null)}
        title={selectedLog ? `Audit Record #${selectedLog.audit_id}: ${selectedLog.action}` : ''}
        description={selectedLog ? `Target: ${selectedLog.entity_type} #${selectedLog.entity_id} • Actor: ${selectedLog.actor}` : ''}
        maxWidth="max-w-2xl"
      >
        {selectedLog && (
          <div className="space-y-4 text-xs font-mono">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="font-semibold text-slate-700 uppercase tracking-wider block mb-1">Previous State</span>
                <pre className="p-3 bg-slate-900 text-slate-300 rounded-lg overflow-x-auto text-[11px] h-48 border border-slate-800">
                  {formatJson(selectedLog.previous_state)}
                </pre>
              </div>
              <div>
                <span className="font-semibold text-teal-700 uppercase tracking-wider block mb-1">New State</span>
                <pre className="p-3 bg-slate-900 text-teal-300 rounded-lg overflow-x-auto text-[11px] h-48 border border-slate-800">
                  {formatJson(selectedLog.new_state)}
                </pre>
              </div>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg text-slate-600 font-sans space-y-1 border border-slate-200 text-xs">
              <div><strong>Correlation ID:</strong> <span className="font-mono">{selectedLog.correlation_id || 'None'}</span></div>
              <div><strong>Workflow Event:</strong> {selectedLog.reason || 'Unspecified'}</div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 bg-slate-800 text-white font-sans font-semibold rounded-lg text-xs"
              >
                Close Diff
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
