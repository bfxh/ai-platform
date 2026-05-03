# MCP Core - 异步执行器

功能:
- 异步任务执行
- 线程池管理
- 并发控制

用法:
    from async_executor import AsyncExecutor
    
    executor = AsyncExecutor(max_workers=10)
    result = await executor.execute(func, *args)
