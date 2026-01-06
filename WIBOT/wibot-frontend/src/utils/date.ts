import { formatDistanceToNow, format, isToday, isYesterday } from 'date-fns';
import { fr } from 'date-fns/locale';

export function formatRelativeDate(dateString: string): string {
  const date = new Date(dateString);

  if (isToday(date)) {
    return formatDistanceToNow(date, { addSuffix: true, locale: fr });
  }

  if (isYesterday(date)) {
    return `Hier ${format(date, 'HH:mm', { locale: fr })}`;
  }

  return format(date, 'd MMM yyyy', { locale: fr });
}

export function formatMessageTime(dateString: string): string {
  const date = new Date(dateString);
  return format(date, 'HH:mm', { locale: fr });
}

export function formatFullDate(dateString: string): string {
  const date = new Date(dateString);
  return format(date, 'd MMMM yyyy à HH:mm', { locale: fr });
}
