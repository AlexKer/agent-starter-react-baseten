'use client';

import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';

interface LogEntry {
  id: string;
  timestamp: string;
  level: 'INFO' | 'WARNING' | 'ERROR' | 'DEBUG';
  message: string;
}

export const BackendLogs = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs]);

  useEffect(() => {
    const eventSource = new EventSource('/api/logs');
    
    eventSource.onmessage = (event) => {
      try {
        const logData = JSON.parse(event.data);
        const newLog: LogEntry = {
          id: `${Date.now()}-${Math.random()}`,
          timestamp: new Date().toLocaleTimeString(),
          level: logData.level || 'INFO',
          message: logData.message || event.data,
        };
        
        setLogs(prev => [...prev.slice(-99), newLog]); // Keep last 100 logs
        setIsVisible(true);
      } catch (error) {
        console.error('Error parsing log data:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, []);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'ERROR':
        return 'text-red-400';
      case 'WARNING':
        return 'text-yellow-400';
      case 'DEBUG':
        return 'text-blue-400';
      default:
        return 'text-green-400';
    }
  };

  if (!isVisible) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="fixed top-20 left-4 right-4 z-40 md:left-8 md:right-8"
    >
      <div className="mx-auto max-w-4xl">
        <motion.div
          className={cn(
            "bg-black/90 backdrop-blur-sm border border-gray-800 rounded-lg shadow-2xl overflow-hidden",
            isExpanded ? "h-64" : "h-32"
          )}
          animate={{ height: isExpanded ? "16rem" : "8rem" }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-2 bg-gray-900/50 border-b border-gray-800">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm font-mono text-gray-300">Backend Logs</span>
              <span className="text-xs text-gray-500">({logs.length})</span>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-gray-400 hover:text-white transition-colors"
              >
                {isExpanded ? (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
                  </svg>
                ) : (
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                )}
              </button>
              <button
                onClick={() => setLogs([])}
                className="text-gray-400 hover:text-white transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </button>
            </div>
          </div>

          {/* Logs Container */}
          <div className="h-full overflow-y-auto bg-black/50">
            <div className="p-3 space-y-1">
              <AnimatePresence>
                {logs.map((log) => (
                  <motion.div
                    key={log.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ duration: 0.2 }}
                    className="flex items-start space-x-3 text-xs font-mono"
                  >
                    <span className="text-gray-500 flex-shrink-0 w-16">
                      {log.timestamp}
                    </span>
                    <span className={cn("flex-shrink-0 w-12 font-semibold", getLevelColor(log.level))}>
                      {log.level}
                    </span>
                    <span className="text-gray-300 flex-1 leading-relaxed">
                      {log.message}
                    </span>
                  </motion.div>
                ))}
              </AnimatePresence>
              <div ref={logsEndRef} />
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}; 