import {
  Coins,
  MessageSquare,
  Users,
  FolderOpen,
  FileText,
  Search,
  RefreshCw
} from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';
import { StatsCard, SimpleBarChart, DonutChart } from '../components/analytics';
import { Spinner } from '../components/ui';
import { Header } from '../components/layout/Header';
import type { AnalyticsPeriod } from '../types';

const periodLabels: Record<AnalyticsPeriod, string> = {
  '24h': '24 heures',
  '7d': '7 jours',
  '30d': '30 jours',
};

export function Supervision() {
  const { stats, period, setPeriod, isLoading, error, refresh } = useAnalytics();

  if (error) {
    return (
      <div className="min-h-screen bg-bg-primary flex flex-col">
        <Header />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-red-400 text-lg mb-4">{error}</p>
            <p className="text-text-secondary">Cliquez sur le logo WIBOT pour revenir au chat</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bg-primary flex flex-col">
      {/* Header principal */}
      <Header />

      {/* Sous-header Supervision */}
      <div className="bg-bg-secondary border-b border-border px-6 py-3">
        <div className="flex items-center justify-between">
          <h1 className="text-lg font-semibold text-text-primary flex items-center gap-2">
            <Search className="w-5 h-5 text-accent" />
            Supervision
          </h1>

          <div className="flex items-center gap-4">
            {/* Period selector */}
            <div className="flex items-center gap-2 bg-bg-primary rounded-lg p-1">
              {(['24h', '7d', '30d'] as AnalyticsPeriod[]).map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    period === p
                      ? 'bg-accent text-white'
                      : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  {periodLabels[p]}
                </button>
              ))}
            </div>

            {/* Refresh button */}
            <button
              onClick={refresh}
              disabled={isLoading}
              className="p-2 rounded-lg bg-bg-primary hover:bg-border transition-colors disabled:opacity-50"
              title="Rafraichir"
            >
              <RefreshCw className={`w-5 h-5 text-text-secondary ${isLoading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="p-6">
        {isLoading && !stats ? (
          <div className="flex items-center justify-center py-20">
            <Spinner size="lg" />
          </div>
        ) : stats ? (
          <div className="space-y-6">
            {/* Stats cards row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatsCard
                title="Tokens utilises"
                value={stats.tokens.used}
                subtitle={`/ ${stats.tokens.quota.toLocaleString('fr-FR')} (${stats.tokens.percentage}%)`}
                icon={Coins}
                color="orange"
                progress={stats.tokens.percentage}
              />
              <StatsCard
                title="Messages"
                value={stats.messages.total}
                subtitle={`+${stats.messages.today} aujourd'hui`}
                icon={MessageSquare}
                color="blue"
              />
              <StatsCard
                title="Conversations"
                value={stats.conversations.total}
                subtitle={`${stats.conversations.active} actives`}
                icon={FolderOpen}
                color="green"
              />
              <StatsCard
                title="Fichiers joints"
                value={stats.files.total}
                subtitle={`${stats.files.messagesWithFiles} messages avec fichiers`}
                icon={FileText}
                color="purple"
              />
            </div>

            {/* Additional stats */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <StatsCard
                title="Utilisateurs"
                value={stats.users.total}
                subtitle="Utilisateurs actifs"
                icon={Users}
                color="blue"
              />
              <StatsCard
                title="Requetes RAG"
                value={stats.rag.queries}
                subtitle="Recherches dans les documents"
                icon={Search}
                color="green"
              />
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Messages by day */}
              <SimpleBarChart
                title={`Messages par jour (${periodLabels[period]})`}
                data={stats.messages.byDay.map((d) => ({
                  label: new Date(d.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }),
                  value: d.count,
                }))}
                color="#6366f1"
                height={180}
              />

              {/* Modes distribution */}
              <DonutChart
                title="Repartition par mode"
                data={[
                  { label: 'Flash', value: stats.modes.flash, color: '#f59e0b' },
                  { label: 'Code', value: stats.modes.code, color: '#6366f1' },
                  { label: 'Pro', value: stats.modes.redaction, color: '#10b981' },
                ]}
              />
            </div>

            {/* Tokens by day */}
            <SimpleBarChart
              title={`Tokens consommes par jour (${periodLabels[period]})`}
              data={stats.messages.byDay.map((d) => ({
                label: new Date(d.date).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit' }),
                value: d.tokens,
              }))}
              color="#f59e0b"
              height={150}
            />
          </div>
        ) : null}
      </main>
    </div>
  );
}
