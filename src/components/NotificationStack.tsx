import { AlertCircle, CheckCircle2, Info, X } from 'lucide-react';
import { useMemo } from 'react';

export type NotificationType = 'success' | 'error' | 'info';

export interface NotificationItem {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  createdAt: number;
}

interface NotificationStackProps {
  notifications: NotificationItem[];
  onDismiss: (id: string) => void;
  direction?: 'ltr' | 'rtl';
  dismissLabel?: string;
}

export function NotificationStack({ notifications, onDismiss, direction = 'ltr', dismissLabel = 'Dismiss notification' }: NotificationStackProps) {
  const positionClasses = direction === 'rtl' ? 'left-4 right-auto' : 'right-4 left-auto';

  const iconForType = useMemo(
    () => ({
      success: <CheckCircle2 className="h-5 w-5 text-emerald-500" aria-hidden="true" />,
      error: <AlertCircle className="h-5 w-5 text-red-500" aria-hidden="true" />,
      info: <Info className="h-5 w-5 text-blue-500" aria-hidden="true" />,
    }),
    []
  );

  return (
    <div
      className={`fixed top-4 ${positionClasses} z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none`}
      role="region"
      aria-live="polite"
    >
      {notifications.map((notification) => {
        const icon = iconForType[notification.type];
        const borderColor =
          notification.type === 'success'
            ? 'border-emerald-200'
            : notification.type === 'error'
            ? 'border-red-200'
            : 'border-blue-200';
        const backgroundColor =
          notification.type === 'success'
            ? 'bg-emerald-50'
            : notification.type === 'error'
            ? 'bg-red-50'
            : 'bg-blue-50';

        return (
          <div
            key={notification.id}
            className={`pointer-events-auto border ${borderColor} ${backgroundColor} rounded-xl shadow-sm`}>
            <div className="p-4 flex items-start gap-3">
              <div className="shrink-0 mt-0.5">{icon}</div>
              <div className="flex-1 space-y-1">
                <p className="text-sm font-semibold text-gray-900">{notification.title}</p>
                {notification.message && (
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {notification.message}
                  </p>
                )}
              </div>
              <button
                type="button"
                className="shrink-0 rounded-full p-1 text-gray-500 hover:text-gray-700 hover:bg-white/70 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                aria-label={dismissLabel}
                onClick={() => onDismiss(notification.id)}
              >
                <X className="h-4 w-4" aria-hidden="true" />
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}
