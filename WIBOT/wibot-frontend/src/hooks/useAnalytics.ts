import { useState, useEffect, useCallback } from 'react';
import { getAnalytics } from '../services/api';
import type { AnalyticsStats, AnalyticsPeriod } from '../types';

interface UseAnalyticsReturn {
  stats: AnalyticsStats | null;
  period: AnalyticsPeriod;
  setPeriod: (period: AnalyticsPeriod) => void;
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useAnalytics(): UseAnalyticsReturn {
  const [stats, setStats] = useState<AnalyticsStats | null>(null);
  const [period, setPeriod] = useState<AnalyticsPeriod>('7d');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await getAnalytics(period);
      if (response.success) {
        setStats(response.stats);
      } else {
        setError('Erreur lors du chargement des statistiques');
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Erreur inconnue';
      if (errorMessage.includes('401') || errorMessage.includes('Admin')) {
        setError('Accès réservé aux administrateurs');
      } else {
        setError('Erreur lors du chargement des statistiques');
      }
      console.error('Analytics error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleSetPeriod = useCallback((newPeriod: AnalyticsPeriod) => {
    setPeriod(newPeriod);
  }, []);

  return {
    stats,
    period,
    setPeriod: handleSetPeriod,
    isLoading,
    error,
    refresh: fetchAnalytics,
  };
}
