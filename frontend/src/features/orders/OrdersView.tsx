import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { Order, Result } from '../../types';
import { Badge } from '../../components/common/Badge';
import { Modal } from '../../components/common/Modal';
import { FlaskConical, ClipboardCheck, AlertCircle, CheckCircle, Clock } from 'lucide-react';

export const OrdersView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'orders' | 'results'>('orders');

  // Orders State
  const [orders, setOrders] = useState<Order[]>([]);
  const [orderTotal, setOrderTotal] = useState(0);
  const [orderPage, setOrderPage] = useState(1);
  const [orderPriority, setOrderPriority] = useState('');
  const [orderStatus, setOrderStatus] = useState('');
  const [ordersLoading, setOrdersLoading] = useState(true);

  // Results State
  const [results, setResults] = useState<Result[]>([]);
  const [resultTotal, setResultTotal] = useState(0);
  const [resultPage, setResultPage] = useState(1);
  const [resultStatus, setResultStatus] = useState('');
  const [abnormalOnly, setAbnormalOnly] = useState(false);
  const [resultsLoading, setResultsLoading] = useState(true);

  // Complete Order Modal
  const [targetOrder, setTargetOrder] = useState<Order | null>(null);
  const [resultForm, setResultForm] = useState({
    result_value: '',
    reference_range: '',
    unit: '',
    abnormal_flag: 'NORMAL'
  });
  const [completeError, setCompleteError] = useState<string | null>(null);

  // Review Result Modal
  const [targetResult, setTargetResult] = useState<Result | null>(null);
  const [reviewerName, setReviewerName] = useState('Dr. Elena Rostova, MD');
  const [reviewError, setReviewError] = useState<string | null>(null);

  const fetchOrders = async () => {
    try {
      setOrdersLoading(true);
      const res = await api.getOrders({
        priority: orderPriority || undefined,
        status: orderStatus || undefined,
        page: orderPage,
        page_size: 15
      });
      setOrders(res.items);
      setOrderTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setOrdersLoading(false);
    }
  };

  const fetchResults = async () => {
    try {
      setResultsLoading(true);
      const res = await api.getResults({
        result_status: resultStatus || undefined,
        abnormal_only: abnormalOnly,
        page: resultPage,
        page_size: 15
      });
      setResults(res.items);
      setResultTotal(res.total);
    } catch (err) {
      console.error(err);
    } finally {
      setResultsLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'orders') fetchOrders();
    else fetchResults();
  }, [activeTab, orderPage, orderPriority, orderStatus, resultPage, resultStatus, abnormalOnly]);

  const handleCompleteOrderSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetOrder) return;
    setCompleteError(null);
    try {
      await api.completeOrder(targetOrder.order_id, {
        result_value: resultForm.result_value,
        reference_range: resultForm.reference_range || undefined,
        unit: resultForm.unit || undefined,
        abnormal_flag: resultForm.abnormal_flag,
        actor: 'Lab-Tech-Automation'
      });
      setTargetOrder(null);
      setResultForm({ result_value: '', reference_range: '', unit: '', abnormal_flag: 'NORMAL' });
      fetchOrders();
    } catch (err: any) {
      setCompleteError(err.message || 'Failed to complete order');
    }
  };

  const handleReviewResultSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!targetResult) return;
    setReviewError(null);
    try {
      await api.reviewResult(targetResult.result_id, reviewerName);
      setTargetResult(null);
      fetchResults();
    } catch (err: any) {
      setReviewError(err.message || 'Failed to sign off result');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Orders & Results Management</h1>
          <p className="text-sm text-slate-500 mt-1">
            Diagnostic order dispatching, laboratory result posting, and physician review signoff workflows.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('orders')}
          className={`flex items-center px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'orders'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <FlaskConical className="w-4 h-4 mr-2" />
          Clinical Orders ({orderTotal})
        </button>
        <button
          onClick={() => setActiveTab('results')}
          className={`flex items-center px-4 py-2.5 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === 'results'
              ? 'border-teal-600 text-teal-700'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <ClipboardCheck className="w-4 h-4 mr-2" />
          Diagnostic Results Review ({resultTotal})
        </button>
      </div>

      {/* TAB 1: ORDERS */}
      {activeTab === 'orders' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={orderPriority}
                onChange={(e) => { setOrderPriority(e.target.value); setOrderPage(1); }}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
              >
                <option value="">All Priorities</option>
                <option value="STAT">STAT (Emergency)</option>
                <option value="URGENT">URGENT</option>
                <option value="ROUTINE">ROUTINE</option>
              </select>
              <select
                value={orderStatus}
                onChange={(e) => { setOrderStatus(e.target.value); setOrderPage(1); }}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
              >
                <option value="">All Statuses</option>
                <option value="ORDERED">ORDERED (Pending)</option>
                <option value="IN_PROGRESS">IN_PROGRESS</option>
                <option value="COMPLETED">COMPLETED</option>
              </select>
            </div>
            <span className="text-xs text-slate-500 font-mono">{orderTotal} Total Orders</span>
          </div>

          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3.5">Order ID</th>
                    <th className="px-5 py-3.5">Test Details</th>
                    <th className="px-5 py-3.5">Patient Details</th>
                    <th className="px-5 py-3.5">Priority</th>
                    <th className="px-5 py-3.5">Ordered Time</th>
                    <th className="px-5 py-3.5">Status</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {ordersLoading ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-slate-400">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600 mx-auto"></div>
                      </td>
                    </tr>
                  ) : orders.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="text-center py-12 text-slate-400">
                        No orders matching current filters.
                      </td>
                    </tr>
                  ) : (
                    orders.map((ord) => (
                      <tr key={ord.order_id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-5 py-3.5 font-mono text-xs font-semibold text-slate-900">
                          ORD-#{ord.order_id}
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="font-semibold text-slate-900">{ord.order_code}</div>
                          <div className="text-xs text-slate-500">{ord.order_name}</div>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="font-medium text-slate-900">{ord.patient_name}</div>
                          <div className="font-mono text-[11px] text-teal-700">{ord.patient_mrn}</div>
                        </td>
                        <td className="px-5 py-3.5">
                          <Badge status={ord.priority} />
                        </td>
                        <td className="px-5 py-3.5 font-mono text-xs text-slate-500">
                          {ord.ordered_at.substring(0, 16).replace('T', ' ')}
                        </td>
                        <td className="px-5 py-3.5">
                          <Badge status={ord.order_status} />
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          {ord.order_status !== 'COMPLETED' ? (
                            <button
                              onClick={() => {
                                setTargetOrder(ord);
                                setCompleteError(null);
                              }}
                              className="px-2.5 py-1 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded border border-teal-200 text-xs font-semibold transition-colors"
                            >
                              Post Result
                            </button>
                          ) : (
                            <span className="text-xs text-emerald-600 font-semibold flex items-center justify-end">
                              <CheckCircle className="w-3.5 h-3.5 mr-1" /> Results Logged
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
              <span>Showing {(orderPage - 1) * 15 + 1} to {Math.min(orderPage * 15, orderTotal)} of {orderTotal}</span>
              <div className="flex items-center space-x-2">
                <button
                  disabled={orderPage <= 1}
                  onClick={() => setOrderPage(p => Math.max(p - 1, 1))}
                  className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="font-mono text-slate-700 font-semibold">{orderPage}</span>
                <button
                  disabled={orderPage * 15 >= orderTotal}
                  onClick={() => setOrderPage(p => p + 1)}
                  className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: RESULTS */}
      {activeTab === 'results' && (
        <div className="space-y-4">
          <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap items-center gap-3">
              <select
                value={resultStatus}
                onChange={(e) => { setResultStatus(e.target.value); setResultPage(1); }}
                className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-xs text-slate-700"
              >
                <option value="">All Review States</option>
                <option value="PENDING_REVIEW">Pending Review</option>
                <option value="REVIEWED">Reviewed & Signed Off</option>
              </select>
              <label className="flex items-center space-x-2 text-xs font-medium text-slate-700 cursor-pointer">
                <input
                  type="checkbox"
                  checked={abnormalOnly}
                  onChange={(e) => { setAbnormalOnly(e.target.checked); setResultPage(1); }}
                  className="rounded text-teal-600 focus:ring-teal-500"
                />
                <span>Abnormal Flags Only (CRITICAL/HIGH/LOW)</span>
              </label>
            </div>
            <span className="text-xs text-slate-500 font-mono">{resultTotal} Total Results</span>
          </div>

          <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50/80 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3.5">Result ID / Time</th>
                    <th className="px-5 py-3.5">Test Code</th>
                    <th className="px-5 py-3.5">Patient Details</th>
                    <th className="px-5 py-3.5">Result Value</th>
                    <th className="px-5 py-3.5">Reference Range</th>
                    <th className="px-5 py-3.5">Abnormal Flag</th>
                    <th className="px-5 py-3.5">Review Status</th>
                    <th className="px-5 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {resultsLoading ? (
                    <tr>
                      <td colSpan={8} className="text-center py-12 text-slate-400">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600 mx-auto"></div>
                      </td>
                    </tr>
                  ) : results.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="text-center py-12 text-slate-400">
                        No diagnostic results found matching filters.
                      </td>
                    </tr>
                  ) : (
                    results.map((res) => (
                      <tr key={res.result_id} className="hover:bg-slate-50/60 transition-colors">
                        <td className="px-5 py-3.5">
                          <div className="font-mono text-xs font-semibold text-slate-900">RES-#{res.result_id}</div>
                          <div className="text-[11px] text-slate-400 font-mono">{res.result_time.substring(0, 16).replace('T', ' ')}</div>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="font-semibold text-slate-900">{res.order_code}</div>
                          <div className="text-xs text-slate-500">{res.order_name}</div>
                        </td>
                        <td className="px-5 py-3.5">
                          <div className="font-medium text-slate-900">{res.patient_name}</div>
                          <div className="font-mono text-[11px] text-teal-700">{res.patient_mrn}</div>
                        </td>
                        <td className="px-5 py-3.5 font-mono text-sm font-bold text-slate-900">
                          {res.result_value} <span className="text-xs font-normal text-slate-500">{res.unit}</span>
                        </td>
                        <td className="px-5 py-3.5 font-mono text-xs text-slate-500">
                          {res.reference_range || 'Standard'}
                        </td>
                        <td className="px-5 py-3.5">
                          <Badge status={res.abnormal_flag} />
                        </td>
                        <td className="px-5 py-3.5">
                          <Badge status={res.result_status} />
                          {res.reviewed_by && (
                            <div className="text-[10px] text-slate-400 truncate max-w-[120px]">{res.reviewed_by}</div>
                          )}
                        </td>
                        <td className="px-5 py-3.5 text-right">
                          {res.result_status === 'PENDING_REVIEW' ? (
                            <button
                              onClick={() => {
                                setTargetResult(res);
                                setReviewError(null);
                              }}
                              className="px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 rounded border border-amber-200 text-xs font-semibold transition-colors"
                            >
                              Sign Off
                            </button>
                          ) : (
                            <span className="text-xs text-slate-400 italic">Signed</span>
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
              <span>Showing {(resultPage - 1) * 15 + 1} to {Math.min(resultPage * 15, resultTotal)} of {resultTotal}</span>
              <div className="flex items-center space-x-2">
                <button
                  disabled={resultPage <= 1}
                  onClick={() => setResultPage(p => Math.max(p - 1, 1))}
                  className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
                >
                  Previous
                </button>
                <span className="font-mono text-slate-700 font-semibold">{resultPage}</span>
                <button
                  disabled={resultPage * 15 >= resultTotal}
                  onClick={() => setResultPage(p => p + 1)}
                  className="px-3 py-1 bg-white border border-slate-200 rounded disabled:opacity-40"
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Complete Order (Post Lab Result) Modal */}
      <Modal
        isOpen={!!targetOrder}
        onClose={() => setTargetOrder(null)}
        title={`Post Result for Order #${targetOrder?.order_id}`}
        description="Creates laboratory RESULT and completes order via PL/SQL atomic complete_order_with_result transaction."
      >
        {targetOrder && (
          <form onSubmit={handleCompleteOrderSubmit} className="space-y-4">
            {completeError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center">
                <AlertCircle className="w-4 h-4 mr-2" />
                <span>{completeError}</span>
              </div>
            )}

            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-1">
              <div><strong>Test:</strong> {targetOrder.order_name} ({targetOrder.order_code})</div>
              <div><strong>Patient:</strong> {targetOrder.patient_name}</div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Result Value *</label>
              <input
                type="text"
                required
                placeholder="e.g. 14.2 or Positive or 118"
                value={resultForm.result_value}
                onChange={(e) => setResultForm({ ...resultForm, result_value: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Unit</label>
                <input
                  type="text"
                  placeholder="e.g. mg/dL, %, 10^3/uL"
                  value={resultForm.unit}
                  onChange={(e) => setResultForm({ ...resultForm, unit: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Reference Range</label>
                <input
                  type="text"
                  placeholder="e.g. 70-99 or <5.7"
                  value={resultForm.reference_range}
                  onChange={(e) => setResultForm({ ...resultForm, reference_range: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Abnormal Flag</label>
              <select
                value={resultForm.abnormal_flag}
                onChange={(e) => setResultForm({ ...resultForm, abnormal_flag: e.target.value })}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
              >
                <option value="NORMAL">NORMAL</option>
                <option value="HIGH">HIGH</option>
                <option value="LOW">LOW</option>
                <option value="CRITICAL">CRITICAL (Immediate Notification)</option>
              </select>
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setTargetOrder(null)}
                className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold rounded-lg"
              >
                Post Result & Complete
              </button>
            </div>
          </form>
        )}
      </Modal>

      {/* Review Result Signoff Modal */}
      <Modal
        isOpen={!!targetResult}
        onClose={() => setTargetResult(null)}
        title="Physician Clinical Signoff"
        description="Records physician verification and marks result REVIEWED in audit trail."
      >
        {targetResult && (
          <form onSubmit={handleReviewResultSubmit} className="space-y-4">
            {reviewError && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-xs flex items-center">
                <AlertCircle className="w-4 h-4 mr-2" />
                <span>{reviewError}</span>
              </div>
            )}

            <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg text-xs space-y-2">
              <div className="flex justify-between items-center">
                <span className="font-semibold text-slate-900">{targetResult.order_name}</span>
                <Badge status={targetResult.abnormal_flag} size="sm" />
              </div>
              <div className="text-base font-mono font-bold text-slate-900">
                {targetResult.result_value} {targetResult.unit}
              </div>
              <div className="text-slate-500">Reference: {targetResult.reference_range || 'Normal'}</div>
              <div className="text-slate-500">Patient: {targetResult.patient_name} ({targetResult.patient_mrn})</div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Reviewing Clinician Name</label>
              <input
                type="text"
                required
                value={reviewerName}
                onChange={(e) => setReviewerName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-sm"
              />
            </div>

            <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setTargetResult(null)}
                className="px-4 py-2 border border-slate-200 text-slate-700 text-xs font-medium rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg"
              >
                Sign Off & Close
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  );
};
