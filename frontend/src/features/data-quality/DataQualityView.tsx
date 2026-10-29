import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { DataQualityIssue } from '../../types';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { ShieldAlert, RefreshCw, CheckCircle2, AlertTriangle, ArrowRight, Wrench } from 'lucide-react';

export const DataQualityView: React.FC = () => {
  const [issues, setIssues] = useState<DataQualityIssue[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Remediation Modal
  const [remediateTarget, setRemediateTarget] = useState<DataQualityIssue | null>(null);
  const [remediationNotes, setRemediationNotes] = useState('');
  const [resolutionStatus, setResolutionStatus] = useState('RESOLVED');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [remediateError, setRemediateError] = useState<string | null>(null);

  // Scan state
  const [isScanning, setIsScanning] = useState(false);
  const [scanMessage, setScanMessage] = useState<string | null>(null);

  const fetchIssues = async () => {
    try {
      setLoading(true);
      const res = await api.getDataQualityIssues({
        status: statusFilter || undefined,
        severity: severityFilter || undefined,
        page,
        page_size: 15
      });
      setIssues(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIssues();
  }, [page, statusFilter, severityFilter]);

  const handleRunScan = async () => {
    setIsScanning(true);
    setScanMessage(null);
    try {
      const res = await api.runDataQualityScan();
      setScanMessage(`Scan complete: evaluated ${res.scanned_rules_count} rules. Found ${res.new_issues_found} new issues; ${res.open_issues_total} total currently open.`);
      fetchIssues();
    } catch (err: any) {
      alert(err.message || 'Scan failed');
    } finally {
      setIsScanning(false);
    }
  };

  const handleRemediateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!remediateTarget) return;
    setIsSubmitting(true);
    setRemediateError(null);
    try {
      await api.resolveDataQualityIssue(
        remediateTarget.issue_id,
        'Dr. Elena Rostova / QA Lead',
        remediationNotes,
        resolutionStatus
      );
      setRemediateTarget(null);
      setRemediationNotes('');
      fetchIssues();
    } catch (err: any) {
      setRemediateError(err.message || 'Failed to remediate issue.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Data Quality & Root-Cause Remediation</h1>
          <p className="text-sm text-slate-500 mt-1">
            Explicit data-integrity rule inspection, anomaly root-cause investigation, and auditable corrective remediation.
          </p>
        </div>
        <button
          onClick={handleRunScan}
          disabled={isScanning}
          className="inline-flex items-center px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors self-start sm:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isScanning ? 'animate-spin' : ''}`} />
          {isScanning ? 'Auditing Database...' : 'Run Live Integrity Audit'}
        </button>
      </div>

      {/* Scan result notification */}
      {scanMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>{scanMessage}</span>
          </div>
          <button onClick={() => setScanMessage(null)} className="text-xs text-emerald-700 underline">Dismiss</button>
        </div>
      )}

      {/* Filters Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
          >
            <option value="">All Resolution Statuses</option>
            <option value="OPEN">OPEN (Requires Action)</option>
            <option value="INVESTIGATING">INVESTIGATING</option>
            <option value="RESOLVED">RESOLVED</option>
            <option value="FALSE_POSITIVE">FALSE_POSITIVE</option>
          </select>
          <select
            value={severityFilter}
            onChange={(e) => { setSeverityFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-mono">{total} Issue{total === 1 ? '' : 's'} Logged</span>
      </div>

      {/* Issues Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">ID / Severity</th>
                <th className="px-5 py-3.5">Rule Code</th>
                <th className="px-5 py-3.5">Affected Entity</th>
                <th className="px-5 py-3.5">Description & Impact</th>
                <th className="px-5 py-3.5">Investigation Steps</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600 mx-auto"></div>
                  </td>
                </tr>
              ) : issues.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    No data quality issues match the selected criteria.
                  </td>
                </tr>
              ) : (
                issues.map((issue) => (
                  <tr key={issue.issue_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-mono text-xs font-semibold text-slate-900">DQ-#{issue.issue_id}</div>
                      <div className="mt-1"><Badge status={issue.severity} size="sm" /></div>
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs font-semibold text-slate-800">
                      {issue.rule_code}
                    </td>
                    <td className="px-5 py-3.5 text-xs">
                      <div className="font-semibold text-teal-800">{issue.affected_entity}</div>
                      <div className="font-mono text-slate-500">ID #{issue.entity_id}</div>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-700 max-w-sm">
                      <p className="line-clamp-2">{issue.description}</p>
                      {issue.remediation_notes && (
                        <div className="mt-1 text-[11px] text-emerald-700 italic bg-emerald-50 p-1.5 rounded border border-emerald-200/60">
                          Fix: {issue.remediation_notes} (by {issue.resolved_by})
                        </div>
                      )}
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500 max-w-xs">
                      <p className="line-clamp-2">{issue.investigation_steps}</p>
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge status={issue.resolution_status} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      {issue.resolution_status === 'OPEN' || issue.resolution_status === 'INVESTIGATING' ? (
                        <button
                          onClick={() => {
                            setRemediateTarget(issue);
                            setRemediationNotes('');
                            setRemediateError(null);
                          }}
                          className="inline-flex items-center px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 rounded text-xs font-semibold transition-colors"
                        >
                          <Wrench className="w-3.5 h-3.5 mr-1" /> Remediate
                        </button>
                      ) : (
                        <span className="text-xs text-emerald-600 font-semibold flex items-center justify-end">
                          <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> Resolved
                        </span>
                      )}
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

      {/* Controlled Remediation Modal */}
      <Modal
        isOpen={!!remediateTarget}
        onClose={() => setRemediateTarget(null)}
        title={`Remediate Data Quality Issue #${remediateTarget?.issue_id}`}
        description="Records resolution diagnosis, corrective actions, and writes an immutable entry into AUDIT_LOG."
      >
        {remediateTarget && (
          <form onSubmit={handleRemediateSubmit} className="space-y-4">
            {remediateError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center">
                <AlertTriangle className="w-4 h-4 mr-2" />
                <span>{remediateError}</span>
              </div>
            )}

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <div><strong>Rule Code:</strong> {remediateTarget.rule_code}</div>
              <div><strong>Entity:</strong> {remediateTarget.affected_entity} #{remediateTarget.entity_id}</div>
              <div className="text-slate-600 mt-1"><strong>Description:</strong> {remediateTarget.description}</div>
              <div className="text-teal-700 mt-1"><strong>Suggested Investigation:</strong> {remediateTarget.investigation_steps}</div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Resolution Outcome *</label>
              <select
                value={resolutionStatus}
                onChange={(e) => setResolutionStatus(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
              >
                <option value="RESOLVED">RESOLVED (Corrected Invariant / Backfilled Record)</option>
                <option value="FALSE_POSITIVE">FALSE_POSITIVE (Clinical Exception Allowed)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Remediation Documentation & Root-Cause Explanation *
              </label>
              <textarea
                rows={4}
                required
                placeholder="Explain the root cause (e.g. kiosk disconnect, manual override), action taken, and verification method..."
                value={remediationNotes}
                onChange={(e) => setRemediationNotes(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setRemediateTarget(null)}
                className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
              >
                {isSubmitting ? 'Writing Audit...' : 'Submit Resolution'}
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};
