import React, { useEffect, useRef, useState } from 'react';
import { AlertTriangle, X } from 'lucide-react';

const LIMIT_DAY = 1400;

/**
 * RateLimitBanner
 * Shows a persistent yellow banner with:
 *  - Usage progress bar when approaching limits
 *  - Live countdown timer (ticking every second) when rate-limited
 *  - Auto-hides when reset_at timestamp passes
 */
export default function RateLimitBanner({ usedToday = 0, rateLimitInfo, onExpired }) {
  const [timeLeft, setTimeLeft] = useState(null);
  const intervalRef = useRef(null);

  const usagePercent = Math.min((usedToday / LIMIT_DAY) * 100, 100);
  const isWarning = usagePercent >= 70 && !rateLimitInfo;
  const isLimited = !!rateLimitInfo;

  // Start / stop countdown timer
  useEffect(() => {
    if (!rateLimitInfo?.reset_at) {
      setTimeLeft(null);
      if (intervalRef.current) clearInterval(intervalRef.current);
      return;
    }

    const tick = () => {
      const remaining = rateLimitInfo.reset_at - Date.now();
      if (remaining <= 0) {
        setTimeLeft(null);
        clearInterval(intervalRef.current);
        if (onExpired) onExpired();
        return;
      }
      const hours = Math.floor(remaining / 3600000);
      const mins  = Math.floor((remaining % 3600000) / 60000);
      const secs  = Math.floor((remaining % 60000) / 1000);

      if (hours > 0) {
        setTimeLeft(`${hours}h ${mins}m`);
      } else if (mins > 0) {
        setTimeLeft(`${mins}m ${String(secs).padStart(2, '0')}s`);
      } else {
        setTimeLeft(`${secs}s`);
      }
    };

    tick(); // run immediately
    intervalRef.current = setInterval(tick, 1000);
    return () => clearInterval(intervalRef.current);
  }, [rateLimitInfo]);

  // Don't render if usage is low and not limited
  if (!isLimited && !isWarning) return null;

  return (
    <div className={`w-full px-4 py-2.5 flex items-center justify-between gap-3 text-sm border-b transition-all
      ${isLimited
        ? 'bg-amber-500/15 border-amber-500/30 text-amber-300'
        : 'bg-amber-500/8 border-amber-500/15 text-amber-400/80'
      }`}
    >
      <div className="flex items-center gap-2.5 min-w-0 flex-1">
        <AlertTriangle size={14} className="shrink-0" />

        <div className="flex flex-col gap-0.5 min-w-0 flex-1">
          {isLimited ? (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold">
                {rateLimitInfo.type === 'minute'
                  ? 'Minute limit reached.'
                  : 'Daily limit reached.'}
              </span>
              {timeLeft && (
                <span className="font-mono text-amber-200 text-xs bg-amber-500/20 px-2 py-0.5 rounded-full">
                  Resets in {timeLeft}
                </span>
              )}
            </div>
          ) : (
            <span>{usedToday} / {LIMIT_DAY} requests used today</span>
          )}

          {/* Progress bar */}
          <div className="w-full h-1 bg-black/20 rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                isLimited ? 'bg-amber-400' : usagePercent >= 90 ? 'bg-amber-500' : 'bg-amber-400/60'
              }`}
              style={{ width: `${usagePercent}%` }}
            />
          </div>
        </div>
      </div>

      {/* Usage fraction (right side) */}
      <span className="text-xs font-mono shrink-0 opacity-70">
        {usedToday}/{LIMIT_DAY}
      </span>
    </div>
  );
}
