# OpenBrain

![Main Build Status](https://github.com/svange/openbrain/actions/workflows/main.yml/badge.svg?event=push)

🚧 **Under active development. Not ready for use.** 🚧

OpenBrain is a chat platform backed by Large Language Model (LLM) agents. It provides APIs and tools to configure, store, and retrieve chat agents, making your chat sessions more versatile and context-aware.

OpenBrain agents are stateful, so they can remember things about you and your conversation. They can also use tools, so you can use the same agent to chat and to perform actions.

Interactions with the agent can be injected into any application easily by constructing a query, choosing an agent configuration, and pre-processing your data through that agent before sending it of for further processing.

## Features

- **Interactive Agent Tuner**: A GUI to modify and test agent configurations.
- **Command-Line Interface**: Use `ob` for quick completions and `ob-chat` for an interactive session.
- **Flexible Configuration**: Customizable agents through DynamoDB backed ORM.
- **Event-Driven Architecture**: Extensible through cloud-based event handling.

## Quick Start
### Installation


```bash
pip install openbrain
```

### Setup .env file
```bash
cp .env.example .env  # Edit this file with your own values
```
### Deploy Supporting Infrastructure
```bash
python ci_cd.py -I
```

## Using OpenBrain

### OpenBrain Gradio Tuner
To facilitate tuning agent parameters and experimenting with prompts, OpenBrain provides a GUI interface using Gradio. To launch the GUI.

![img.png](img.png)

```bash
$ ob-tuner
Running on local URL:  http://0.0.0.0:7861

To create a public link, set `share=True` in `launch()`.
Tip: You can show or hide the button for flagging with the `allow_flagging=` kwarg; for example: gr.Interface(..., allow_flagging=False)
```

### Command Line Completions

```bash
$ ob "What is the air speed velocity of an unladen swallow?" -v

> Entering new AgentExecutor chain...
Ah, the famous question about the air speed velocity of an unladen swallow. Are you referring to an African or European swallow?

> Finished chain.
Ah, the famous question about the air speed velocity of an unladen swallow. Are you referring to an African or European swallow?
```

### Command Line Interactive Session

```bash
$ ob-chat
---------- Begin Chat Session ----------
> OpenBrain: What… is your name?
User: It is Arthur – King of the Britons.
> OpenBrain: What… is your quest?
User: To seek the Holy Grail.
> OpenBrain: What… is the air-speed velocity of an unladen swallow?
User: What do you mean? An African or a European swallow?
> OpenBrain: I don’t know that. Aaaaaaaaagh!
```

## Architecture Overview

### Data Model

```mermaid
classDiagram
    class ChatMessage {
        User provided*
        + str: sessionId
        + str: clientId
        + str: message
        + AgentConfig: agentConfigOverrides
        + str: agentConfig
        + bool: reset
    }

    class AgentConfig {
        + str: profileName
        + str: clientId
        + str: iceBreaker
        + Decimal: temperature
        + ...
        + save()
        + refresh()
        + load()
        + delete()
        + get_all()
    }

    class ChatSession {
        + str: sessionId
        + str: clientId
        + byte: agentMemory
        + AgentConfig: agentConfig
        + Lead: lead
        + save()
        + load()
    }

    class Lead {
        + str: sessionId
        + str: clientId
        + str: fullName
        + str: firstName
        + str: middleName
        + str: lastName
        + List[str]: medications
        + str: email
        + ...
        + save()
        + refresh()
        + delete()
        + load()
        + get_all()
    }

    ChatSession "1" *-- "1" Lead: contains
    ChatSession "1" *-- "1" AgentConfig: contains
%%    ChatMessage "1" *-- "1" AgentConfig: contains
%%    ChatSession "1" *-- "*" ChatMessage: contains
    ChatSession "1" *-- "1" langchain_ChatMemory: from langchain, serialized
```

# Data Flow diagram
OpenBrain uses an event driven architecture. The agent sends events to event bus and then the developer can simply write rules and targets for the incoming events once the targets are ready. The following diagram shows the data flow in two parts.
1. The user interaction with the agent and the agent interaction with an event bus.
2. The event bus and the targets that are triggered by the events.
```mermaid
sequenceDiagram
    title Agent Data Flow
    participant User
    create participant GPT Agent
    participant AgentConfigTable
    participant OpenAI
    participant Tool
    participant EventBus

    User ->> GPT Agent: (AgentConfig, AgentMemory), ChatMessage
        GPT Agent -->> AgentConfigTable: profileName
        AgentConfigTable -->> GPT Agent: AgentConfig
        GPT Agent -->> OpenAI: ChatMessage
        OpenAI -->> GPT Agent: ChatMessage
%%        GPT Agent ->> GPT Agent: Create/Update Object
        GPT Agent -->> Tool: Tool(Object, clientId)
        Tool -->> EventBus: (Object, clientId, session_id, object_id)
        Tool -->> GPT Agent: ChatMessage
    destroy GPT Agent
    GPT Agent ->> User: ChatMessage, (AgentConfig, AgentMemory), Object

  box blue Databases
      participant AgentConfigTable
  end
  box purple Tool
      participant Tool
  end

  box gray EventBus
      participant EventBus
  end

  box red Provider
      participant OpenAI
  end
```

```mermaid
sequenceDiagram
    title Agent Data Flow
    participant SQS
    participant EventBus
    participant Lambda
    participant ObjectTable
    participant AgentConfigTable
    participant ChatHistoryTable
    participant ExternalSite

    EventBus ->> Lambda: (Object, clientId, sessionId, objectId)
    Lambda -->> ObjectTable: (clientId, objectId)
    ObjectTable -->> Lambda: Object

    Lambda -->> AgentConfigTable: (profileName, clientId)
    ChatHistoryTable -->> Lambda: AgentConfig

    Lambda --> ChatHistoryTable: (clientId, sessionId)
    ChatHistoryTable -->> Lambda: (AgentMemory, AgentConfig)

    Lambda ->> ExternalSite: ...
    ExternalSite --x Lambda: ERROR
    Lambda ->> SQS: <DETAILS NEEDED TO RETRY>
    ExternalSite ->> Lambda: ...

    Lambda -> EventBus: <POTENTIAL NEW EVENT>

    box maroon DeadLetterQueue
        participant SQS
    end

    box blue Databases
        participant ObjectTable
        participant AgentConfigTable
        participant ChatHistoryTable
    end

    box gray EventBus
        participant EventBus
    end

    box brown EventTargets
        participant Lambda
    end

    box green Internet
        participant ExternalSite
    end



```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

- **Open Source**: AGPL-3.0, see [LICENSE](LICENSE)
- **Commercial**: See [COMMERCIAL_LICENSE](COMMERCIAL_LICENSE) and contact us for inquiries.
