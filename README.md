# OpenBra.in
![Main](https://github.com/svange/openbrain/actions/workflows/main.yaml/badge.svg?event=push)

A tool to store and retrieve sets of langchain LLM agent parameters for use in chat sessions. Allows users to chat with a programatically configurable, stateful LLM agent. An ORM is provided using DynamoDB to aid in the storage and retrieval of agent parameters, sessions, agent parameters, agent memories, and more.

## Command line interface and tools
The following commands are available for use in the shell. 

```bash
ob "message" # sends a single message to the agent and returns the response 
```
```bash
ob-chat # starts a chat session with the agent
```
```bash
ob-tuner # launch a local gradio instance to create and modify AgentConfig objects
```

## OpenBrain Central Infrastructure
This project holds central infrastructure that is used as a base for all operations needed by OpenBra.in. 

To build and deploy run the following in your shell:

```bash
pipenv run build
```

Alternatively, you can run the following to build and deploy:

```bash
sam build 
sam deploy --guided
```
## Object Model - High level summary
Details subject to change. See OpenAPI spec for latest details.

### ChatMessage Object

#### Fields:

- **sessionId**: Used if sessions are not working correctly using headers.
- **clientId**: Used to identify the user client. The client is the user that deploys the chat widget with their API
  key.

- **reset**:
    - If `True`, the session is reset and an Optional AgentConfig is used to start a new session. A default is used if
      no AgentConfig is provided.
    - If `False`, the session is continued and a response to **message** is returned. If `None`, the session is started.
- **message**: The message sent by the user. Only considered during requests to chat (`reset == False`).
- **agentConfig**: The AgentConfig object used to customize the chat session. Only considered during requests to
  chat (`reset == True`).

```json 
{
    "sessionId": "OPTIONAL",
    "clientId": "OPTIONAL",
    "message": "OPTIONAL",
    "agentConfigOverrides": { "AgentConfig": "OPTIONAL" },
    "reset": "OPTIONAL"
}
``` 

## AgentConfig Object

Used to customize a chat session by configuring LLM options such as system message, temperature, and model. Also allows
for the use of saved configurations and a combination of saved and custom configurations.

```json
{
    "profileName": "REQUIRED",
    "clientId": "REQUIRED",
    "systemMessage": "OPTIONAL",
    "iceBreaker": "OPTIONAL",
    "...": "..."
}
```

# Data Model

The API uses a "dirty" sessions table to store agent memories and configurations. The chat session object is composed of
the following.

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
We use a decoupled, event driven architecture. The agent sends events to event bus and then the developer can simply write rules and targets for the incoming events once the targets are ready. The following diagram shows the data flow in two parts. 
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

## Deployment (CI/CD)
All devops procedures are codified in `ci_cd.py` to run cross-platform, and the commands are ultimately available as
simple pipenv scripts.

```
# python ci_cd.py --help  
usage: ci_cd.py [-h] [--dry-run] [--verbose] [--print-central-infra-outputs] [--stage {dev,prod}] [--test-python] [--skip-tests] [--skip-build] [--build-python] [--publish-python] [--deploy-infra]

Utility script for deployment of python packages and supporting infrastructure.

options:
  -h, --help            show this help message and exit
  --dry-run, -d         Prevents any changes from being made.
  --verbose, -v         Logs debug messages.
  --print-central-infra-outputs, -p
                        Prints the central infrastructure outputs as they currently exist.
  --stage {dev,prod}, -s {dev,prod}
                        If 'dev', publish to pypi-test, if 'prod', publish to pypi.
  --test-python, -t     Run pytest tests
  --skip-tests          Skip pytest tests
  --skip-build          Skip poetry build commands
  --build-python, -B    Run poetry build commands in an idempotent manner.
  --publish-python, -P  Publish python using poetry
  --deploy-infra, -I    Deploy the central infrastructure stack
```

## License

This project is dual-licensed.

1. For open-source projects and educational purposes, it is available under the AGPL-3.0 License. See [LICENSE](LICENSE) for details.
  
2. For commercial projects, a separate license is available. See [COMMERCIAL_LICENSE](COMMERCIAL_LICENSE) for details and contact [Your Contact Information] for inquiries.
