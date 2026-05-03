import React from 'react';

interface DiffViewerProps {
  diff: {
    added: string[];
    modified: string[];
    deleted: string[];
    unchanged: string[];
  };
}

export default function DiffViewer({ diff }: DiffViewerProps) {
  const sections = [
    { label: 'Added', files: diff.added, color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20', icon: '+' },
    { label: 'Modified', files: diff.modified, color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20', icon: '~' },
    { label: 'Deleted', files: diff.deleted, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20', icon: '-' },
    { label: 'Unchanged', files: diff.unchanged, color: 'text-slate-500 dark:text-slate-400', bg: 'bg-slate-50 dark:bg-slate-800', icon: '=' },
  ];

  return (
    <div className="space-y-3">
      {sections.map(({ label, files, color, bg, icon }) => (
        <div key={label}>
          <div className={`flex items-center gap-2 px-3 py-1.5 rounded-t-lg ${bg} text-sm font-medium ${color}`}>
            <span className="font-mono">{icon}</span>
            <span>{label}</span>
            <span className="ml-auto text-xs opacity-70">{files.length} files</span>
          </div>
          {files.length > 0 ? (
            <div className="border border-t-0 border-slate-200 dark:border-slate-700 rounded-b-lg divide-y divide-slate-100 dark:divide-slate-800">
              {files.slice(0, 20).map((file) => (
                <div key={file} className="px-3 py-1.5 text-sm font-mono text-slate-700 dark:text-slate-300 truncate">
                  {file}
                </div>
              ))}
              {files.length > 20 && (
                <div className="px-3 py-1.5 text-sm text-slate-400">
                  +{files.length - 20} more files
                </div>
              )}
            </div>
          ) : (
            <div className="border border-t-0 border-slate-200 dark:border-slate-700 rounded-b-lg px-3 py-2 text-sm text-slate-400">
              No files
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
