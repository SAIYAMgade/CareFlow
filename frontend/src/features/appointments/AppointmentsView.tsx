import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Appointment } from '../../types';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Calendar, Plus, UserCheck, XCircle, Clock, AlertCircle } from 'lucide-react';

export const AppointmentsView: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Check in confirmation
  const [checkInTarget, setCheckInTarget] = useState<Appointment | null>(null);
  const [checkInMsg, setCheckInMsg] = useState<string | null>(null);

  // Cancellation modal
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null);
  const [cancelReason, setCancelReason] = useState('');
  const [cancelError, setCancelError] = useState<string | null>(null);

  // Reschedule modal
  const [rescheduleTarget, setRescheduleTarget] = useState<Appointment | null>(null);
  const [newTime, setNewTime] = useState('');
  const [rescheduleError, setRescheduleError] = useState<string | null>(null);

  // Create Appointment modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createForm, setCreateForm] = useState({
    patient_id: 1,
    appointment_time: '',
    appointment_type: 'FOLLOW_UP',
    department: 'Cardiology',
    provider_name: 'Dr. Elena Rostova, MD'
  });
  const [createError, setCreateError] = useState<string | null>(null);

  const fetchAppointments = async () => {
    try {
      setLoading(true);
      const res = await api.getAppointments({
        date: dateFilter || undefined,
        department: departmentFilter || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 15
      });
      setAppointments(res.items);
      setTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAppointments();
  }, [page, departmentFilter, statusFilter, dateFilter]);

  const handleCheckIn = async () => {
    if (!checkInTarget) return;
    try {
      const res = await api.checkInAppointment(checkInTarget.appointment_id, 'FRONT_DESK_KIOSK');
      setCheckInMsg(`Patient checked in! Auto-generated Encounter ID #${res.encounter_id}`);
      setTimeout(() => {
        setCheckInTarget(null);
        setCheckInMsg(null);
        fetchAppointments();
      }, 1500);
    } catch (err: any) {
      alert(err.message || 'Check-in failed');
    }
  };

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancelTarget) return;
    setCancelError(null);
    try {
      await api.cancelAppointment(cancelTarget.appointment_id, cancelReason);
      setCancelTarget(null);
      setCancelReason('');
      fetchAppointments();
    } catch (err: any) {
      setCancelError(err.message || 'Failed to cancel appointment');
    }
  };

  const handleRescheduleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rescheduleTarget) return;
    setRescheduleError(null);
    try {
      await api.rescheduleAppointment(rescheduleTarget.appointment_id, newTime);
      setRescheduleTarget(null);
      setNewTime('');
      fetchAppointments();
    } catch (err: any) {
      setRescheduleError(err.message || 'Failed to reschedule');
    }
  };

  const handleCreateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreateError(null);
    try {
      await api.createAppointment(createForm);
      setIsCreateOpen(false);
      fetchAppointments();
    } catch (err: any) {
      setCreateError(err.message || 'Failed to book appointment');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Appointment Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Operational appointment scheduling, kiosk check-in workflow, and atomic encounter initialization.
          </p>
        </div>
        <button
          onClick={() => setIsCreateOpen(true)}
          className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors self-start sm:self-auto"
        >
          <Plus className="w-4 h-4 mr-2" />
          Book Appointment
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => { setDateFilter(e.target.value); setPage(1); }}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs font-mono text-slate-700"
          />
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
            <option value="SCHEDULED">Scheduled</option>
            <option value="CHECKED_IN">Checked In</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="COMPLETED">Completed</option>
            <option value="CANCELLED">Cancelled</option>
            <option value="NO_SHOW">No Show</option>
          </select>
        </div>
        <span className="text-xs text-slate-500 font-mono">{total} Appointment{total === 1 ? '' : 's'}</span>
      </div>

      {/* Appointments Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">ID / Time</th>
                <th className="px-5 py-3.5">Patient Details</th>
                <th className="px-5 py-3.5">Department</th>
                <th className="px-5 py-3.5">Assigned Clinician</th>
                <th className="px-5 py-3.5">Status</th>
                <th className="px-5 py-3.5">Check-In Arrival</th>
                <th className="px-5 py-3.5 text-right">Workflow Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600 mx-auto"></div>
                  </td>
                </tr>
              ) : appointments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    No appointments found matching current filters.
                  </td>
                </tr>
              ) : (
                appointments.map((appt) => (
                  <tr key={appt.appointment_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="font-mono text-xs font-semibold text-slate-900">#{appt.appointment_id}</div>
                      <div className="text-xs text-slate-500">{appt.appointment_time.replace('T', ' ')}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <div className="font-medium text-slate-900">{appt.patient_name}</div>
                      <div className="font-mono text-[11px] text-teal-700">{appt.patient_mrn}</div>
                    </td>
                    <td className="px-5 py-3.5 text-xs text-slate-700">{appt.department}</td>
                    <td className="px-5 py-3.5 text-xs text-slate-600">{appt.provider_name}</td>
                    <td className="px-5 py-3.5">
                      <Badge status={appt.status} />
                    </td>
                    <td className="px-5 py-3.5 font-mono text-xs text-slate-500">
                      {appt.check_in_time ? appt.check_in_time.replace('T', ' ') : '—'}
                    </td>
                    <td className="px-5 py-3.5 text-right space-x-2">
                      {appt.status === 'SCHEDULED' && (
                        <>
                          <button
                            onClick={() => setCheckInTarget(appt)}
                            className="inline-flex items-center px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-700 text-xs font-semibold rounded-md border border-emerald-200 transition-colors"
                          >
                            <UserCheck className="w-3.5 h-3.5 mr-1" /> Check In
                          </button>
                          <button
                            onClick={() => { setRescheduleTarget(appt); setNewTime(appt.appointment_time); }}
                            className="text-xs text-slate-500 hover:text-slate-800"
                          >
                            Reschedule
                          </button>
                          <button
                            onClick={() => setCancelTarget(appt)}
                            className="text-xs text-rose-500 hover:text-rose-700"
                          >
                            Cancel
                          </button>
                        </>
                      )}
                      {appt.status === 'CHECKED_IN' && (
                        <span className="text-xs text-amber-600 font-semibold flex items-center justify-end">
                          <Clock className="w-3.5 h-3.5 mr-1" /> In Waiting Room
                        </span>
                      )}
                      {appt.status === 'COMPLETED' && (
                        <span className="text-xs text-slate-400">Visit Concluded</span>
                      )}
                      {appt.status === 'CANCELLED' && (
                        <span className="text-xs text-rose-400 italic" title={appt.cancel_reason}>
                          {appt.cancel_reason || 'Cancelled'}
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

      {/* Check In Confirmation Modal */}
      <Modal
        isOpen={!!checkInTarget}
        onClose={() => setCheckInTarget(null)}
        title="Confirm Patient Reception Arrival"
        description="Executes atomic PL/SQL check_in_patient workflow: updates appointment and opens clinical encounter."
      >
        {checkInTarget && (
          <div className="space-y-4">
            <div className="p-4 bg-teal-50 border border-teal-200 rounded-lg text-xs space-y-1 text-teal-900">
              <div><strong>Patient:</strong> {checkInTarget.patient_name} ({checkInTarget.patient_mrn})</div>
              <div><strong>Appointment:</strong> #{checkInTarget.appointment_id} • {checkInTarget.department}</div>
              <div><strong>Clinician:</strong> {checkInTarget.provider_name}</div>
            </div>

            {checkInMsg ? (
              <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold rounded-lg">
                ✓ {checkInMsg}
              </div>
            ) : (
              <p className="text-xs text-slate-600">
                Are you sure you want to mark this patient as <strong>CHECKED_IN</strong>? This will record the arrival timestamp and automatically create an OPEN encounter in clinical triage.
              </p>
            )}

            {!checkInMsg && (
              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setCheckInTarget(null)}
                  className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleCheckIn}
                  className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg"
                >
                  Confirm Arrival
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>

      {/* Cancellation Modal */}
      <Modal
        isOpen={!!cancelTarget}
        onClose={() => setCancelTarget(null)}
        title="Cancel Appointment"
        description="Records cancellation reason and updates clinic status history."
      >
        <form onSubmit={handleCancelSubmit} className="space-y-4">
          {cancelError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              <span>{cancelError}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Cancellation Reason *</label>
            <input
              type="text"
              required
              placeholder="e.g. Patient sick, transport issue, physician emergency"
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
            />
          </div>
          <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setCancelTarget(null)}
              className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
            >
              Back
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg"
            >
              Confirm Cancellation
            </button>
          </div>
        </form>
      </Modal>

      {/* Reschedule Modal */}
      <Modal
        isOpen={!!rescheduleTarget}
        onClose={() => setRescheduleTarget(null)}
        title="Reschedule Appointment"
        description="Updates scheduled date and time with audit correlation tracking."
      >
        <form onSubmit={handleRescheduleSubmit} className="space-y-4">
          {rescheduleError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              <span>{rescheduleError}</span>
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">New Appointment Date & Time *</label>
            <input
              type="datetime-local"
              required
              value={newTime}
              onChange={(e) => setNewTime(e.target.value)}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
            />
          </div>
          <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setRescheduleTarget(null)}
              className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
            >
              Back
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg"
            >
              Save New Schedule
            </button>
          </div>
        </form>
      </Modal>

      {/* Book New Appointment Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Book New Appointment"
        description="Schedule a simulated patient encounter."
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          {createError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center">
              <AlertCircle className="w-4 h-4 mr-2" />
              <span>{createError}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Patient ID (1 to 50)</label>
            <input
              type="number"
              min="1"
              max="100"
              required
              value={createForm.patient_id}
              onChange={(e) => setCreateForm({ ...createForm, patient_id: parseInt(e.target.value) || 1 })}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Appointment Time *</label>
            <input
              type="datetime-local"
              required
              value={createForm.appointment_time}
              onChange={(e) => setCreateForm({ ...createForm, appointment_time: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Department</label>
              <select
                value={createForm.department}
                onChange={(e) => setCreateForm({ ...createForm, department: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
              >
                <option value="Cardiology">Cardiology</option>
                <option value="Endocrinology">Endocrinology</option>
                <option value="Family Medicine">Family Medicine</option>
                <option value="Pediatrics">Pediatrics</option>
                <option value="Urgent Care">Urgent Care</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Visit Type</label>
              <select
                value={createForm.appointment_type}
                onChange={(e) => setCreateForm({ ...createForm, appointment_type: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
              >
                <option value="FOLLOW_UP">Follow Up</option>
                <option value="NEW_PATIENT">New Patient</option>
                <option value="CONSULTATION">Consultation</option>
                <option value="PROCEDURE">Procedure</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Provider Name</label>
            <input
              type="text"
              required
              value={createForm.provider_name}
              onChange={(e) => setCreateForm({ ...createForm, provider_name: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsCreateOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg"
            >
              Book Appointment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
