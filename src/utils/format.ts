export function formatFileSize(bytes: number | null | undefined): string {
  if (typeof bytes !== 'number' || !Number.isFinite(bytes) || bytes <= 0) {
    return '—';
  }

  const thresh = 1024;
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let value = bytes;
  let unitIndex = 0;

  while (value >= thresh && unitIndex < units.length - 1) {
    value /= thresh;
    unitIndex += 1;
  }

  return `${value.toFixed(value >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

export function formatDuration(totalSeconds: number | null | undefined): string {
  if (typeof totalSeconds !== 'number' || !Number.isFinite(totalSeconds) || totalSeconds < 0) {
    return '—';
  }

  const seconds = Math.floor(totalSeconds % 60);
  const minutes = Math.floor((totalSeconds / 60) % 60);
  const hours = Math.floor(totalSeconds / 3600);

  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
  }

  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

export function formatLocalizedTimestamp(timestamp: string | null | undefined, locale: string): string {
  if (!timestamp) {
    return '';
  }

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return '';
  }

  try {
    return date.toLocaleString(locale, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      day: '2-digit',
      month: 'short',
    });
  } catch (error) {
    return date.toLocaleString();
  }
}

export function sanitizeFileNameSegment(segment: string): string {
  return segment
    .toLowerCase()
    .replace(/[^\p{L}\p{N}\-_. ]+/gu, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '');
}
