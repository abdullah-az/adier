import { SubtitleCue } from '../types/preview';

function parseTimeToSeconds(timeString: string): number {
  const parts = timeString.replace(',', '.').split(':');
  if (parts.length === 3) {
    const hours = parseInt(parts[0], 10);
    const minutes = parseInt(parts[1], 10);
    const seconds = parseFloat(parts[2]);
    return hours * 3600 + minutes * 60 + seconds;
  }
  return 0;
}

export function parseSRT(content: string): SubtitleCue[] {
  const cues: SubtitleCue[] = [];
  const blocks = content.trim().split(/\n\s*\n/);

  for (const block of blocks) {
    const lines = block.trim().split('\n');
    if (lines.length < 3) continue;

    const timeLine = lines[1];
    const match = timeLine.match(/(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})/);

    if (match) {
      const start = parseTimeToSeconds(match[1]);
      const end = parseTimeToSeconds(match[2]);
      const text = lines.slice(2).join('\n');

      cues.push({ start, end, text });
    }
  }

  return cues;
}

export function parseVTT(content: string): SubtitleCue[] {
  const cues: SubtitleCue[] = [];
  const lines = content.split('\n');
  let i = 0;

  while (i < lines.length) {
    const line = lines[i].trim();

    if (line.includes('-->')) {
      const match = line.match(/(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}\.\d{3})/);

      if (match) {
        const start = parseTimeToSeconds(match[1]);
        const end = parseTimeToSeconds(match[2]);

        const textLines: string[] = [];
        i++;
        while (i < lines.length && lines[i].trim() !== '') {
          textLines.push(lines[i]);
          i++;
        }

        const text = textLines.join('\n');
        cues.push({ start, end, text });
      }
    }
    i++;
  }

  return cues;
}

export async function loadSubtitles(url: string): Promise<SubtitleCue[]> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error('Failed to load subtitles');
    }

    const content = await response.text();
    const extension = url.split('.').pop()?.toLowerCase();

    if (extension === 'srt') {
      return parseSRT(content);
    } else if (extension === 'vtt') {
      return parseVTT(content);
    }

    return [];
  } catch (error) {
    console.error('Error loading subtitles:', error);
    return [];
  }
}
