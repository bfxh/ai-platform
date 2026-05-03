#!/usr/bin/env python3
import os
import sys
import re
import json
from pathlib import Path
from typing import Dict, Optional, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from skills.base import Skill

try:
    import requests
except ImportError:
    requests = None


class JavaGuide(Skill):
    name = "java_guide"
    description = "JavaGuide - Java 学习指南、面试题库和知识体系"
    version = "2.0.0"

    JAVA_KNOWLEDGE = {
        "基础": {
            "topics": ["数据类型", "String", "equals/hashCode", "泛型", "注解", "异常", "反射", "SPI"],
            "key_points": {
                "数据类型": "8种基本类型: byte/short/int/long/float/double/char/boolean，包装类有缓存池(Integer -128~127)",
                "String": "不可变，final类，字符串常量池，StringBuilder线程不安全快，StringBuffer线程安全慢",
                "equals/hashCode": "equals相等则hashCode必须相等，重写equals必须重写hashCode，HashMap依赖此契约",
                "泛型": "类型擦除，运行时不存在泛型信息，PECS原则: 生产者extends消费者super",
                "异常": "检查型(Exception)vs非检查型(RuntimeException)，try-with-resources自动关闭",
                "反射": "Class.forName()加载，getDeclaredMethods获取私有方法，setAccessible突破访问限制",
                "SPI": "ServiceLoader机制，META-INF/services目录，JDBC/Dubbo使用"
            }
        },
        "集合": {
            "topics": ["List", "Set", "Map", "Queue", "ConcurrentHashMap"],
            "key_points": {
                "List": "ArrayList动态数组O(1)随机访问，LinkedList双向链表O(1)插入删除",
                "Set": "HashSet基于HashMap，TreeSet红黑树排序，LinkedHashSet保持插入顺序",
                "Map": "HashMap数组+链表+红黑树(链表>=8)，初始容量16负载因子0.75",
                "ConcurrentHashMap": "JDK7分段锁，JDK8 CAS+synchronized锁桶节点，支持并发读"
            }
        },
        "多线程": {
            "topics": ["线程创建", "锁机制", "线程池", "CAS", "AQS", "Volatile"],
            "key_points": {
                "线程创建": "继承Thread/实现Runnable/Callable/Future/线程池",
                "锁机制": "synchronized(JVM层面)/ReentrantLock(API层面)/读写锁/StampedLock",
                "线程池": "ThreadPoolExecutor 7个参数，4种拒绝策略，Executors工厂方法不推荐",
                "CAS": "Compare-And-Swap无锁乐观并发，ABA问题用AtomicStampedReference解决",
                "AQS": "AbstractQueuedSynchronizer，核心state+CLH队列，ReentrantLock/Semaphore基于它",
                "Volatile": "保证可见性禁止指令重排，不保证原子性，双重检查锁单例必须用"
            }
        },
        "JVM": {
            "topics": ["内存模型", "GC算法", "类加载", "调优"],
            "key_points": {
                "内存模型": "堆(新生代1/3+老年代2/3)、方法区/元空间、虚拟机栈、本地方法栈、程序计数器",
                "GC算法": "标记-清除(碎片)/标记-整理(慢)/复制(空间浪费)/分代收集，G1/ZGC/ Shenandoah",
                "类加载": "双亲委派: Bootstrap->Extension->Application，打破: SPI/热部署/OSGi",
                "调优": "-Xms/-Xmx设相同避免扩容，-XX:+UseG1GC，jstat/jmap/jstack/Arthas诊断"
            }
        },
        "Spring": {
            "topics": ["IoC", "AOP", "事务", "Bean生命周期", "循环依赖"],
            "key_points": {
                "IoC": "控制反转，DI依赖注入，@Autowired/@Resource/@Inject，三级缓存解决循环依赖",
                "AOP": "动态代理: JDK(接口)/CGLIB(类)，@Aspect切面，5种通知类型",
                "事务": "@Transactional，7种传播行为，4种隔离级别，rollbackFor指定回滚异常",
                "Bean生命周期": "实例化->属性赋值->初始化(BeanPostProcessor)->使用->销毁",
                "循环依赖": "三级缓存: singletonObjects/earlySingletonObjects/singletonFactories"
            }
        },
        "数据库": {
            "topics": ["索引", "事务", "锁", "SQL优化", "分库分表"],
            "key_points": {
                "索引": "B+树索引，最左前缀原则，覆盖索引避免回表，索引失效: 函数/隐式转换/OR",
                "事务": "ACID，4种隔离级别: 读未提交/读已提交/可重复读/串行化，MVCC多版本并发控制",
                "锁": "行锁/表锁/间隙锁/临键锁，乐观锁(版本号)/悲观锁(SELECT FOR UPDATE)",
                "SQL优化": "EXPLAIN分析，避免SELECT *，小表驱动大表，用EXISTS替代IN",
                "分库分表": "ShardingSphere，水平分表(取模/范围)，分布式ID(雪花算法)"
            }
        },
        "分布式": {
            "topics": ["CAP", "分布式锁", "消息队列", "服务注册", "网关"],
            "key_points": {
                "CAP": "一致性/可用性/分区容错性三选二，CP(ZooKeeper)/AP(Eureka/Nacos)",
                "分布式锁": "Redis SETNX+过期+Lua释放，Redisson看门狗续期，ZooKeeper临时节点",
                "消息队列": "Kafka(高吞吐)/RocketMQ(事务消息)/RabbitMQ(路由灵活)，防重复消费幂等",
                "服务注册": "Nacos(AP+CP)/Eureka(AP)/ZooKeeper(CP)，心跳检测+服务发现",
                "网关": "Spring Cloud Gateway，路由/过滤/限流/鉴权，基于WebFlux异步非阻塞"
            }
        }
    }

    INTERVIEW_QUESTIONS = {
        "java基础": [
            {"q": "== 和 equals 的区别？", "a": "== 比较引用地址，equals比较内容。String重写了equals方法比较字符序列。基本类型用==比较值。"},
            {"q": "HashMap的底层实现？", "a": "JDK8: 数组+链表+红黑树。默认容量16，负载因子0.75，链表长度>=8且数组>=64转红黑树。put过程: hash->定位桶->链表/树插入->扩容检查。"},
            {"q": "线程池的核心参数？", "a": "corePoolSize核心线程数、maximumPoolSize最大线程数、keepAliveTime空闲存活时间、workQueue任务队列、threadFactory线程工厂、handler拒绝策略。"},
            {"q": "synchronized和ReentrantLock区别？", "a": "synchronized是JVM层面关键字，自动释放锁；ReentrantLock是API层面，需手动unlock。后者支持公平锁、可中断、多条件变量。"},
            {"q": "JVM内存模型？", "a": "堆(对象实例)、方法区/元空间(类信息常量)、虚拟机栈(栈帧局部变量)、本地方法栈(Native)、程序计数器(当前指令)。堆是GC主要区域。"},
        ],
        "spring": [
            {"q": "Spring Bean的生命周期？", "a": "实例化->属性注入->Aware接口回调->BeanPostProcessor前置->InitializingBean->init-method->BeanPostProcessor后置->使用->DisposableBean->destroy-method"},
            {"q": "Spring如何解决循环依赖？", "a": "三级缓存: singletonObjects(完整Bean)、earlySingletonObjects(早期引用)、singletonFactories(对象工厂)。A创建时发现需要B，B创建需要A，从三级缓存取A的工厂创建早期引用。"},
            {"q": "@Transactional失效的场景？", "a": "1.方法非public 2.自调用(同类方法调用不走代理) 3.异常被catch未抛出 4.rollbackFor未包含实际异常 5.数据库引擎不支持事务(MyISAM)"},
        ],
        "数据库": [
            {"q": "MySQL索引失效的场景？", "a": "1.对索引列使用函数/计算 2.隐式类型转换 3.LIKE以%开头 4.OR条件中有非索引列 5.不满足最左前缀 6.NOT IN/NOT EXISTS 7.数据量太小优化器选择全表扫描"},
            {"q": "事务的隔离级别？", "a": "读未提交(脏读)->读已提交(不可重复读)->可重复读(幻读，MySQL默认)->串行化。MySQL通过MVCC+间隙锁在RR级别解决幻读。"},
        ]
    }

    def execute(self, action: str, params: Dict) -> Dict:
        actions = {
            "search_topics": self._search_topics,
            "get_interview_questions": self._get_interview_questions,
            "get_learning_path": self._get_learning_path,
            "list_topics": self._list_topics,
            "get_key_points": self._get_key_points,
        }
        fn = actions.get(action)
        if fn:
            return fn(params)
        return {"success": False, "error": f"未知动作: {action}, 可用: {list(actions.keys())}"}

    def _search_topics(self, params: Dict) -> Dict:
        query = params.get("query", "").lower()
        if not query:
            return {"success": False, "error": "缺少搜索关键词"}

        results = []
        for category, data in self.JAVA_KNOWLEDGE.items():
            for topic in data["topics"]:
                if query in topic.lower() or query in category.lower():
                    key_point = data["key_points"].get(topic, "")
                    results.append({"category": category, "topic": topic, "key_point": key_point})

        for category, questions in self.INTERVIEW_QUESTIONS.items():
            for q in questions:
                if query in q["q"].lower() or query in q["a"].lower():
                    results.append({"category": f"面试题-{category}", "topic": q["q"], "key_point": q["a"]})

        return {"success": True, "query": query, "results": results, "count": len(results)}

    def _get_interview_questions(self, params: Dict) -> Dict:
        topic = params.get("topic", "java基础")
        questions = self.INTERVIEW_QUESTIONS.get(topic, [])
        if not questions:
            all_topics = list(self.INTERVIEW_QUESTIONS.keys())
            for t, qs in self.INTERVIEW_QUESTIONS.items():
                if topic.lower() in t.lower():
                    questions = qs
                    topic = t
                    break
        return {"success": True, "topic": topic, "questions": questions, "available_topics": list(self.INTERVIEW_QUESTIONS.keys())}

    def _get_learning_path(self, params: Dict) -> Dict:
        level = params.get("level", "beginner")
        paths = {
            "beginner": [
                {"stage": "Java基础", "duration": "2-4周", "topics": ["语法", "面向对象", "集合", "异常", "IO"]},
                {"stage": "数据库", "duration": "1-2周", "topics": ["SQL", "MySQL", "索引", "事务"]},
                {"stage": "Web基础", "duration": "2-3周", "topics": ["HTTP", "Servlet", "Cookie/Session"]},
                {"stage": "框架入门", "duration": "3-4周", "topics": ["Spring", "SpringMVC", "MyBatis"]},
            ],
            "intermediate": [
                {"stage": "并发编程", "duration": "2-3周", "topics": ["线程池", "锁", "CAS", "AQS", "并发集合"]},
                {"stage": "JVM深入", "duration": "1-2周", "topics": ["内存模型", "GC", "类加载", "调优"]},
                {"stage": "Spring Boot", "duration": "2-3周", "topics": ["自动配置", "Starter", "Actuator"]},
                {"stage": "中间件", "duration": "2-3周", "topics": ["Redis", "MQ", "ES", "Nginx"]},
            ],
            "advanced": [
                {"stage": "微服务", "duration": "3-4周", "topics": ["Spring Cloud", "服务注册", "网关", "配置中心"]},
                {"stage": "分布式", "duration": "2-3周", "topics": ["分布式锁", "分布式事务", "CAP", "限流熔断"]},
                {"stage": "架构设计", "duration": "持续", "topics": ["DDD", "CQRS", "事件驱动", "高可用设计"]},
                {"stage": "性能优化", "duration": "持续", "topics": ["JVM调优", "SQL优化", "缓存策略", "压测"]},
            ]
        }
        return {"success": True, "level": level, "learning_path": paths.get(level, paths["beginner"]), "available_levels": list(paths.keys())}

    def _list_topics(self, params: Dict = None) -> Dict:
        topics = []
        for category, data in self.JAVA_KNOWLEDGE.items():
            topics.append({"category": category, "topics": data["topics"]})
        return {"success": True, "categories": topics, "interview_topics": list(self.INTERVIEW_QUESTIONS.keys())}

    def _get_key_points(self, params: Dict) -> Dict:
        topic = params.get("topic", "")
        if not topic:
            return {"success": False, "error": "缺少主题名称"}

        for category, data in self.JAVA_KNOWLEDGE.items():
            if topic in data["key_points"]:
                return {"success": True, "category": category, "topic": topic, "key_point": data["key_points"][topic]}
            for t in data["topics"]:
                if topic.lower() in t.lower():
                    return {"success": True, "category": category, "topic": t, "key_point": data["key_points"].get(t, "")}

        return {"success": False, "error": f"未找到主题: {topic}", "available": list(self.JAVA_KNOWLEDGE.keys())}


if __name__ == "__main__":
    skill = JavaGuide()
    print("JavaGuide 技能 v2.0")
