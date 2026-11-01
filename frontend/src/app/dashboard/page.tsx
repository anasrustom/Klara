'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import type { DashboardStats, Contract } from '@/types';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import StatsCard from '@/components/StatsCard';
import LoadingSpinner from '@/components/LoadingSpinner';
import AIChatSidebar from '@/components/AIChatSidebar';
import { useLanguage } from '@/contexts/LanguageContext';

export default function DashboardPage() {
  const router = useRouter();
  const { t } = useLanguage();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [isChatOpen, setIsChatOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }

    fetchDashboardStats();
  }, [router]);

  const fetchDashboardStats = async () => {
    try {
      const token = localStorage.getItem('access_token');
      
      // Fetch dashboard stats from backend
      const statsResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/contracts/dashboard/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (statsResponse.ok) {
        const data = await statsResponse.json();
        setStats(data);
      } else {
        // Empty state when the request fails
        setStats({
          total_contracts: 0,
          pending_reviews: 0,
          high_risk_contracts: 0,
          expiring_soon: 0,
          recent_uploads: [],
        });
      }
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      // Mock data for development
      setStats({
        total_contracts: 0,
        pending_reviews: 0,
        high_risk_contracts: 0,
        expiring_soon: 0,
        recent_uploads: [],
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <LoadingSpinner fullScreen />;
  }

  return (
    <div className="min-h-screen bg-light-gray">
      <Header title={t('dashboard.title')} />
      <Navigation />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Section */}
        <div className="mb-8 animate-fade-in-up">
          <div className="card-gradient p-8 relative overflow-hidden">
            <div className="relative z-10">
              <h2 className="text-3xl font-bold mb-2">{t('dashboard.welcomeBack')}</h2>
              <p className="text-white/90 text-lg">
                {t('dashboard.subtitle')}
              </p>
            </div>
            {/* Decorative elements */}
            <div className="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -translate-y-1/2 translate-x-1/2" />
            <div className="absolute bottom-0 left-0 w-48 h-48 bg-white/5 rounded-full translate-y-1/2 -translate-x-1/2" />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4 mb-8">
          <StatsCard
            title={t('dashboard.stats.total')}
            value={stats?.total_contracts || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            }
            color="primary"
            animationDelay={0.1}
          />

          <StatsCard
            title={t('dashboard.stats.awaiting')}
            value={stats?.pending_reviews || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            }
            color="warning"
            animationDelay={0.2}
          />

          <StatsCard
            title={t('dashboard.stats.risks')}
            value={stats?.high_risk_contracts || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            }
            color="error"
            animationDelay={0.3}
          />

          <StatsCard
            title={t('dashboard.stats.expiring')}
            value={stats?.expiring_soon || 0}
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            }
            color="info"
            animationDelay={0.4}
          />
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <Link href="/upload" className="card-hover group animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-gradient-primary mx-auto rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-smooth shadow-glow">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('dashboard.action.upload')}</h3>
              <p className="text-sm text-gray-600">{t('dashboard.action.uploadDesc')}</p>
            </div>
          </Link>

          <Link href="/contracts" className="card-hover group animate-fade-in-up" style={{ animationDelay: '0.6s' }}>
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-secondary-600 to-secondary-700 mx-auto rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-smooth shadow-glow">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('dashboard.action.view')}</h3>
              <p className="text-sm text-gray-600">{t('dashboard.action.viewDesc')}</p>
            </div>
          </Link>

          <div 
            className="card-hover group cursor-pointer animate-fade-in-up" 
            style={{ animationDelay: '0.7s' }}
            onClick={() => setIsChatOpen(true)}
          >
            <div className="p-6 text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-green-600 to-green-500 mx-auto rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-smooth shadow-glow">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">{t('dashboard.action.chat')}</h3>
              <p className="text-sm text-gray-600">{t('dashboard.action.chatDesc')}</p>
            </div>
          </div>
        </div>

        {/* Recent Uploads */}
        <div className="card animate-fade-in-up" style={{ animationDelay: '0.8s' }}>
          <div className="px-6 py-5 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">{t('dashboard.recentUploads')}</h2>
              <Link href="/contracts" className="text-sm font-medium text-primary-600 hover:text-primary-700 transition-smooth">
                {t('dashboard.viewAll')} →
              </Link>
            </div>
          </div>
          <div className="px-6 py-6">
            {stats?.recent_uploads && stats.recent_uploads.length > 0 ? (
              <div className="space-y-4">
                {stats.recent_uploads.map((contract, index) => (
                  <div 
                    key={contract.id} 
                    className="flex items-center justify-between p-4 rounded-lg hover:bg-gray-50 transition-smooth border border-gray-100 hover:border-primary-200 group animate-slide-in-left"
                    style={{ animationDelay: `${0.9 + index * 0.1}s` }}
                  >
                    <div className="flex items-center gap-4 flex-1">
                      <div className="w-12 h-12 bg-primary-50 rounded-lg flex items-center justify-center group-hover:scale-110 transition-smooth">
                        <svg className="w-6 h-6 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <Link 
                          href={`/contracts/${contract.id}`} 
                          className="text-base font-semibold text-gray-900 hover:text-primary-600 transition-smooth block truncate"
                        >
                          {contract.title}
                        </Link>
                        <p className="text-sm text-gray-500 truncate">{contract.file_name}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`badge transition-smooth ${
                        contract.status === 'completed' ? 'badge-success' :
                        contract.status === 'processing' ? 'badge-info' :
                        contract.status === 'failed' ? 'badge-error' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {contract.status}
                      </span>
                      <svg className="w-5 h-5 text-gray-400 group-hover:text-primary-600 transition-smooth" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 animate-fade-in">
                <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <p className="text-gray-600 mb-4">{t('dashboard.noUploads')}</p>
                <Link href="/upload" className="btn btn-primary inline-flex">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  {t('dashboard.getStarted')}
                </Link>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* AI Chat Sidebar */}
      <AIChatSidebar isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} chatId="dashboard" />
    </div>
  );
}
