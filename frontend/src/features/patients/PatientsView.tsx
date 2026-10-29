import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Patient, Observation } from '../../types';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { Search, UserPlus, Eye, AlertCircle, Phone, Mail, MapPin } from 'lucide-react';

export const PatientsView: React.FC = () => {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);

  // Registration modal
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [regForm, setRegForm] = useState({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: 'FEMALE',
    phone: '',
    email: '',
    address: ''
  });
  const [regError, setRegError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Detail / Chart Modal
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [patientVitals, setPatientVitals] = useState<Observation[]>([]);
  const [detailLoading, setDetailLoading] = useState(false);

  const fetchPatients = async () => {
    try {
      setLoading(true);
      const res = await api.getPatients({
        search: search || undefined,
        status: statusFilter || undefined,
        page,
        page_size: 15
      });
      setPatients(res.items);
      setTotal(res.total);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchPatients();
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setRegError(null);
    setIsSubmitting(true);
    try {
      await api.createPatient(regForm);
      setIsRegisterOpen(false);
      setRegForm({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: 'FEMALE',
        phone: '',
        email: '',
        address: ''
      });
      fetchPatients();
    } catch (err: any) {
      setRegError(err.message || 'Failed to register patient.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openPatientDetail = async (patient: Patient) => {
    setSelectedPatient(patient);
    setDetailLoading(true);
    try {
      const vitals = await api.getObservations({ patient_id: patient.patient_id });
      setPatientVitals(vitals);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Patient Registry</h1>
          <p className="text-sm text-slate-500 mt-1">
            Search, register, and audit simulated patient demographic records and unique MRNs.
          </p>
        </div>
        <button
          onClick={() => setIsRegisterOpen(true)}
          className="inline-flex items-center px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-lg shadow-sm transition-colors self-start sm:self-auto"
        >
          <UserPlus className="w-4 h-4 mr-2" />
          Register Patient
        </button>
      </div>

      {/* Filter / Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex-1 flex items-center space-x-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Filter by Name or MRN (e.g. MRN-2026-10001)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-800 focus:bg-white focus:outline-none focus:ring-1 focus:ring-teal-600"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-slate-800 text-white text-sm font-medium rounded-lg hover:bg-slate-700 transition-colors"
          >
            Search
          </button>
        </form>

        <div className="flex items-center space-x-3">
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="MERGED">Merged</option>
          </select>
          <span className="text-xs text-slate-500 font-mono">
            {total} Record{total === 1 ? '' : 's'}
          </span>
        </div>
      </div>

      {/* Patient Table */}
      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
              <tr>
                <th className="px-5 py-3.5">MRN</th>
                <th className="px-5 py-3.5">Patient Name</th>
                <th className="px-5 py-3.5">Date of Birth</th>
                <th className="px-5 py-3.5">Sex</th>
                <th className="px-5 py-3.5">Contact Details</th>
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
              ) : patients.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-12 text-slate-400">
                    No patient records matched the search criteria.
                  </td>
                </tr>
              ) : (
                patients.map((p) => (
                  <tr key={p.patient_id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5 font-mono text-xs font-semibold text-teal-700">{p.mrn}</td>
                    <td className="px-5 py-3.5 font-medium text-slate-900">
                      {p.last_name}, {p.first_name}
                    </td>
                    <td className="px-5 py-3.5 text-slate-600 font-mono text-xs">{p.date_of_birth}</td>
                    <td className="px-5 py-3.5 text-slate-600 capitalize text-xs">{p.gender.toLowerCase()}</td>
                    <td className="px-5 py-3.5 text-xs text-slate-500">
                      <div>{p.phone || '—'}</div>
                      <div className="text-[11px] text-slate-400 truncate max-w-xs">{p.email || '—'}</div>
                    </td>
                    <td className="px-5 py-3.5">
                      <Badge status={p.status} />
                    </td>
                    <td className="px-5 py-3.5 text-right">
                      <button
                        onClick={() => openPatientDetail(p)}
                        className="inline-flex items-center text-xs font-semibold text-teal-600 hover:text-teal-800 hover:underline"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1" /> View Chart
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

      {/* Registration Modal */}
      <Modal
        isOpen={isRegisterOpen}
        onClose={() => setIsRegisterOpen(false)}
        title="Register New Patient"
        description="Creates a validated patient entity and generates an Oracle unique MRN."
      >
        <form onSubmit={handleRegisterSubmit} className="space-y-4">
          {regError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center">
              <AlertCircle className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{regError}</span>
            </div>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">First Name *</label>
              <input
                type="text"
                required
                value={regForm.first_name}
                onChange={(e) => setRegForm({ ...regForm, first_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Last Name *</label>
              <input
                type="text"
                required
                value={regForm.last_name}
                onChange={(e) => setRegForm({ ...regForm, last_name: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Date of Birth *</label>
              <input
                type="date"
                required
                value={regForm.date_of_birth}
                onChange={(e) => setRegForm({ ...regForm, date_of_birth: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Administrative Sex</label>
              <select
                value={regForm.gender}
                onChange={(e) => setRegForm({ ...regForm, gender: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
              >
                <option value="FEMALE">Female</option>
                <option value="MALE">Male</option>
                <option value="OTHER">Other</option>
                <option value="UNKNOWN">Unknown</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Phone Number</label>
              <input
                type="tel"
                placeholder="555-0100"
                value={regForm.phone}
                onChange={(e) => setRegForm({ ...regForm, phone: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <input
                type="email"
                placeholder="patient@synthetic-careflow.org"
                value={regForm.email}
                onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Address</label>
            <input
              type="text"
              placeholder="123 Health Ave, Metro City"
              value={regForm.address}
              onChange={(e) => setRegForm({ ...regForm, address: e.target.value })}
              className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:bg-white focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={() => setIsRegisterOpen(false)}
              className="px-4 py-2 border border-slate-200 text-slate-700 text-sm font-medium rounded-lg hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-lg shadow-sm disabled:opacity-50"
            >
              {isSubmitting ? 'Registering...' : 'Register Patient'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Patient Detail / Chart Modal */}
      <Modal
        isOpen={!!selectedPatient}
        onClose={() => setSelectedPatient(null)}
        title={selectedPatient ? `${selectedPatient.last_name}, ${selectedPatient.first_name}` : ''}
        description={selectedPatient ? `Medical Record Number: ${selectedPatient.mrn}` : ''}
        maxWidth="max-w-2xl"
      >
        {selectedPatient && (
          <div className="space-y-6">
            {/* Demographics Card */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs">
              <div>
                <span className="text-slate-400 block">Date of Birth</span>
                <span className="font-semibold text-slate-800">{selectedPatient.date_of_birth}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Sex</span>
                <span className="font-semibold text-slate-800 capitalize">{selectedPatient.gender.toLowerCase()}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Record Status</span>
                <Badge status={selectedPatient.status} size="sm" />
              </div>
              <div>
                <span className="text-slate-400 block">Phone</span>
                <span className="font-semibold text-slate-800">{selectedPatient.phone || 'None'}</span>
              </div>
              <div className="col-span-2">
                <span className="text-slate-400 block">Email</span>
                <span className="font-semibold text-slate-800 truncate block">{selectedPatient.email || 'None'}</span>
              </div>
            </div>

            {/* Vitals History */}
            <div>
              <h4 className="text-xs font-semibold text-slate-900 uppercase tracking-wider mb-2">
                Recorded Clinical Vitals & Observations
              </h4>
              {detailLoading ? (
                <div className="text-center py-6 text-xs text-slate-400">Loading vitals...</div>
              ) : patientVitals.length === 0 ? (
                <div className="p-4 bg-slate-50 rounded-lg text-xs text-slate-500 text-center">
                  No vital signs recorded for this patient.
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {patientVitals.map(v => (
                    <div key={v.observation_id} className="p-2.5 rounded-lg border border-slate-200/80 bg-white flex justify-between items-center text-xs">
                      <div>
                        <span className="font-semibold text-slate-800">{v.observation_code}</span>
                        <span className="text-[11px] text-slate-400 block">{v.source}</span>
                      </div>
                      <span className="font-mono font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                        {v.value_numeric || v.value_text} {v.unit}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-100">
              <button
                onClick={() => setSelectedPatient(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold rounded-lg"
              >
                Close Chart
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
