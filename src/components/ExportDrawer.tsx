import { FormEvent, useEffect, useMemo, useState } from 'react';
import { X, Film, Info, BadgeCheck, Bell, Type } from 'lucide-react';
import { ExportPreset, ExportResolution } from '../types/export';
import { useTranslation } from 'react-i18next';
import { sanitizeFileNameSegment } from '../utils/format';

export interface QueueExportSelection {
  presetId: string;
  resolution: ExportResolution;
  includeCaptions: boolean;
  autoShare: boolean;
  fileName?: string;
}

interface ExportDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  presets: ExportPreset[];
  onQueueExport: (selection: QueueExportSelection) => Promise<void> | void;
  isSubmitting?: boolean;
}

export function ExportDrawer({
  isOpen,
  onClose,
  presets,
  onQueueExport,
  isSubmitting = false,
}: ExportDrawerProps) {
  const { t, i18n } = useTranslation();
  const direction = i18n.dir();

  const [selectedPresetId, setSelectedPresetId] = useState<string | null>(null);
  const [selectedResolution, setSelectedResolution] = useState<ExportResolution | null>(null);
  const [includeCaptions, setIncludeCaptions] = useState(true);
  const [autoShare, setAutoShare] = useState(true);
  const [fileName, setFileName] = useState('');

  useEffect(() => {
    if (isOpen && presets.length > 0) {
      const firstPreset = presets[0];
      setSelectedPresetId((prev) => prev ?? firstPreset.id);
    }
  }, [isOpen, presets]);

  const selectedPreset = useMemo(
    () => presets.find((preset) => preset.id === selectedPresetId) ?? null,
    [presets, selectedPresetId]
  );

  useEffect(() => {
    if (selectedPreset) {
      const defaultResolution = selectedPreset.supportedResolutions[0];
      if (!selectedResolution || !selectedPreset.supportedResolutions.includes(selectedResolution)) {
        setSelectedResolution(defaultResolution);
      }
      if (!fileName) {
        const suggestion = sanitizeFileNameSegment(
          `${selectedPreset.name}-${selectedPreset.aspectRatio}-${defaultResolution}`
        );
        setFileName(suggestion);
      }
    }
  }, [selectedPreset, selectedResolution, fileName]);

  useEffect(() => {
    if (!isOpen) {
      setIncludeCaptions(true);
      setAutoShare(true);
      setFileName('');
    }
  }, [isOpen]);

  if (!isOpen) {
    return null;
  }

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedPreset || !selectedResolution) {
      return;
    }

    const sanitizedName = fileName ? sanitizeFileNameSegment(fileName) : undefined;

    await onQueueExport({
      presetId: selectedPreset.id,
      resolution: selectedResolution,
      includeCaptions,
      autoShare,
      fileName: sanitizedName,
    });
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-40 flex" role="dialog" aria-modal="true">
      <div
        className="absolute inset-0 bg-gray-900/50 backdrop-blur-sm"
        onClick={handleClose}
        aria-hidden="true"
      />
      <div
        dir={direction}
        className={`relative ml-auto h-full w-full max-w-lg bg-white shadow-2xl flex flex-col ${direction === 'rtl' ? 'border-l border-gray-100' : 'border-l border-gray-100'}`}
      >
        <div className="flex items-center justify-between px-6 py-5 border-b border-gray-100">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wide text-indigo-500">
              {t('preview.export.drawer.title')}
            </p>
            <h2 className="text-2xl font-bold text-gray-900">
              {t('preview.export.drawer.heading')}
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {t('preview.export.drawer.subtitle')}
            </p>
          </div>
          <button
            type="button"
            onClick={handleClose}
            className="rounded-full p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            aria-label={t('preview.export.drawer.close')}
            disabled={isSubmitting}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8">
            <section>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
                {t('preview.export.drawer.presetLabel')}
              </h3>
              <div className="space-y-3">
                {presets.map((preset) => {
                  const isSelected = preset.id === selectedPresetId;
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      className={`w-full text-left border rounded-xl px-4 py-4 transition-all duration-200 ${
                        isSelected
                          ? 'border-indigo-500 ring-2 ring-indigo-200 bg-indigo-50/60'
                          : 'border-gray-200 hover:border-indigo-300 bg-white'
                      }`}
                      onClick={() => setSelectedPresetId(preset.id)}
                      disabled={isSubmitting}
                    >
                      <div className="flex items-start gap-3">
                        <div
                          className={`mt-1 flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500/10 to-indigo-500/5 ${
                            isSelected ? 'text-indigo-600' : 'text-gray-500'
                          }`}
                        >
                          <Film className="h-5 w-5" aria-hidden="true" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center justify-between gap-3">
                            <p className="text-sm font-semibold text-gray-900">{preset.name}</p>
                            <span className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700">
                              <BadgeCheck className="h-3.5 w-3.5" />
                              {preset.aspectRatio}
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-gray-600 leading-relaxed">
                            {preset.description}
                          </p>
                          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-gray-500">
                            <span className="font-medium uppercase tracking-wide text-[11px]">
                              {t('preview.export.drawer.supportedResolutions')}:
                            </span>
                            {preset.supportedResolutions.map((resolution) => (
                              <span
                                key={resolution}
                                className={`inline-flex rounded-full border px-2 py-1 ${
                                  isSelected ? 'border-indigo-300 text-indigo-600' : 'border-gray-200'
                                }`}
                              >
                                {resolution}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section>
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">
                {t('preview.export.drawer.resolutionLabel')}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {selectedPreset?.supportedResolutions.map((resolution) => {
                  const isActive = resolution === selectedResolution;
                  return (
                    <button
                      key={resolution}
                      type="button"
                      onClick={() => setSelectedResolution(resolution)}
                      className={`rounded-xl border px-4 py-3 text-sm font-medium transition ${
                        isActive
                          ? 'border-indigo-500 bg-indigo-500/10 text-indigo-600'
                          : 'border-gray-200 text-gray-700 hover:border-indigo-300'
                      }`}
                      disabled={isSubmitting}
                    >
                      {resolution}
                    </button>
                  );
                })}
              </div>
              <p className="mt-2 flex items-start gap-2 text-xs text-gray-500">
                <Info className="mt-0.5 h-4 w-4" aria-hidden="true" />
                {t('preview.export.drawer.resolutionHint')}
              </p>
            </section>

            <section className="space-y-4">
              <div>
                <label className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2 block">
                  {t('preview.export.drawer.fileNameLabel')}
                </label>
                <div className="relative">
                  <Type className="pointer-events-none absolute inset-y-0 left-4 top-3 h-4 w-4 text-gray-400" aria-hidden="true" />
                  <input
                    type="text"
                    value={fileName}
                    onChange={(event) => setFileName(event.target.value)}
                    disabled={isSubmitting}
                    className="w-full rounded-xl border border-gray-200 bg-white py-3 pl-11 pr-4 text-sm text-gray-700 placeholder:text-gray-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                    placeholder={t('preview.export.drawer.fileNamePlaceholder')}
                  />
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  {t('preview.export.drawer.fileNameHint')}
                </p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                <label className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    checked={includeCaptions}
                    onChange={(event) => setIncludeCaptions(event.target.checked)}
                    disabled={isSubmitting}
                  />
                  <div>
                    <p className="font-semibold">{t('preview.export.drawer.includeCaptionsLabel')}</p>
                    <p className="text-xs text-gray-500">{t('preview.export.drawer.includeCaptionsHint')}</p>
                  </div>
                </label>

                <label className="flex items-start gap-3 rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700">
                  <input
                    type="checkbox"
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    checked={autoShare}
                    onChange={(event) => setAutoShare(event.target.checked)}
                    disabled={isSubmitting}
                  />
                  <div>
                    <p className="font-semibold">{t('preview.export.drawer.notificationsLabel')}</p>
                    <p className="text-xs text-gray-500">{t('preview.export.drawer.notificationsHint')}</p>
                  </div>
                </label>
              </div>
            </section>
          </div>

          <div className="border-t border-gray-100 px-6 py-5 flex flex-col gap-4 bg-gray-50">
            <div className="flex items-center gap-2 text-xs text-gray-500">
              <Bell className="h-4 w-4" aria-hidden="true" />
              {t('preview.export.drawer.queueInfo')}
            </div>
            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="rounded-lg border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-white"
                disabled={isSubmitting}
              >
                {t('preview.export.drawer.cancel')}
              </button>
              <button
                type="submit"
                className="inline-flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-indigo-400"
                disabled={isSubmitting || !selectedPreset || !selectedResolution}
              >
                {isSubmitting && (
                  <svg
                    className="h-4 w-4 animate-spin"
                    viewBox="0 0 24 24"
                    fill="none"
                    xmlns="http://www.w3.org/2000/svg"
                    aria-hidden="true"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                    />
                  </svg>
                )}
                <span>{t('preview.export.drawer.queueAction')}</span>
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
