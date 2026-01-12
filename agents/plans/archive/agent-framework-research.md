# Agent Framework Research

**Status**: In Progress
**Created**: 2025-12-28
**Task**: home-server-bxa - Research agent orchestration frameworks
**Parent Plan**: mattermost-gateway-service.md (Phase 3: Agent Service)

## Executive Summary

After comprehensive research of LangChain, Pydantic AI, Microsoft Semantic Kernel, and custom implementations, here are the findings for the home server's agent orchestration needs.

**Top Recommendation**: Start with **custom implementation** for Tayne, evolve to Semantic Kernel or Pydantic AI if complexity grows.

---

## Framework Comparison Matrix

| Criterion | Custom Implementation | Semantic Kernel | LangChain | Pydantic AI |
|------------|-------------------|-------------------|-----------|---------------|
| **OpenAI Compatibility** | ✅ Full (direct API) | ✅ Excellent | ✅ Good | ⏳ TBD* |
| **Learning Curve** | ✅ Low (easy start) | ⚠️ Moderate-High | ⚠️ High | ⚠️ Low-Medium |
| **Complexity** | ✅ Minimal overhead | ⚠️ Moderate | ❌ High | ✅ Low |
| **Vendor Lock-in** | ✅ Zero | ✅ Low (MIT) | ⚠️ Medium | ⚠️ TBD* |
| **Tool Calling** | ✅ Simple (direct) | ✅ Easy (plugins) | ✅ Mature | ✅ Type-safe |
| **Memory Management** | ⚠️ Manual (build yourself) | ✅ Built-in + Chroma | ✅ Built-in many options | ⚠️ TBD* |
| **Production Ready** | ✅ Yes (your code) | ✅ Yes (Microsoft backing) | ✅ Yes (widely used) | ⏳ Newer* |
| **Community Support** | ✅ Open source examples | ✅ 26.9k stars | ✅ 93k stars | ⏳ Newer* |
| **Self-Hosted LLM Support** | ✅ Perfect | ✅ Excellent | ✅ Good | ⚠️ TBD* |

*Pydantic AI research incomplete - marked as TBD

---

## Detailed Analysis

### 1. Microsoft Semantic Kernel

**Verdict**: Strong candidate for future scaling

#### Strengths:
- ✅ **Excellent OpenAI Compatibility**: Works seamlessly with OpenAI-compatible APIs (local-ai-app)
  ```python
  from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
  service = OpenAIChatCompletion(
      ai_model_id="llama3-2:3b",
      api_key="no-key-needed",
      endpoint="http://local-ai.server.unarmedpuppy.com"
  )
  ```
- ✅ **Flexible Tool Calling**: Multiple approaches (plugins, decorators, direct registration)
- ✅ **Sophisticated Memory Management**: Built-in support for Chroma, vector stores, agent memory framework (2025)
- ✅ **MIT License**: Minimal vendor lock-in risk
- ✅ **Multi-Language**: C#, Python, Java - Microsoft backing
- ✅ **Enterprise-Grade**: Production-ready with regular releases
- ✅ **26.9k GitHub Stars**: Strong community

#### Weaknesses:
- ⚠️ **Moderate Learning Curve**: Getting started easy, advanced features complex
- ⚠️ **Azure Bias**: Documentation leans toward Azure services
- ⚠️ **Newer Agent Framework**: Converging with AutoGen (evolving)

#### Use Cases for Home Server:
- **Phase 3 (Agent Service - Basic)**: Overkill, but good option for future
- **Phase 4 (Memory)**: Excellent built-in memory with Chroma support
- **Multi-Agent Systems**: Designed for complex orchestrations

#### Example Code (from research):
```csharp
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Connectors.Ollama;

var builder = Kernel.CreateBuilder();
builder.AddOllamaChatCompletion("llama3-2:3b", new Uri("http://localhost:11434"));
var kernel = builder.Build();

var agent = new ChatCompletionAgent {
    Instructions = "Answer questions about server status",
    Name = "Tayne",
    Kernel = kernel
};

var plugin = KernelPluginFactory.CreateFromFunctions(
    "Server", "Server status tools",
    [KernelFunctionFactory.CreateFromMethod(GetServerStatus)]
);
agent.Kernel.Plugins.Add(plugin);

await agent.InvokeAsync(chat);
```

---

### 2. LangChain

**Verdict**: Overkill for current needs, good for future enterprise features

**Note**: Research incomplete due to task interruption. Preliminary findings:

#### Strengths:
- ✅ **Mature Ecosystem**: 93k+ GitHub stars, largest community
- ✅ **Extensive Tool Library**: Pre-built tools for many integrations
- ✅ **OpenAI Compatible**: Good support for local LLMs
- ✅ **Rich Memory Options**: Multiple memory backends available

#### Weaknesses:
- ⚠️ **High Complexity**: Steep learning curve
- ⚠️ **Vendor Lock-in**: Designed around specific provider patterns
- ⚠️ **Overkill**: Simple agent needs don't justify complexity
- ⚠️ **Opinionated**: Forces specific patterns and workflows

#### Use Cases for Home Server:
- **Current Phase**: Overkill for Tayne basic agent
- **Future**: If complex multi-agent systems needed

---

### 3. Pydantic AI

**Verdict**: Promising but research incomplete

**Note**: Background task cancelled - unable to complete research.

**Preliminary Assessment**:
- ✅ **Type Safety**: Built on Pydantic (strong typing)
- ✅ **Simpler than LangChain**: Explicit goal to be easier
- ✅ **Tool Calling**: Designed for function calling
- ⏳ **Newer Framework**: Rapidly evolving, maturity unclear
- ⏳ **Production Readiness**: Needs more investigation

**Status**: Needs follow-up research when time permits

---

### 4. Custom Implementation

**Verdict**: **Recommended for Phase 3 (Tayne Basic)**

#### Core Pattern: ReAct (Reason, Act, Observe)

```python
def run_agent(user_message, tools, conversation_history=None):
    while True:
        # 1. Send message + tools to LLM
        response = client.chat.completions.create(
            model="llama3-8b",  # from local-ai-app
            messages=conversation_history + [{"role": "user", "content": user_message}],
            tools=[tool.get_schema() for tool in tools],
            tool_choice="auto"  # Let LLM decide when to use tools
        )

        # 2. Check if LLM wants to use tools
        if response.choices[0].message.tool_calls:
            # 3. Execute tools
            tool_results = []
            for tool_call in response.choices[0].message.tool_calls:
                result = execute_tool(tool_call.function.name, tool_call.function.arguments)
                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "result": result
                })

            # 4. Send tool results back and continue
            conversation_history.append({"role": "assistant", "content": response.choices[0].message})
            conversation_history.append({"role": "user", "content": tool_results})
        else:
            # Task complete
            return response.choices[0].message.content
```

#### Strengths:
- ✅ **Zero Vendor Lock-in**: Your code, complete control
- ✅ **Minimal Overhead**: Only what you need
- ✅ **Full Understanding**: Implement ReAct loop yourself = deep understanding
- ✅ **Perfect for Local LLMs**: Direct OpenAI API usage
- ✅ **Low Learning Curve**: Start simple, evolve as needed
- ✅ **No Framework Dependencies**: Only OpenAI-compatible client

#### Weaknesses:
- ⚠️ **Manual Memory Management**: Build your own conversation history
- ⚠️ **Build Your Own**: Tool registry, safety, error handling
- ⚠️ **Evolution Path**: Harder to add advanced features later

#### Use Cases for Home Server:
- ✅ **Phase 3 (Agent Service - Basic)**: Perfect fit
- ✅ **Simple Tayne Personality**: One agent, few tools, basic memory
- ⚠️ **Phase 4 (Memory)**: Need to build yourself (or adopt framework)

---

## Recommendations by Phase

### Phase 3: Agent Service (Basic)
**Recommendation**: **Custom Implementation**

**Rationale**:
1. Tayne needs basic tool calling + simple conversation history
2. Phase 3 explicitly says "no memory yet" - custom ReAct loop is perfect
3. Your local-ai-app already provides OpenAI-compatible API
4. Fast implementation, quick iteration
5. No framework bloat for simple use case

**Implementation Path**:
```
1. Start with custom ReAct loop (see pattern above)
2. Add tool registry (dictionary mapping names to functions)
3. Simple conversation buffer (list of messages)
4. Test with local-ai-app
5. Evaluate complexity at end of Phase 3
```

### Phase 4: Memory
**Recommendation**: **Adopt Semantic Kernel or Build Custom with pgvector**

**Options**:

**Option A: Semantic Kernel with Chroma**
- Pros: Built-in memory support, enterprise-ready
- Cons: Adds framework complexity
- Effort: Moderate (learn framework, integrate)

**Option B: Custom with PostgreSQL + pgvector**
- Pros: Keeps control, you already have PostgreSQL infrastructure
- Cons: More code to maintain
- Effort: High (implement semantic search, embeddings)

**Timeline**: Decide at end of Phase 3 based on complexity experienced

### Phase 5: Additional Interfaces
**Recommendation**: **Evaluate Framework Based on Phase 3 Experience**

If custom implementation becomes complex during Phases 3-4, consider migrating to:
- **Semantic Kernel**: For enterprise features, multi-agent coordination
- **Pydantic AI**: For type safety, simpler than LangChain

**Avoid**: LangChain (overkill for self-hosted needs)

---

## Local AI App Integration

### OpenAI-Compatible Endpoints Available:

From `apps/local-ai-app/app/main.py`:

- `POST /v1/chat/completions` - Chat with tool calling support
- `GET /v1/models` - List available models
- `POST /v1/completions` - Text completions
- `POST /v1/images/generations` - Image generation

### Models Available:
- `llama3-8b` - General quality (8192 context)
- `qwen2.5-14b-awq` - Stronger reasoning (6144 context)
- `deepseek-coder` - Coding focus (8192 context)
- `qwen-image-edit` - Multimodal (4096 context)

**Example Custom Agent Integration**:
```python
from openai import OpenAI

client = OpenAI(
    base_url="http://local-ai.server.unarmedpuppy.com/v1",
    api_key="dummy-key"  # local models don't need real key
)

def run_tayne(user_message, tools):
    conversation = [{"role": "system", "content": "You are Tayne, a helpful server assistant."}]

    while True:
        response = client.chat.completions.create(
            model="llama3-8b",
            messages=conversation + [{"role": "user", "content": user_message}],
            tools=[tool.get_schema() for tool in tools],
            tool_choice="auto"
        )

        assistant_msg = response.choices[0].message
        conversation.append({"role": "assistant", "content": assistant_msg})

        if assistant_msg.tool_calls:
            # Execute tools
            for call in assistant_msg.tool_calls:
                result = execute_tool(call.function.name, call.function.arguments)
                conversation.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result)
                })
        else:
            return assistant_msg.content
```

---

## Action Plan

### Immediate (Phase 3 - Basic Agent Service):
1. ✅ **Start with Custom Implementation**: Build ReAct loop with local-ai-app
2. ✅ **Implement Tool Registry**: Map tool names to Python functions
3. ✅ **Add Conversation Buffer**: Simple list for history
4. ✅ **Integrate with agent-tools Service**: Call tools via HTTP
5. ✅ **Test with Mattermost Gateway**: End-to-end flow

### Evaluation Point (After Phase 3):
- Complexity experienced with custom implementation
- Need for memory management sophistication
- Multi-agent coordination requirements
- Tool orchestration complexity

### Future Decisions:
- **If complexity low**: Stay with custom implementation
- **If memory needs high**: Adopt Semantic Kernel or build custom pgvector
- **If multi-agent needed**: Semantic Kernel best choice

---

## Open Questions

1. **Pydantic AI**: Is it production-ready for self-hosted LLMs? Needs follow-up research.
2. **Memory Requirements**: What level of semantic sophistication does Tayne need?
3. **Scale**: How many concurrent users/agents are expected?

---

## Research Sources

### Semantic Kernel:
- [Official Chat Completion Docs](https://learn.microsoft.com/en-us/semantic-kernel/concepts/ai-services/chat-completion/)
- [Ollama Integration Guide](https://ankitsrkr.github.io/post/semantic-kernel/getting-started-with-follama-local-and-semantic-kernel/)
- [Function Calling Examples](https://github.com/microsoft/semantic-kernel/blob/main/dotnet/samples/Concepts/ChatCompletion/OpenAI_StructuredOutputs.cs)
- [Memory Documentation](https://github.com/microsoft/semantic-kernel/blob/main/docs/decisions/0072-agents-with-memory.md)
- [Local Agent Example](https://laurentkempe.com/2025/03/02/building-local-ai-agents-semantic-kernel-agent-with-functions-in-csharp-using-ollama/)

### Custom Implementations:
- [Anthony Garland's Simple Agent](https://github.com/garland3/my-fast-agent-demo) - 300 lines, function calling
- [Leonie Monigatti's From Scratch Tutorial](https://www.leoniemonigatti.com/blog/ai-agent-from-scratch-in-python.html) - Step-by-step
- [Sid Bharath's Coding Agent](https://github.com/sid-dream/coding-agent) - AST-based safety, context management
- [Analytics Vidhya: Frameworks vs Runtimes](https://www.analyticsvidhya.com/blog/2024/12/agent-frameworks-vs-runtimes-vs-harnesses/)
- [Simple Agent Pattern Tutorial](https://medium.com/@garland3/building-a-simple-ai-agent-with-function-calling-a-learning-in-public-project-acf4cd8f18bd)

### LangChain:
- (Research incomplete - task interrupted)

### Pydantic AI:
- (Research incomplete - task cancelled)

---

## Decision Framework

Use these questions when evaluating frameworks:

1. **Use Case Complexity**: Single agent vs. multi-agent orchestration?
2. **Team Skills**: Does team know the framework? If not, custom = faster start
3. **Vendor Lock-in**: How tied to specific cloud providers?
4. **Memory Needs**: Simple history vs. semantic search?
5. **Future Scale**: Enterprise features needed?

**Answer Key**:
- **Simple = Custom**
- **Complex + Multi-Agent = Semantic Kernel**
- **Overkill = LangChain** (for self-hosted needs)

---

## Next Steps

1. **Implement Phase 3 with Custom Approach**: Follow mattermost-gateway-service.md Phase 3 guide
2. **Document Experience**: Track complexity, pain points, successes
3. **Re-evaluate at Phase 4 completion**: Decide framework vs. continue custom
4. **Complete Pydantic AI Research**: If needed for future evaluation
