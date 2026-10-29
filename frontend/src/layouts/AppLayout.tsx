import React, { useState, useEffect } from 'react';
import { Sidebar, NavItemKey } from '../components/common/Sidebar';
import { Navbar } from '../components/common/Navbar';
import { DashboardView } from '../features/dashboard/DashboardView';
import { PatientsView } from '../features/patients/PatientsView';
import { AppointmentsView } from '../features/appointments/AppointmentsView';
import { EncountersView } from '../features/encounters/EncountersView';
import { OrdersView } from '../features/orders/OrdersView';
import { ReportsView } from '../features/reports/ReportsView';
import { DataQualityView } from '../features/data-quality/DataQualityView';
import { AuditView } from '../features/audit/AuditView';
import { HealthView } from '../features/health/HealthView';
import { api } from '../api/client';

export const AppLayout: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavItemKey>('dashboard');
  const [collapsed, setCollapsed] = useState(false);
  const [waitingCount, setWaitingCount] = useState(0);
  const [openDqCount, setOpenDqCount] = useState(0);

  const refreshBadges = async () => {
    try {
      const stats = await api.getStats();
      setWaitingCount(stats.patients_waiting);
      setOpenDqCount(stats.open_data_quality_issues);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    refreshBadges();
  }, [currentTab]);

  const renderContent = () => {
    switch (currentTab) {
      case 'dashboard':
        return <DashboardView onNavigate={(tab) => setCurrentTab(tab)} />;
      case 'patients':
        return <PatientsView />;
      case 'appointments':
        return <AppointmentsView />;
      case 'encounters':
        return <EncountersView />;
      case 'orders':
        return <OrdersView />;
      case 'reports':
        return <ReportsView />;
      case 'data-quality':
        return <DataQualityView />;
      case 'audit':
        return <AuditView />;
      case 'health':
        return <HealthView />;
      default:
        return <DashboardView onNavigate={(tab) => setCurrentTab(tab)} />;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        collapsed={collapsed}
        onToggleCollapse={() => setCollapsed(!collapsed)}
        waitingCount={waitingCount}
        openDqCount={openDqCount}
      />

      {/* Main Wrapper */}
      <div className={`flex-1 flex flex-col min-h-screen transition-all duration-300 ${collapsed ? 'ml-20' : 'ml-64'}`}>
        <Navbar onRefresh={refreshBadges} />
        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto animate-fade-in">
          {renderContent()}
        </main>
      </div>
    </div>
  );
};
