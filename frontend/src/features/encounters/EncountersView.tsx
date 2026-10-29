import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Encounter, Order, Observation } from '../../types';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Stethoscope, CheckCircle, FileText, AlertCircle, Plus, FlaskConical } from 'lucide-react';

export const EncountersView: React.FC = () => {
  const [encounters, setEncounters] = useState<Encounter[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Status transition modal
  const [transitionTarget, setTransitionTarget] = useState<Encounter | null>(null);
  const [newStatus, setNewStatus] = useState('IN_PROGRESS');
  const [notes, setNotes] = useState('');
  const [transitionError, setTransitionError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Detail modal
  const [selectedEncounter, setSelectedEncounter] = useState<Encounter | null>(null);
  const [encounterOrders, setEncounterOrders] = useState<Order[]>([]);
  const [encounterObs, setEncounterObs] = useState<Observation[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  // Place order modal
  const [isOrderOpen, setIsOrderOpen] = useState(false);
  const [orderForm, setOrderForm] = useState({
    order_code: 'CBC',
    order_name: 'Complete Blood Count',
    priority: 'ROUTINE'
  });

  const fetchEncounters = async () => {
    try {
      setLoading(true);
      const res = await api.getEncounters({
        department: departmentFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 15
      });
      setEncounters(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEncounters();
  }, [page, departmentFilter, statusFilter]);

  const openEncounterDetails = async (enc: Encounter) => {
    setSelectedEncounter(enc);
    setDetailLoading(true);
    try {
      const [ordRes, obsRes] = await Promise.all([
        api.getOrders({ encounter_id: enc.encounter_id }),
        api.getObservations({ encounter_id: enc.encounter_id })
      ]);
      setEncounterOrders(ordRes.items);
      setEncounterObs(obsRes);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleStatusTransition = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!transitionTarget) return;
    setTransitionError(null);
    setIsSubmitting(true);
    try {
      await api.updateEncounterStatus(
        transitionTarget.encounter_id,
        newStatus,
        'Dr. Elena Rostova, MD',
        notes || undefined
      );
      setTransitionTarget(null);
      setNotes('');
      fetchEncounters();
    } catch (err: any) {
      setTransitionError(err.message || 'Failed to update encounter status.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCreateOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEncounter) return;
    try {
      await api.createOrder({
        encounter_id: selectedEncounter.encounter_id,
        patient_id: selectedEncounter.patient_id,
        order_type: 'LABORATORY',
        order_code: orderForm.order_code,
        order_name: orderForm.order_name,
        priority: orderForm.priority,
        ordered_by: selectedEncounter.provider_name
      });
      setIsOrderOpen(false);
      openEncounterDetails(selectedEncounter);
    } catch (err: any) {
      alert(err.message || 'Failed to place order');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Encounter Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Active clinical visits, status progression, documentation, and pending orders safety gates.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={departmentFilter}
            onChange={(e) => { setDepartmentFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
          >
            <option value="">All Departments</option>
            <option value="Cardiology">Cardiology</option>
            <option value="Endocrinology">Endocrinology</option>
            <option value="Family Medicine">Family Medicine</option>
            <option value="Pediatrics">Pediatrics</option>
            <option value="Urgent Care">Urgent Care</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
          >
            <option value="">All Statuses</option>
            <option value="OPEN">Open (Triage)</option>
            <option value="IN_PROGRESS">In Progress (Exam)</option>
            <option value="AWAITING_RESULTS">Awaiting Lab Results</option>
            <option value="COMPLETED">Completed</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-mono">{total} Encounter{total === 1 ? '' : 's'}</span>
      </div>

      {/* Encounters Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">ID / Start</th>
                <th className="px-5 py-3.5">Patient Details</th>
                <th className="px-5 py-3.5">Department / Type</th>
                <th className="px-5 py-3.5">Attending Clinician</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Chief Complaint</th>
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
              ) : encounters.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    No clinical encounters found.
                  </td>
                </tr>
              ) : (
                encounters.map((enc) => (
                  <tr key={enc.encounter_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-mono text-xs font-semibold text-slate-900">ENC-#{enc.encounter_id}</div>
                      <div className="text-[11px] text-slate-400 font-mono">{enc.start_time.substring(0, 16).replace('T', ' ')}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-slate-900">{enc.patient_name}</div>
                      <div className="font-mono text-[11px] text-teal-700">{enc.patient_mrn}</div>
                    </td>
                    <td className="px-5 py-3.5 text-xs">
                      <div className="text-slate-800 font-medium">{enc.department}</div>
                      <div className="text-slate-400 text-[11px]">{enc.encounter_type}</div>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-600">{enc.provider_name}</td>
                    <td className="px-5 py-3.5">
                      <Badge status={enc.status} />
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-500 max-w-xs truncate">
                      {enc.chief_complaint || '—'}
                    </td>
                    <td className="px-5 py-3.5 text-right space-x-2">
                      <button
                        onClick={() => openEncounterDetails(enc)}
                        className="text-xs font-semibold text-teal-600 hover:text-teal-800"
                      >
                        Inspect
                      </button>
                      {enc.status !== 'COMPLETED' && enc.status !== 'CANCELLED' && (
                        <button
                          onClick={() => {
                            setTransitionTarget(enc);
                            setNewStatus(enc.status === 'OPEN' ? 'IN_PROGRESS' : 'COMPLETED');
                            setTransitionError(null);
                          }}
                          className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-medium"
                        >
                          Progress Status
                        </button>
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
          <span>
            Showing {(page - 1) * 15 + 1} to {Math.min(page * 15, total)} of {total} records
          </span>
          <div className="flex items-center space-x-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(p => Math.max(p - 1, 1))}
              className="px-3 py-1 bg-white border border-slate-200 rounded text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              Previous
            </button>
            <span className="font-mono text-slate-700 font-semibold">{page}</span>
            <button
              disabled={page * 15 >= total}
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1 bg-white border border-slate-200 rounded text-slate-700 hover:bg-slate-50 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Status Transition Modal */}
      <Modal
        isOpen={!!transitionTarget}
        onClose={() => setTransitionTarget(null)}
        title={`Transition Status: Encounter #${transitionTarget?.encounter_id}`}
        description="Enforces database integrity rules: completion is blocked if clinical orders remain pending."
      >
        <form onSubmit={handleStatusTransition} className="space-y-4">
          {transitionError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-start">
              <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="block font-semibold">Workflow Safety Rejection:</strong>
                <span>{transitionError}</span>
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Target Status *</label>
            <select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
            >
              <option value="OPEN">OPEN (Triage)</option>
              <option value="IN_PROGRESS">IN_PROGRESS (Clinical Examination)</option>
              <option value="AWAITING_RESULTS">AWAITING_RESULTS (Orders Dispatched)</option>
              <option value="COMPLETED">COMPLETED (Signoff & Discharge)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Clinical Signoff Notes</label>
            <textarea
              rows={3}
              placeholder="Summary of evaluation, examination findings, and follow-up plan..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setTransitionTarget(null)}
              className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg shadow-sm disabled:opacity-50"
            >
              {isSubmitting ? 'Validating...' : 'Apply Transition'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Encounter Inspection Modal */}
      <Modal
        isOpen={!!selectedEncounter}
        onClose={() => setSelectedEncounter(null)}
        title={selectedEncounter ? `Encounter #${selectedEncounter.encounter_id} - ${selectedEncounter.department}` : ''}
        description={selectedEncounter ? `Patient: ${selectedEncounter.patient_name} (${selectedEncounter.patient_mrn})` : ''}
        maxWidth="max-w-3xl"
      >
        {selectedEncounter && (
          <div className="space-y-6 text-xs">
            {/* Meta summary */}
            <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 grid grid-cols-3 gap-3">
              <div>
                <span className="text-slate-400 block">Status</span>
                <Badge status={selectedEncounter.status} size="sm" />
              </div>
              <div>
                <span className="text-slate-400 block">Clinician</span>
                <span className="font-semibold text-slate-800">{selectedEncounter.provider_name}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Start Time</span>
                <span className="font-mono text-slate-700">{selectedEncounter.start_time.replace('T', ' ')}</span>
              </div>
            </div>

            {/* Clinical Notes */}
            <div>
              <h4 className="font-semibold text-slate-900 uppercase tracking-wider mb-1">Clinical Documentation</h4>
              <p className="p-3 bg-slate-50 rounded-lg text-slate-700 leading-relaxed border border-slate-100">
                {selectedEncounter.clinical_notes || 'No clinical notes recorded.'}
              </p>
            </div>

            {/* Linked Diagnostic Orders */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-semibold text-slate-900 uppercase tracking-wider">
                  Diagnostic Orders ({encounterOrders.length})
                </h4>
                {selectedEncounter.status !== 'COMPLETED' && (
                  <button
                    onClick={() => setIsOrderOpen(true)}
                    className="inline-flex items-center px-2 py-1 bg-teal-50 text-teal-700 border border-teal-200 rounded font-semibold text-[11px]"
                  >
                    <Plus className="w-3 h-3 mr-1" /> Place Lab Order
                  </button>
                )}
              </div>

              {detailLoading ? (
                <div className="text-center py-4 text-slate-400">Loading orders...</div>
              ) : encounterOrders.length === 0 ? (
                <div className="p-3 bg-slate-50 rounded text-center text-slate-400">No laboratory orders placed.</div>
              ) : (
                <div className="space-y-1.5">
                  {encounterOrders.map(o => (
                    <div key={o.order_id} className="p-2.5 rounded border border-slate-200 bg-white flex items-center justify-between">
                      <div>
                        <span className="font-semibold text-slate-900">{o.order_code}</span> - {o.order_name}
                        <span className="ml-2 text-[10px] text-slate-400">({o.priority})</span>
                      </div>
                      <Badge status={o.order_status} size="sm" />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                onClick={() => setSelectedEncounter(null)}
                className="px-4 py-2 bg-slate-800 text-white font-semibold rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Place Order Modal */}
      <Modal
        isOpen={isOrderOpen}
        onClose={() => setIsOrderOpen(false)}
        title="Place Diagnostic Order"
        description="Requisition a laboratory order attached to this active encounter."
      >
        <form onSubmit={handleCreateOrder} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Laboratory Test</label>
            <select
              value={orderForm.order_code}
              onChange={(e) => {
                const names: Record<string, string> = {
                  CBC: 'Complete Blood Count',
                  BMP: 'Basic Metabolic Panel',
                  LIPID: 'Lipid Profile Panel',
                  TSH: 'Thyroid Stimulating Hormone',
                  HBA1C: 'Hemoglobin A1c Glycated',
                  UA: 'Urinalysis Complete'
                };
                setOrderForm({
                  ...orderForm,
                  order_code: e.target.value,
                  order_name: names[e.target.value] || e.target.value
                });
              }}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
            >
              <option value="CBC">Complete Blood Count (CBC)</option>
              <option value="BMP">Basic Metabolic Panel (BMP)</option>
              <option value="LIPID">Lipid Profile Panel (LIPID)</option>
              <option value="TSH">Thyroid Stimulating Hormone (TSH)</option>
              <option value="HBA1C">Hemoglobin A1c Glycated (HBA1C)</option>
              <option value="UA">Urinalysis Complete (UA)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Priority</label>
            <select
              value={orderForm.priority}
              onChange={(e) => setOrderForm({ ...orderForm, priority: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
            >
              <option value="ROUTINE">ROUTINE</option>
              <option value="URGENT">URGENT</option>
              <option value="STAT">STAT (Emergency Priority)</option>
            </select>
          </div>

          <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsOrderOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg"
            >
              Dispatch Order
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
