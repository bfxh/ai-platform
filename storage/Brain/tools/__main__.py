#!/usr/bin/env python
"""Brain Knowledge Base CLI Tools"""

import argparse
import json
import sys
from pathlib import Path

# 添加父路径到 sys.path
sys.path.append(str(Path(__file__).parent.parent.parent))

def cmd_query(args):
    """搜索知识库"""
    from storage.Brain.search.hybrid_search import HybridSearchEngine
    
    searcher = HybridSearchEngine()
    results = searcher.search(
        keyword=args.keyword,
        source=args.source,
        limit=args.limit,
        tags=args.tag
    )
    
    print(f"找到 {len(results)} 条结果:")
    print("-" * 60)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. [{result['source']}] {result.get('title', result['id'])}")
        print(f"   相关性: {result['relevance']:.3f}")
        print(f"   分类: {result.get('category', '-')}")
        if result.get('content_preview'):
            print(f"   内容: {result['content_preview'][:150]}...")
        if result.get('tags'):
            print(f"   标签: {', '.join(result['tags'])}")

def cmd_import(args):
    """导入外部数据"""
    from storage.Brain.memory.engine import get_memory_engine
    
    engine = get_memory_engine()
    
    if args.source == "qoder":
        from storage.Brain.importers.qoder_importer import QoderImporter
        importer = QoderImporter(args.path)
        stats = importer.import_all(engine)
        print("Qoder 导入完成:")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    elif args.source == "trae":
        from storage.Brain.importers.trae_importer import TraeImporter
        importer = TraeImporter(args.path)
        stats = importer.import_all(engine)
        print("TRAE 导入完成:")
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知数据源: {args.source}")

def cmd_stats(args):
    """显示统计信息"""
    from storage.Brain.memory.engine import get_memory_engine
    from storage.Brain.indexer.auto_indexer import AutoIndexer
    
    engine = get_memory_engine()
    indexer = AutoIndexer()
    
    engine_stats = engine.stats()
    index_stats = indexer.get_stats()
    
    print("=== Brain 知识库统计 ===")
    print("\n【记忆引擎】")
    print(f"  工作记忆: {engine_stats['working_memory_size']} 条")
    print(f"  会话数量: {engine_stats['session_count']} 个")
    print(f"  知识条目: {engine_stats['knowledge_entries']} 条")
    print(f"  模式数量: {engine_stats['pattern_count']} 个")
    print(f"  总大小: {engine_stats['total_size_mb']} MB")
    print(f"  保存次数: {engine_stats['saves']}")
    print(f"  加载次数: {engine_stats['loads']}")
    print(f"  召回次数: {engine_stats['recalls']}")
    
    print("\n【索引统计】")
    print(f"  话题总数: {index_stats.get('total_topics', 0)}")
    print(f"  知识总数: {index_stats.get('total_knowledge', 0)}")
    print(f"  会话总数: {index_stats.get('total_sessions', 0)}")
    print(f"  模式总数: {index_stats.get('total_patterns', 0)}")
    
    if 'categories' in index_stats:
        print("\n【分类分布】")
        for cat, info in index_stats['categories'].items():
            print(f"  {cat}: {info.get('count', 0)} 条")

def cmd_clean(args):
    """清理旧条目"""
    from storage.Brain.memory.engine import get_memory_engine
    
    engine = get_memory_engine()
    print("清理功能开发中...")
    print("当前统计:")
    stats = engine.stats()
    print(f"  会话数量: {stats['session_count']}")
    print(f"  总大小: {stats['total_size_mb']} MB")

def cmd_reindex(args):
    """重建索引"""
    from storage.Brain.indexer.auto_indexer import AutoIndexer
    
    indexer = AutoIndexer()
    print("正在重建索引...")
    stats = indexer.rebuild_index()
    print("索引重建完成:")
    print(json.dumps(stats, ensure_ascii=False, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Brain 知识库管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # query 命令
    query_parser = subparsers.add_parser('query', help='搜索知识库')
    query_parser.add_argument('keyword', help='搜索关键词')
    query_parser.add_argument('--source', '-s', default='all', 
                              choices=['all', 'topics', 'knowledge', 'sessions', 'patterns'],
                              help='数据源')
    query_parser.add_argument('--limit', '-l', type=int, default=10, help='结果数量')
    query_parser.add_argument('--tag', '-t', action='append', help='标签过滤')

    # import 命令
    import_parser = subparsers.add_parser('import', help='导入外部数据')
    import_parser.add_argument('--source', '-s', required=True, 
                               choices=['qoder', 'trae'], help='数据源类型')
    import_parser.add_argument('--path', '-p', help='数据路径')

    # stats 命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')

    # clean 命令
    clean_parser = subparsers.add_parser('clean', help='清理旧条目')

    # reindex 命令
    reindex_parser = subparsers.add_parser('reindex', help='重建索引')

    args = parser.parse_args()

    if args.command == 'query':
        cmd_query(args)
    elif args.command == 'import':
        cmd_import(args)
    elif args.command == 'stats':
        cmd_stats(args)
    elif args.command == 'clean':
        cmd_clean(args)
    elif args.command == 'reindex':
        cmd_reindex(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
