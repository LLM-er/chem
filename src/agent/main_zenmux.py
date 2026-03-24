import os
import time
from typing_extensions import runtime
import uuid
import tkinter as tt
from tkinter import messagebox
from pathlib import Path
from dotenv import load_dotenv
from langchain_tavily import TavilySearch
from langchain.messages import AIMessage
from langchain.agents import AgentState, create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.graph.ui import push_ui_message  
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend
from deepagents.middleware import (
    FilesystemMiddleware, 
    SubAgentMiddleware
)

load_dotenv()

reports_dir = Path("./reports") # 报告文件存放在./reports目录下，在生成新报告前删除旧报告，
reports_dir.mkdir(exist_ok=True) # exist_ok=True：当目录已经存在时，不要报错。


# 搜索工具（所有代理共享）
internet_search_tool = TavilySearch(max_results=5,topic="general")
# res = internet_search_tool.invoke("杭州天气")
# print("tool ress:",res) #使用 write_todos 规划，**ls 检查前勿跳步**！


# n1n模型平台
def get_model_chat(model_id: str):
    """
    使用 init_chat_model 通用初始化模型
    provider 设为 "openai"，模型需兼容 OpenAI 格式
    使用时只需传入 model_id 即可
    """
    return init_chat_model(
        model=model_id,
        model_provider="openai",
        base_url= os.getenv("ZENMUX_BASE_URL"),
        api_key= os.getenv("ZENMUX_API_KEY"),
        temperature=0.2
    )

# 模型初始化
model_claudeSonnet = get_model_chat("anthropic/claude-sonnet-4.6") # 200k sonnet 中端模型 用于整合报告

# model_google = get_model_chat("google/gemini-3.1-pro-preview") # 上下文长度 1,000,000, google模型会出tasktask错误
model_claudeOpus = get_model_chat("anthropic/claude-opus-4.6") # 200k opus 旗舰级模型 用于生成报告
model_moonshot = get_model_chat("moonshotai/kimi-k2-thinking") # 月之暗面，善于agent多步骤任务,下下文长度 256,000
model_stepfun = get_model_chat("stepfun/step-3.5-flash") # 200k
model_mistralai = get_model_chat("mistralai/mistral-large-2512") #32k
model_llama = get_model_chat("meta/llama-3.3-70b-instruct") #131k
model_gork = get_model_chat("x-ai/grok-4.2-fast") # 上下文长度 128000
model_qwen = get_model_chat("qwen/qwen3-max") # 上下文长度 32768 个 token
model_minimax = get_model_chat("minimax/minimax-m2.5") # 200k
model_xiaomi = get_model_chat("xiaomi/mimo-v2-flash") # 小米 256k 
model_tencent = get_model_chat("tencent/hunyuan-2.0-thinking") #32k
model_gpt = get_model_chat("openai/gpt-5.4")  # 65536
model_glm = get_model_chat("z-ai/glm-5") # 智谱，200k, 善于编程，对标claude
model_baidu = get_model_chat("baidu/ernie-x1.1-preview") # baidu 8192
model_deepseek = get_model_chat("deepseek/deepseek-chat") # 上下文长度 128k
model_doubao = get_model_chat("volcengine/doubao-seed-2.0-pro") # 8k

# test = model_claude.invoke("谁啊")
# print("test",test)
# exit()

# Deepseek立计费的模型
# deepseek_llm = init_chat_model( 
#     model="deepseek-chat",    # 或 "deepseek-coder"
#     model_provider="openai",  # 指定提供商 如果是openai兼容的模型，可以使用openai 但需指定base_url
#     base_url=os.getenv("DEEPSEEK_BASE_URL"),
#     api_key= os.getenv("DEEPSEEK_API_KEY"),
#     # temperature=0.7,
# )

# 测试
@tool
def get_weather():
    """获取天气"""
    weather =" 天气dd "
    # Emit UI elements associated with the message
    push_ui_message("weather", weather, message=message)
    return {"messages": [message]}

# 删除指定文件
@tool
def delete_cache_file():
    """删除文件"""

    # 遍历删除报表缓存文件
    # for f in reports_dir.glob("*.md"):
    #     # 如果文件存在，删除
    #     if f.exists():
    #         f.unlink()

# 批次 ID
# batch_id = f"id_{int(time.time())}"
batch_id = "null"

@tool
def get_batch_id():
    """获取批次编号"""
    batch_id = f"id_{int(time.time())}"
    return batch_id

# 子代理：相同结构报告
deepseek_subagent = {
    "name": "deepseek-analyst",
    "description": "deepseek产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_deepseek.md`**

    """,
    # "tools": [internet_search],
    "model": model_deepseek,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

gork_subagent = {
    "name": "gork-analyst",
    "description": "gork产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_gork.md`**

    """,
    # "tools": [internet_search],
    "model": model_gork,
    # "middleware": [  # 添加文件系统访问权限
    #   FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

doubao_subagent = {
    "name": "doubao-analyst",
    "description": "doubao产品调研专家",
    "system_prompt": f"""

    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_doubao.md`**

    """,
    # "tools": [internet_search],
    "model": model_doubao,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

qwen_subagent = {
    "name": "qwen-analyst",
    "description": "qwen产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_qwen.md`**

    """,
    # "tools": [internet_search],
    "model": model_qwen,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

stepfun_subagent = {
    "name": "stepfun-analyst",
    "description": "stepfun产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_stepfun.md`**

    """,
    # "tools": [internet_search],
    "model": model_stepfun,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

tencent_subagent = {
    "name": "tencent-analyst",
    "description": "tencent产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_tencent.md`**

    """,
    # "tools": [internet_search],
    "model": model_tencent,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }    

baidu_subagent = {
    "name": "baidu-analyst",
    "description": "baidu产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_baidu.md`**

    """,
    # "tools": [internet_search],
    "model": model_baidu,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

xiaomi_subagent = {
    "name": "xiaomi-analyst",
    "description": "xiaomi产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_xiaomi.md`**

    """,
    # "tools": [internet_search],
    "model": model_xiaomi,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }


llama_subagent = {
    "name": "llama-analyst",
    "description": "llama产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_llama.md`**

    """,
    # "tools": [internet_search],
    "model": model_llama,
    # "middleware": [  # 添加文件系统访问权限
    #   FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

moonshot_subagent = {
    "name": "moonshot-analyst",
    "description": "moonshot产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_moonshot.md`**

    """,
    # "tools": [internet_search],
    "model": model_moonshot,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

glm_subagent = {
    "name": "glm-analyst",
    "description": "glm产品调研专家",
    "system_prompt": f"""

    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_glm.md`**

    _minimax
    """,
    # "tools": [internet_search],
    "model": model_glm,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

gpt_subagent = {
    "name": "gpt-analyst",
    "description": "gpt产品调研专家",
    "system_prompt": f"""
    
    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_gpt.md`**
    """,
    # "tools": [internet_search],
    "model": model_gpt,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

claude_subagent = {
    "name": "claude-analyst",
    "description": "claude产品调研专家",
    "system_prompt": f"""

    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,
    
    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_claudet.md`**
    """,

    "model": model_claudeSonnet,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

minimax_subagent = {
    "name": "minimax-analyst",
    "description": "minimax产品调研专家",
    "system_prompt": f"""

    **你是化工行业的市场调研专家,按报告结构生成专业的产品调研报告,为用户建立化工生产工厂提供依据,报告控制在5000字以内**,

    **严格结构**：
      1. 产品描述
      2. 市场分析
      3. 投资回报
      4. 工艺流程

    **使用 `write_file` 工具将生成的调研报告文件保存到文件 `{batch_id}_minimax.md`**

    """,
    # "tools": [internet_search],
    "model": model_minimax,
    "middleware": [  # 添加文件系统访问权限
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True))]
    }

# 主代理：并行 → 等待 → 去重汇总
main_system_prompt = f"""
你是化工领域的专家，按步骤运行输出总结性工程报告：

**报告结构**：
1. 产品描述
2. 市场分析
3. 投资回报
4. 工艺流程
    -在描述工艺流程之后经提炼总结并使用Mermaid生成相应流程图，工艺流程详细文字描述和流程图需同时存在

**执行流程**：
1. **清除历史文件**：
   调用工具 delete_cache_file 删除历史文件

2. **获取批次编号**：
   调用工具 get_batch_id 获取并显示批次编号{batch_id}

3. **运行所有子代理，让每个子代理都生成一份报告并显示报告内容**
   - task("claude-analyst", "claude调研报告")
   - task("tencent-analyst", "tencent调研报告")
   - task("qwen-analyst", "qwen调研报告")
   - task("doubao-analyst", "doubao调研报告")
   - task("gpt-analyst", "gpt调研报告")
   - task("minimax-analyst", "minimax调研报告")

4. **循环检查最多5分钟**：ls 直到同批次{batch_id}所有子代理报告文件都存在

5. **汇总整理生成最终报告**： 
   - read_file 读取同批次{batch_id}子代理报告
   - 按报告结构将相同批次{batch_id}子代理报告去除重复内容，整理优化成一份完整无冗余的最终报告,最终报告没有字数限制，可以使用搜索工具确保最终报告数据准确且有化工专业特性

6. **最终报告注意事**:
   - 页脚注明来源为：亚太化工
   - 不要加注本报告综合了哪些内容
   - 不要表明运行了多少个子代理，直接写所有子代理就行 
   - 不要注明有多少份报告，直接写所有报告就行
   - 页尾不要加注日期
   - 流程图后面不要加`Mermaid`
   - 生成最终报告保存到文件 {batch_id}_final.md
   - 向用户界面展示最终报告的详细内容
"""
# 使用 write_todos 规划，**ls 检查前勿跳步**！

# main_prompt = main_system_prompt.format(batch_id=batch_id)
# print("main_prompt",main_prompt)
# exit()

# @tool
# def agent_node(state, config):  # config 参数自动注入
#     """打印线程ID"""
#     thread_id = config["configurable"]["thread_id"]  # ✅ 标准方式
#     print("thread id", thread_id)
#     return state

# model_gork支持超长上下文用做主模型
agent = create_agent(
    model=model_claudeOpus,
    tools=[delete_cache_file,get_batch_id,internet_search_tool], 
    middleware=[
      FilesystemMiddleware(backend=FilesystemBackend(root_dir=str(reports_dir),virtual_mode=True)),  # ✅ 文件系统
      SubAgentMiddleware(
        default_model=model_claudeOpus,
        default_tools=[],
        subagents=[claude_subagent,tencent_subagent,qwen_subagent,doubao_subagent,gpt_subagent,minimax_subagent],  # 子代理
        ),
    ],
    system_prompt=main_system_prompt.format(batch_id=batch_id)
)

# 创建代理（FilesystemBackend 直接写磁盘）
# agent = create_deep_agent(
#     model = model_moonshot,  # 主模型
#     tools=[delete_cache_file,internet_search_tool], 
#     subagents=[deepseek_subagent,doubao_subagent,gpt_subagent,claude_subagent,minimax_subagent],  # 子代理
#     system_prompt = main_system_prompt.format(batch_id=batch_id), # 加入动态ID区别不同批次
#     # 可下载目录，virtual_mode=True[路径限制/沙箱]：把所有文件操作都限制在 root_dir 下避免被攻击lan
#     backend = FilesystemBackend(root_dir=str(reports_dir), virtual_mode=True)
# )

# topic = "智能音箱"
# print(f"生成 {topic} 调研报告...")

# result = agent.invoke({
#     "messages": [{"role": "user", "content": f"产品：{topic}，生成200字调研报告"}]
# })
# print(result["messages"][-1].content)

# print(f"✅ 完成！下载 /file/cache/{batch_id}_final.md")
# print(result["messages"][-1].content)

# if __name__ == "__main__":
#     topic = "智能音箱"
#     print(f"生成 {topic} 调研报告...")

#     # 弹出错误窗口
#     def show_error_message(error_message):
#         root = tt.Tk() #创建一个 Tkinter 主窗口对象
#         root.withdraw()  # 隐藏主窗口，因为messagebox 需要一个父窗口上下文，但我们不想要一个空的主窗口出现。
#         messagebox.showerror("错误", error_message)
#         root.destroy() #销毁 Tkinter 主窗口，释放资源。
    
#     try:
#         result = agent.invoke({
#             "messages": [{"role": "user", "content": f"产品：{topic}，生成200字调研报告"}]
#         })
#         print(f"✅ 完成！下载 /file/cache/{batch_id}_final.md")
#         print(result["messages"][-1].content)
#     except Exception as e:
#         # 捕获所有异常，并显示在一个消息框中
#         show_error_message(str(e))
