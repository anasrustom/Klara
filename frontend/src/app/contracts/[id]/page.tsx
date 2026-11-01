'use client';

import { useCallback, useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import type { Contract, Risk } from '@/types';
import Header from '@/components/Header';
import Navigation from '@/components/Navigation';
import LoadingSpinner from '@/components/LoadingSpinner';
import AIChatSidebar from '@/components/AIChatSidebar';
import { useLanguage } from '@/contexts/LanguageContext';

type Tab = 'overview' | 'risks' | 'parties';

const SEVERITY_STYLES: Record<Risk['severity'], { badge: string; bar: string; dot: string }> = {
  critical: { badge: 'bg-red-100 text-red-800', bar: 'border-red-600', dot: 'bg-red-600' },
  high: { badge: 'bg-orange-100 text-orange-800', bar: 'border-orange-500', dot: 'bg-orange-500' },
  medium: { badge: 'bg-yellow-100 text-yellow-800', bar: 'border-yellow-400', dot: 'bg-yellow-400' },
  low: { badge: 'bg-gray-100 text-gray-800', bar: 'border-gray-300', dot: 'bg-gray-400' },
};

const SEVERITIES: Risk['severity'][] = ['critical', 'high', 'medium', 'low'];

// A verbatim passage from the contract, with the page it was found on
function SourceQuote({ page, snippet }: { page?: number | null; snippet?: string | null }) {
  const { t } = useLanguage();
  if (!snippet) return null;
  return (
    <div className="mt-3 rounded-md bg-gray-50 border-s-4 border-primary-300 px-3 py-2">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-gray-500 mb-1">
        {t('detail.source')}{page ? ` · ${t('detail.page')} ${page}` : ''}
      </p>
      <p dir="auto" className="text-sm text-gray-700 italic leading-relaxed">&ldquo;{snippet}&rdquo;</p>
    </div>
  );
}

export default function ContractDetailPage() {
  const params = useParams();
  const router = useRouter();
  const contractId = params.id as string;
  const { t, language } = useLanguage();

  const [contract, setContract] = useState<Contract | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editedContract, setEditedContract] = useState<Contract | null>(null);
  const [showAddRisk, setShowAddRisk] = useState(false);
  const [isAIChatOpen, setIsAIChatOpen] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [actionError, setActionError] = useState('');

  const authHeaders = () => ({ 'Authorization': `Bearer ${localStorage.getItem('access_token')}` });

  const fetchContractDetails = useCallback(async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/contracts/${contractId}`, {
        headers: authHeaders(),
      });

      if (response.status === 401) {
        router.push('/login');
        return;
      }
      if (response.ok) {
        const contractData = await response.json();
        setContract(contractData);
        setEditedContract(contractData);
      }
    } catch (error) {
      console.error('Error fetching contract details:', error);
    } finally {
      setLoading(false);
    }
  }, [contractId, router]);

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      router.push('/login');
      return;
    }
    if (contractId) {
      fetchContractDetails();
    }
  }, [contractId, fetchContractDetails, router]);

  const handleSaveChanges = async () => {
    if (!editedContract) return;
    setActionError('');
    try {
      // Only send changed fields
      const fields: (keyof Contract)[] = [
        'title', 'status', 'governing_law', 'jurisdiction', 'industry', 'contract_type', 'summary', 'purpose', 'scope',
      ];
      const updateData: Record<string, unknown> = {};
      fields.forEach((f) => {
        if (editedContract[f] !== contract?.[f]) updateData[f] = editedContract[f];
      });

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/contracts/${contractId}`, {
        method: 'PATCH',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(updateData),
      });
      if (!response.ok) throw new Error('update failed');

      await fetchContractDetails();
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating contract:', error);
      setActionError(t('detail.saveFailed'));
    }
  };

  const handleCancelEdit = () => {
    setEditedContract(contract);
    setIsEditing(false);
  };

  const updateContractField = (field: keyof Contract, value: string) => {
    if (editedContract) {
      setEditedContract({ ...editedContract, [field]: value });
    }
  };

  const addRisk = async (risk: Record<string, FormDataEntryValue | null>) => {
    setActionError('');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/contracts/${contractId}/risks`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify(risk),
      });
      if (!response.ok) throw new Error('add risk failed');
      await fetchContractDetails();
    } catch (error) {
      console.error('Error adding risk:', error);
      setActionError(t('detail.riskAddFailed'));
    }
  };

  const removeRisk = async (riskId: string) => {
    setActionError('');
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/contracts/${contractId}/risks/${riskId}`, {
        method: 'DELETE',
        headers: authHeaders(),
      });
      if (!response.ok) throw new Error('delete risk failed');
      await fetchContractDetails();
    } catch (error) {
      console.error('Error deleting risk:', error);
      setActionError(t('detail.riskDeleteFailed'));
    }
  };

  const runAnalysis = async () => {
    setAnalyzing(true);
    setActionError('');
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/contracts/${contractId}/analyze?output_language=${language}`,
        { method: 'POST', headers: authHeaders() },
      );
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || 'analysis failed');
      }
      await fetchContractDetails();
    } catch (error) {
      console.error('Error analyzing contract:', error);
      setActionError(t('detail.analysisFailed'));
    } finally {
      setAnalyzing(false);
    }
  };

  const formatDate = (iso: string) =>
    new Date(iso).toLocaleDateString(language === 'ar' ? 'ar' : 'en-GB', { year: 'numeric', month: 'long', day: 'numeric' });

  const formatAmount = (amount: number, currency: string | null) => {
    try {
      return currency
        ? new Intl.NumberFormat(language === 'ar' ? 'ar' : 'en', { style: 'currency', currency, maximumFractionDigits: 2 }).format(amount)
        : amount.toLocaleString(language === 'ar' ? 'ar' : 'en');
    } catch {
      return `${currency ?? ''} ${amount.toLocaleString()}`.trim();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-4 bg-light-gray">
        <LoadingSpinner size="lg" />
        <p className="text-gray-600">{t('detail.loading')}</p>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-light-gray">
        <p className="text-gray-500 mb-4">{t('detail.notFound')}</p>
        <Link href="/contracts" className="text-primary-600 hover:text-primary-500">
          {t('detail.backToContracts')}
        </Link>
      </div>
    );
  }

  const displayContract = (isEditing ? editedContract : contract) ?? contract;
  const risks = displayContract.risks || [];
  const severeRisks = risks.filter(r => r.severity === 'high' || r.severity === 'critical');
  const topRisks = (severeRisks.length > 0 ? severeRisks : risks).slice(0, 5);
  const riskCounts = SEVERITIES.map(s => ({ severity: s, count: risks.filter(r => r.severity === s).length }));
  const notAnalyzed = !contract.analyzed && !contract.summary;

  const tabs: { id: Tab; label: string; count?: number }[] = [
    { id: 'overview', label: t('detail.tab.overview') },
    { id: 'risks', label: t('detail.risks'), count: risks.length },
    { id: 'parties', label: t('detail.tab.parties') },
  ];

  const facts: { key: keyof Contract; label: string }[] = [
    { key: 'contract_type', label: t('detail.contractType') },
    { key: 'industry', label: t('detail.industry') },
    { key: 'governing_law', label: t('detail.governingLaw') },
    { key: 'jurisdiction', label: t('detail.jurisdiction') },
  ];

  const statusStyle =
    displayContract.status === 'completed' ? 'bg-green-100 text-green-800' :
    displayContract.status === 'processing' ? 'bg-blue-100 text-blue-800' :
    displayContract.status === 'failed' ? 'bg-red-100 text-red-800' :
    'bg-gray-100 text-gray-800';

  return (
    <div className="min-h-screen bg-light-gray">
      <Header title={displayContract.title} />
      <Navigation />

      {/* Contract header */}
      <section className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Link href="/contracts" className="text-sm text-primary-600 hover:text-primary-500 mb-2 inline-flex items-center gap-1">
            <span className="rtl:rotate-180 inline-block">&larr;</span> {t('detail.backToContracts')}
          </Link>
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div className="min-w-0">
              {isEditing ? (
                <input
                  type="text"
                  value={editedContract?.title || ''}
                  onChange={(e) => updateContractField('title', e.target.value)}
                  className="input text-xl font-bold"
                />
              ) : (
                <h1 dir="auto" className="text-2xl font-bold text-gray-900 truncate">{displayContract.title}</h1>
              )}
              <p className="text-sm text-gray-600 mt-1 flex flex-wrap items-center gap-x-2">
                <span dir="auto">{displayContract.file_name}</span>
                {displayContract.pages ? <span>· {displayContract.pages} {t('detail.pages')}</span> : null}
                {displayContract.language ? <span>· {t(`detail.lang.${displayContract.language}`)}</span> : null}
              </p>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              {isEditing ? (
                <>
                  <button onClick={handleCancelEdit} className="btn btn-outline text-sm">
                    {t('common.cancel')}
                  </button>
                  <button onClick={handleSaveChanges} className="btn btn-primary text-sm">
                    {t('detail.saveChanges')}
                  </button>
                </>
              ) : (
                <>
                  <span className={`px-4 py-2 text-sm font-medium rounded-full ${statusStyle}`}>
                    {t(`contracts.status.${displayContract.status}`)}
                  </span>
                  <button onClick={() => setIsEditing(true)} className="btn btn-primary text-sm">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    {t('detail.edit')}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-6 overflow-x-auto" role="tablist">
            {tabs.map(tab => (
              <button
                key={tab.id}
                role="tab"
                aria-selected={activeTab === tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 text-sm font-medium border-b-2 whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.label}
                {tab.count !== undefined && (
                  <span className="ms-2 px-2 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">{tab.count}</span>
                )}
              </button>
            ))}
          </div>
        </div>
      </section>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {actionError && (
          <div className="mb-6 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-800" role="alert">
            {actionError}
          </div>
        )}

        {(notAnalyzed || contract.analysis_error) && (
          <div className="mb-6 rounded-lg bg-primary-50 border border-primary-200 px-4 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <p className="text-sm text-primary-900">
              {contract.analysis_error ? t('detail.analysisFailed') : t('detail.notAnalyzed')}
            </p>
            <button onClick={runAnalysis} disabled={analyzing} className="btn btn-primary text-sm disabled:opacity-60">
              {analyzing ? t('detail.analyzing') : t('detail.runAnalysis')}
            </button>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Overview Tab */}
            {activeTab === 'overview' && (
              <>
                {isEditing && (
                  <div className="bg-white shadow rounded-lg p-6">
                    <h2 className="text-lg font-medium text-gray-900 mb-4">{t('detail.contractStatus')}</h2>
                    <select
                      value={editedContract?.status}
                      onChange={(e) => updateContractField('status', e.target.value)}
                      className="input"
                    >
                      {(['pending', 'processing', 'completed', 'failed'] as const).map(s => (
                        <option key={s} value={s}>{t(`contracts.status.${s}`)}</option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Summary */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">{t('detail.contractSummary')}</h2>
                  {isEditing ? (
                    <textarea
                      value={editedContract?.summary || ''}
                      onChange={(e) => updateContractField('summary', e.target.value)}
                      className="input min-h-[120px]"
                      placeholder={t('detail.summaryPlaceholder')}
                    />
                  ) : (
                    <p dir="auto" className="text-gray-700 leading-relaxed">{displayContract.summary || t('detail.noSummary')}</p>
                  )}
                  <div className="mt-5 grid grid-cols-1 md:grid-cols-2 gap-4">
                    {(['purpose', 'scope'] as const).map(field => (
                      <div key={field} className="rounded-lg bg-gray-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-wide text-gray-500">{t(`detail.${field}`)}</p>
                        {isEditing ? (
                          <textarea
                            value={editedContract?.[field] || ''}
                            onChange={(e) => updateContractField(field, e.target.value)}
                            className="input mt-2 min-h-[80px]"
                          />
                        ) : (
                          <p dir="auto" className="mt-1 text-sm text-gray-900 leading-relaxed">{displayContract[field] || t('detail.notStated')}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Highlights */}
                {!isEditing && contract.highlights && contract.highlights.length > 0 && (
                  <div className="bg-white shadow rounded-lg p-6">
                    <h2 className="text-lg font-medium text-gray-900 mb-4">{t('detail.highlights')}</h2>
                    <ul className="space-y-2">
                      {contract.highlights.map((h, i) => (
                        <li key={i} className="flex gap-3 text-sm text-gray-700">
                          <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-primary-500 shrink-0" />
                          <span dir="auto">{h}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Key facts */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  {facts.map(({ key, label }) => (
                    <div key={key} className="bg-white shadow rounded-lg p-6">
                      <h3 className="text-sm font-medium text-gray-500 mb-2">{label}</h3>
                      {isEditing ? (
                        <input
                          type="text"
                          value={(editedContract?.[key] as string) || ''}
                          onChange={(e) => updateContractField(key, e.target.value)}
                          className="input"
                        />
                      ) : (
                        <p dir="auto" className="text-base font-semibold text-gray-900">{(displayContract[key] as string) || t('detail.notStated')}</p>
                      )}
                    </div>
                  ))}
                </div>

                {/* Financial Terms */}
                <div className="bg-white shadow rounded-lg p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">{t('detail.financialTerms')}</h2>
                  {displayContract.financial_terms && displayContract.financial_terms.length > 0 ? (
                    <div className="divide-y divide-gray-100">
                      {displayContract.financial_terms.map((term) => (
                        <div key={term.id} className="py-4 first:pt-0 last:pb-0">
                          <div className="flex justify-between items-start gap-4">
                            <div className="min-w-0">
                              <p className="font-medium text-gray-900">{t(`termType.${term.term_type}`)}</p>
                              {term.description && <p dir="auto" className="text-sm text-gray-600 mt-0.5">{term.description}</p>}
                              {term.schedule && <p dir="auto" className="text-xs text-gray-500 mt-1">{term.schedule}</p>}
                            </div>
                            <p className="text-base font-semibold text-gray-900 whitespace-nowrap">
                              {term.amount !== null && term.amount !== undefined
                                ? formatAmount(term.amount, term.currency)
                                : <span className="text-sm font-normal text-gray-400">{t('detail.amountNotStated')}</span>}
                            </p>
                          </div>
                          <SourceQuote page={term.source_page} snippet={term.source_snippet} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">{t('detail.noFinancialTerms')}</p>
                  )}
                </div>

                {/* Top Risks */}
                <div className="bg-white shadow rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-medium text-gray-900">{t('detail.topRisks')}</h2>
                    {risks.length > topRisks.length && (
                      <button onClick={() => setActiveTab('risks')} className="text-sm font-medium text-primary-600 hover:text-primary-700">
                        {t('detail.allRisks')} ({risks.length})
                      </button>
                    )}
                  </div>
                  {topRisks.length > 0 ? (
                    <div className="space-y-4">
                      {topRisks.map((risk) => (
                        <div key={risk.id} className={`border-s-4 ${SEVERITY_STYLES[risk.severity].bar} ps-4 py-1`}>
                          <div className="flex items-start justify-between gap-4">
                            <p dir="auto" className="font-medium text-gray-900">{risk.title}</p>
                            <span className={`px-2 py-1 text-xs font-medium rounded shrink-0 ${SEVERITY_STYLES[risk.severity].badge}`}>
                              {t(`risk.${risk.severity}`)}
                            </span>
                          </div>
                          <p dir="auto" className="text-sm text-gray-600 mt-1">{risk.description}</p>
                          {risk.source_page ? (
                            <p className="text-xs text-gray-400 mt-1">{t('detail.source')} · {t('detail.page')} {risk.source_page}</p>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">{t('detail.noHighRisks')}</p>
                  )}
                </div>
              </>
            )}

            {/* Risk Analysis Tab */}
            {activeTab === 'risks' && (
              <div className="bg-white shadow rounded-lg p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-medium text-gray-900">{t('detail.allRisks')}</h2>
                  {isEditing && (
                    <button onClick={() => setShowAddRisk(true)} className="btn btn-primary text-sm">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      {t('detail.addRisk')}
                    </button>
                  )}
                </div>
                {risks.length > 0 ? (
                  <div className="space-y-4">
                    {risks.map((risk) => (
                      <article key={risk.id} className={`border rounded-lg p-5 relative border-s-4 ${SEVERITY_STYLES[risk.severity].bar}`}>
                        {isEditing && (
                          <button
                            onClick={() => removeRisk(risk.id)}
                            aria-label={t('common.delete')}
                            className="absolute top-3 end-3 text-red-600 hover:text-red-700"
                          >
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            </svg>
                          </button>
                        )}
                        <div className="flex items-start justify-between gap-4 mb-2 pe-8">
                          <h3 dir="auto" className="font-semibold text-gray-900">{risk.title}</h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded shrink-0 ${SEVERITY_STYLES[risk.severity].badge}`}>
                            {t(`risk.${risk.severity}`)}
                          </span>
                        </div>
                        <p className="text-xs text-gray-500 mb-2">
                          {t(`riskType.${risk.risk_type}`)}
                          {risk.clause_reference && <> · {t('detail.reference')}: <span dir="auto">{risk.clause_reference}</span></>}
                        </p>
                        <p dir="auto" className="text-sm text-gray-700 leading-relaxed">{risk.description}</p>
                        {risk.recommendation && (
                          <div className="mt-3 bg-blue-50 p-3 rounded">
                            <p className="text-sm text-blue-900">
                              <strong>{t('detail.recommendation')}:</strong> <span dir="auto">{risk.recommendation}</span>
                            </p>
                          </div>
                        )}
                        <SourceQuote page={risk.source_page} snippet={risk.source_snippet} />
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">{t('detail.noRisks')}</p>
                )}
              </div>
            )}

            {/* Parties & Dates Tab */}
            {activeTab === 'parties' && (
              <>
                <div className="bg-white shadow rounded-lg p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">{t('detail.parties')}</h2>
                  {displayContract.parties && displayContract.parties.length > 0 ? (
                    <div className="space-y-3">
                      {displayContract.parties.map((party) => (
                        <div key={party.id} className="border rounded-lg p-4">
                          <p dir="auto" className="font-medium text-gray-900">{party.name}</p>
                          <div className="flex flex-wrap gap-2 mt-2">
                            <span className="badge badge-primary">{t(`role.${party.role}`)}</span>
                            <span className="badge badge-info">{t(`partyType.${party.type}`)}</span>
                          </div>
                          <SourceQuote page={party.source_page} snippet={party.source_snippet} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">{t('detail.noParties')}</p>
                  )}
                </div>

                <div className="bg-white shadow rounded-lg p-6">
                  <h2 className="text-lg font-medium text-gray-900 mb-4">{t('detail.keyDates')}</h2>
                  {displayContract.key_dates && displayContract.key_dates.length > 0 ? (
                    <div className="divide-y divide-gray-100">
                      {displayContract.key_dates.map((dateItem) => (
                        <div key={dateItem.id} className="py-4 first:pt-0 last:pb-0">
                          <div className="flex justify-between items-start gap-4">
                            <div className="min-w-0">
                              <p className="font-medium text-gray-900">{t(`dateType.${dateItem.date_type}`)}</p>
                              {dateItem.description && <p dir="auto" className="text-sm text-gray-600">{dateItem.description}</p>}
                            </div>
                            <p className="text-sm font-semibold text-gray-900 whitespace-nowrap">{formatDate(dateItem.date)}</p>
                          </div>
                          <SourceQuote page={dateItem.source_page} snippet={dateItem.source_snippet} />
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500 text-sm">{t('detail.noDates')}</p>
                  )}

                  {contract.undated_terms && contract.undated_terms.length > 0 && (
                    <div className="mt-6">
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">{t('detail.undatedTerms')}</h3>
                      <ul className="space-y-2">
                        {contract.undated_terms.map((d, i) => (
                          <li key={i} className="text-sm text-gray-700">
                            <span className="font-medium">{t(`dateType.${d.type}`)}:</span> <span dir="auto">{d.description}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                {contract.key_obligations && contract.key_obligations.length > 0 && (
                  <div className="bg-white shadow rounded-lg p-6">
                    <h2 className="text-lg font-medium text-gray-900 mb-4">{t('detail.obligations')}</h2>
                    <ul className="space-y-3">
                      {contract.key_obligations.map((o, i) => (
                        <li key={i} className="text-sm text-gray-700">
                          {/* Separate blocks so a party name in one script and text in another never interleave */}
                          {o.party && <p dir="auto" className="font-semibold text-gray-900">{o.party}</p>}
                          <p dir="auto">{o.obligation}</p>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <button
              onClick={() => setIsAIChatOpen(true)}
              className="bg-white shadow rounded-lg p-6 w-full hover:shadow-lg transition-all cursor-pointer group text-center"
            >
              <div className="w-16 h-16 bg-gradient-to-br from-green-600 to-green-500 mx-auto rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-smooth shadow-glow">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('detail.askKlara')}</h3>
              <p className="text-sm text-gray-600">{t('detail.askKlaraDesc')}</p>
            </button>

            {risks.length > 0 && (
              <div className="bg-white shadow rounded-lg p-6">
                <h3 className="font-semibold text-gray-900 mb-4">{t('detail.riskProfile')}</h3>
                <div className="flex h-2 rounded-full overflow-hidden bg-gray-100 mb-4">
                  {riskCounts.filter(r => r.count > 0).map(r => (
                    <div key={r.severity} className={SEVERITY_STYLES[r.severity].dot} style={{ width: `${(r.count / risks.length) * 100}%` }} />
                  ))}
                </div>
                <ul className="space-y-2">
                  {riskCounts.map(r => (
                    <li key={r.severity} className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2 text-gray-700">
                        <span className={`w-2.5 h-2.5 rounded-full ${SEVERITY_STYLES[r.severity].dot}`} />
                        {t(`risk.${r.severity}`)}
                      </span>
                      <span className="font-semibold text-gray-900">{r.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Add Risk Modal */}
      {showAddRisk && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold text-gray-900 mb-4">{t('detail.addRisk')}</h3>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.currentTarget);
              addRisk({
                title: formData.get('title'),
                description: formData.get('description'),
                severity: formData.get('severity'),
                risk_type: formData.get('risk_type'),
                recommendation: formData.get('recommendation'),
              });
              setShowAddRisk(false);
            }}>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('detail.riskTitle')}</label>
                  <input type="text" name="title" required className="input" placeholder={t('detail.riskTitlePlaceholder')} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('detail.description')}</label>
                  <textarea name="description" required className="input" rows={3} placeholder={t('detail.descriptionPlaceholder')} />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('detail.severity')}</label>
                  <select name="severity" required className="input">
                    {SEVERITIES.slice().reverse().map(s => (
                      <option key={s} value={s}>{t(`risk.${s}`)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('detail.riskType')}</label>
                  <select name="risk_type" required className="input">
                    {(['missing_clause', 'unusual_clause', 'non_standard', 'inconsistency', 'compliance'] as const).map(rt => (
                      <option key={rt} value={rt}>{t(`riskType.${rt}`)}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{t('detail.recommendationOptional')}</label>
                  <textarea name="recommendation" className="input" rows={2} placeholder={t('detail.recommendationPlaceholder')} />
                </div>
              </div>
              <div className="flex gap-2 mt-6">
                <button type="button" onClick={() => setShowAddRisk(false)} className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                  {t('common.cancel')}
                </button>
                <button type="submit" className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                  {t('detail.addRisk')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* AI Chat Sidebar */}
      <AIChatSidebar
        isOpen={isAIChatOpen}
        onClose={() => setIsAIChatOpen(false)}
        chatId={`contract-${contractId}`}
        contractId={contractId}
      />
    </div>
  );
}
