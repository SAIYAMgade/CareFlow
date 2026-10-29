import React, { useEffect, useState } from 'react';
import { api } from '../../api/client';
import { DashboardKpis, DashboardChartsResponse } from '../../types';
import { StatCard } from '../../components/common/StatCard';
import {
  Calendar, UserCheck, Clock, Stethoscope, CheckCircle2,
  FlaskConical, ClipboardCheck, ShieldAlert, AlertTriangle, ArrowRight
} from 'lucide-react';
import { NavItemKey } from '../../components/common/Sidebar';

interface DashboardViewProps {
  onNavigate: (tab: NavItemKey) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<DashboardKpis | null>(null);
  const [charts, setCharts] = useState<DashboardChartsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [sData, cData] = await Promise.all([
        api.getStats(),
        api.getCharts()
      ]);
      setStats(sData);
      setCharts(cData);
    } catch (err: any) {
      setError(err.message || 'Failed to load dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-brand-700"></div>
      </div>
    );
  }

  if (error || !stats || !charts) {
    return (
      <div className="p-6 bg-rose-50 border border-rose-200 rounded-xl text-rose-800">
        <h4 className="font-semibold flex items-center">
          <AlertTriangle className="w-5 h-5 mr-2" />
          Dashboard Data Unavailable
        </h4>
        <p className="mt-1 text-sm">{error || 'Unable to load operational metrics from database.'}</p>
        <button
          onClick={loadData}
          className="mt-3 px-4 py-1.5 bg-rose-600 text-white text-xs font-semibold rounded-lg hover:bg-rose-700"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Clinic Operations Dashboard</h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time operational metrics, workflow progression, and diagnostic tracking derived directly from persisted records.
          </p>
        </div>
        <div className="text-xs text-slate-400 font-mono self-start sm:self-auto bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
          Source of Truth: <span className="text-emerald-700 font-semibold">Live Database</span>
        </div>
      </div>

      {/* Critical Alert Bar if Open DQ Issues */}
      {stats.open_data_quality_issues > 0 && (
        <div 
          onClick={() => onNavigate('data-quality')}
          className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-center justify-between cursor-pointer hover:bg-amber-100/80 transition-colors"
        >
          <div className="flex items-center space-x-3">
            <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0" />
            <div>
              <span className="text-sm font-semibold text-amber-900">
                {stats.open_data_quality_issues} Data Quality Exception(s) Require Staff Investigation
              </span>
              <p className="text-xs text-amber-700 mt-0.5">
                Timestamp discrepancies or incomplete workflow invariants detected. Click to open investigation workspace.
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold text-amber-800 flex items-center">
            Review Issues <ArrowRight className="w-4 h-4 ml-1" />
          </span>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Today's Appointments"
          value={stats.appointments_today}
          icon={Calendar}
          colorScheme="blue"
          subtext="Booked across all 5 departments"
          onClick={() => onNavigate('appointments')}
        />
        <StatCard
          label="Patients Checked In"
          value={stats.patients_checked_in}
          icon={UserCheck}
          colorScheme="emerald"
          subtext="Arrived at clinic reception"
          onClick={() => onNavigate('appointments')}
        />
        <StatCard
          label="Patients Waiting"
          value={stats.patients_waiting}
          icon={Clock}
          colorScheme="amber"
          subtext="Awaiting clinician triage"
          onClick={() => onNavigate('appointments')}
        />
        <StatCard
          label="Encounters In Progress"
          value={stats.encounters_in_progress}
          icon={Stethoscope}
          colorScheme="purple"
          subtext="Active clinical evaluations"
          onClick={() => onNavigate('encounters')}
        />
        <StatCard
          label="Encounters Completed"
          value={stats.encounters_completed_today}
          icon={CheckCircle2}
          colorScheme="emerald"
          subtext="Signed off today"
          onClick={() => onNavigate('encounters')}
        />
        <StatCard
          label="Orders Awaiting Results"
          value={stats.orders_awaiting_results}
          icon={FlaskConical}
          colorScheme="amber"
          subtext="In laboratory processing"
          onClick={() => onNavigate('orders')}
        />
        <StatCard
          label="Results Awaiting Review"
          value={stats.results_awaiting_review}
          icon={ClipboardCheck}
          colorScheme="rose"
          subtext="Pending physician signoff"
          onClick={() => onNavigate('orders')}
        />
        <StatCard
          label="Data Quality Exceptions"
          value={stats.open_data_quality_issues}
          icon={ShieldAlert}
          colorScheme="rose"
          subtext="Active integrity flags"
          onClick={() => onNavigate('data-quality')}
        />
      </div>

      {/* Operational Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Hourly Appointment Volume */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Appointment Volume by Hour</h3>
              <p className="text-xs text-slate-500">Scheduled vs. Checked In patient distribution</p>
            </div>
            <span className="text-xs font-mono text-slate-400">SELECT EXTRACT(HOUR FROM ...)</span>
          </div>

          <div className="h-64 flex items-end space-x-2 pt-6 pb-2 border-b border-slate-100">
            {charts.hourly_volume.length === 0 ? (
              <div className="w-full text-center text-sm text-slate-400 py-12">No appointment activity recorded.</div>
            ) : (
              charts.hourly_volume.map((item) => {
                const maxVal = Math.max(...charts.hourly_volume.map(v => v.scheduled), 1);
                const schedHeight = Math.max(Math.round((item.scheduled / maxVal) * 180), 8);
                const checkHeight = Math.max(Math.round((item.checked_in / maxVal) * 180), 4);
                return (
                  <div key={item.hour} className="flex-1 flex flex-col items-center group relative">
                    <div className="w-full flex items-end justify-center space-x-1">
                      <div 
                        style={{ height: `${schedHeight}px` }} 
                        className="w-2.5 sm:w-4 bg-slate-300 rounded-t group-hover:bg-slate-400 transition-colors"
                        title={`Hour ${item.hour}:00 - Scheduled: ${item.scheduled}`}
                      />
                      <div 
                        style={{ height: `${checkHeight}px` }} 
                        className="w-2.5 sm:w-4 bg-teal-600 rounded-t group-hover:bg-teal-500 transition-colors"
                        title={`Hour ${item.hour}:00 - Checked In: ${item.checked_in}`}
                      />
                    </div>
                    <span className="text-[10px] text-slate-500 font-mono mt-2">{item.hour}:00</span>
                  </div>
                );
              })
            )}
          </div>
          <div className="flex items-center justify-center space-x-6 mt-3 text-xs text-slate-600">
            <span className="flex items-center">
              <span className="w-3 h-3 bg-slate-300 rounded mr-1.5"></span> Scheduled
            </span>
            <span className="flex items-center">
              <span className="w-3 h-3 bg-teal-600 rounded mr-1.5"></span> Checked In
            </span>
          </div>
        </div>

        {/* Chart 2: Average Wait Time by Department */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Average Patient Wait Time (Minutes)</h3>
              <p className="text-xs text-slate-500">Duration from check-in to encounter start</p>
            </div>
            <span className="text-xs font-mono text-slate-400">AVG(start - checkin)</span>
          </div>

          <div className="space-y-4 pt-2">
            {charts.wait_time_by_dept.length === 0 ? (
              <div className="text-center text-sm text-slate-400 py-12">No wait time records logged yet.</div>
            ) : (
              charts.wait_time_by_dept.map((dept) => {
                const maxWait = Math.max(...charts.wait_time_by_dept.map(d => d.avg_wait_minutes), 30);
                const pct = Math.min(Math.round((dept.avg_wait_minutes / maxWait) * 100), 100);
                const isHigh = dept.avg_wait_minutes > 20;

                return (
                  <div key={dept.department} className="space-y-1">
                    <div className="flex items-center justify-between text-xs font-medium text-slate-700">
                      <span>{dept.department}</span>
                      <span className={`font-mono font-semibold ${isHigh ? 'text-amber-600' : 'text-slate-900'}`}>
                        {dept.avg_wait_minutes.toFixed(1)} mins
                      </span>
                    </div>
                    <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        style={{ width: `${pct}%` }}
                        className={`h-full rounded-full transition-all duration-500 ${
                          isHigh ? 'bg-amber-500' : 'bg-teal-600'
                        }`}
                      />
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Chart 3: Encounter Status Distribution */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Encounter Status Breakdown</h3>
              <p className="text-xs text-slate-500">Distribution of active vs. completed clinic visits</p>
            </div>
            <span className="text-xs font-mono text-slate-400">GROUP BY status</span>
          </div>

          <div className="space-y-3 pt-2">
            {charts.encounter_distribution.map((item) => {
              const totalEnc = charts.encounter_distribution.reduce((acc, curr) => acc + curr.count, 0) || 1;
              const pct = Math.round((item.count / totalEnc) * 100);
              return (
                <div key={item.status} className="flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-brand-700"></span>
                    <span className="font-medium text-slate-700">{item.status}</span>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="font-mono text-slate-500">{item.count}</span>
                    <span className="font-mono text-slate-400 w-10 text-right">({pct}%)</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Chart 4: Order Turnaround Time */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-semibold text-slate-900">Diagnostic Turnaround Time (Hours)</h3>
              <p className="text-xs text-slate-500">Average completion time per laboratory test</p>
            </div>
            <span className="text-xs font-mono text-slate-400">AVG(completed - ordered)</span>
          </div>

          <div className="space-y-3 pt-2">
            {charts.order_turnaround.map((ord) => (
              <div key={ord.order_code} className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-slate-50/70 border border-slate-100">
                <div>
                  <span className="font-semibold text-slate-800">{ord.order_code}</span>
                  <span className="text-slate-500 ml-2">({ord.order_name})</span>
                </div>
                <span className="font-mono font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200/60">
                  {ord.avg_turnaround_hours.toFixed(2)} hrs
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
