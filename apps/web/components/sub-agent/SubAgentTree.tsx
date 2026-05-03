import React from 'react';

interface TreeNode {
  id: string;
  name: string;
  type: string;
  status: string;
  children?: TreeNode[];
}

interface SubAgentTreeProps {
  nodes: TreeNode[];
  onSelect: (nodeId: string) => void;
  selectedId?: string;
}

export default function SubAgentTree({ nodes, onSelect, selectedId }: SubAgentTreeProps) {
  const renderNode = (node: TreeNode, depth: number = 0) => (
    <div key={node.id} className="select-none">
      <button
        onClick={() => onSelect(node.id)}
        className={`w-full flex items-center gap-2 px-3 py-2 text-left rounded-lg transition-colors ${
          selectedId === node.id
            ? 'bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300'
            : 'hover:bg-slate-50 dark:hover:bg-slate-700/50 text-slate-700 dark:text-slate-300'
        }`}
        style={{ paddingLeft: `${12 + depth * 20}px` }}
      >
        <span className={`w-2 h-2 rounded-full ${
          node.status === 'running' ? 'bg-emerald-500' :
          node.status === 'completed' ? 'bg-blue-500' :
          node.status === 'failed' ? 'bg-red-500' : 'bg-slate-400'
        }`} />
        <span className="text-sm font-medium">{node.name}</span>
        <span className="text-xs text-slate-400 ml-auto">{node.type}</span>
      </button>
      {node.children?.map((child) => renderNode(child, depth + 1))}
    </div>
  );

  return (
    <div className="py-2">
      {nodes.map((node) => renderNode(node))}
      {nodes.length === 0 && (
        <div className="px-3 py-4 text-sm text-slate-400 text-center">
          No sub-agents
        </div>
      )}
    </div>
  );
}
