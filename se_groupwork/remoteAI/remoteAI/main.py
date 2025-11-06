from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any
import json
from articleAISerializer import entry

def parallel_process(items: List[Any], func: Callable[[Any], Any], max_workers: int = 5) -> List[Any]:
    """
    用多线程池并行处理列表元素，返回函数调用结果列表（保持与输入列表相同的顺序）
    
    参数:
        items: 待处理的元素列表
        func: 处理单个元素的函数（输入为列表元素，返回处理结果）
        max_workers: 线程池最大线程数（根据API限制调整）
    
    返回:
        按输入列表顺序排列的结果列表
    """
    # 存储结果（用索引绑定顺序）
    results = [None] * len(items)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交任务并记录索引，确保结果顺序与输入一致
        future_to_index = {
            executor.submit(func, item): idx 
            for idx, item in enumerate(items)
        }

        # 遍历完成的任务，按索引填充结果
        for future in as_completed(future_to_index):
            idx = future_to_index[future]
            try:
                # 获取函数返回结果
                result = future.result()
                results[idx] = result
            except Exception as e:
                # 捕获单个任务的异常，避免影响其他任务
                print(f"处理元素 {items[idx]} 时出错: {str(e)}")
                results[idx] = None
    
    return results

if __name__ == "__main__":
    filenames = ["1.content", "2.content", "3.content", "4.content", "5.content", "6.content"]
    contents = []
    for filename in filenames:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
            contents.append(content)
    results = parallel_process(contents, entry, max_workers=5)
    json_results = {}
    for i in range(len(filenames)):
        json_results[filenames[i]] = results[i]
    print(json.dumps(json_results, ensure_ascii=False, indent=4))
    with open("aggregated_results.json", "w", encoding="utf-8") as f:
        json.dump(json_results, f, ensure_ascii=False, indent=4)
        